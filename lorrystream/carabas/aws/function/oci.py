import dataclasses
import importlib
import logging
import os
import shlex
import shutil
import subprocess
import typing as t
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent

from boto_session_manager import BotoSesManager

from lorrystream.util.python.bundle import collect_requirements

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class LambdaPythonImage:
    """
    Manage
    https://docs.aws.amazon.com/lambda/latest/dg/images-create.html
    https://docs.aws.amazon.com/lambda/latest/dg/python-image.html
    https://aws.amazon.com/blogs/containers/containerizing-lambda-deployments-using-oci-container-images/
    https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/deploy-lambda-functions-with-container-images.html
    """

    name: str
    entrypoint_handler: str
    oci_image: t.Union[str, None] = None
    oci_version: t.Union[str, None] = None
    python_version: str = "3.12"
    oci_baseimage: str = "public.ecr.aws/lambda/python"
    oci_platform: str = "linux/amd64"
    entrypoint_file: t.Union[Path, None] = None
    packages: t.List[str] = dataclasses.field(default_factory=list)
    requirements_list: t.List[str] = dataclasses.field(default_factory=list)
    requirements_file: t.Union[str, Path, None] = None

    _bsm: BotoSesManager = None

    def __post_init__(self):
        self._bsm = BotoSesManager()
        if self.oci_image is None:
            self.oci_image = f"{self._bsm.aws_account_id}.dkr.ecr.{self._bsm.aws_region}.amazonaws.com/{self.name}"
        if self.oci_version is None:
            self.oci_version = "latest"
        self.temporary_requirements_file = NamedTemporaryFile()

    @property
    def uri(self) -> str:
        """
        The full specification to an OCI image defining the processor element.
        """
        return f"{self.oci_image}:{self.oci_version}"

    @property
    def image_build(self):
        """
        The full qualified name of the image in `build` stage, including tag.
        """
        return f"{self.name}:build"

    def find_repository_root(self, package: str):
        return self.find_package_root(package).parent

    def find_package_root(self, package: str):
        mod = importlib.import_module(package)
        return Path(mod.__path__[0])

    def get_package_folder(self, package):
        return f"src/{package}"

    def get_dockerfile(self) -> str:
        requirements = ""
        entrypoint = ""
        packages = ""

        # Populate dependencies from package name.
        # This is suitable for building an image including the code on your working tree.
        for package in self.packages:
            pkg_folder = self.get_package_folder(package)
            packages += f"ADD {pkg_folder} /{pkg_folder}"
            self.requirements_list.append(f"/{pkg_folder}")

        # Populate dependencies from inline script metadata (PEP 723).
        # This is suitable for picking up dependencies from standalone single-file Python programs.
        if self.entrypoint_file is not None:
            requirements_pep723 = collect_requirements(self.entrypoint_file.read_text())
            self.requirements_list += requirements_pep723

        # Write list of picked up dependencies into `requirements.txt` file.
        if self.requirements_list:
            tmpfile = self.temporary_requirements_file
            Path(tmpfile.name).write_text("\n".join(self.requirements_list))
            tmpfile.flush()
            self.requirements_file = tmpfile.name

        # Render `Dockerfile` snippet to process a `requirements.txt` file.
        if self.requirements_file is not None:
            requirements = dedent(
                """
            # Copy requirements.txt
            COPY requirements.txt ${LAMBDA_TASK_ROOT}

            # Install the specified packages
            RUN pip install -r requirements.txt
            """
            )

        # Render `Dockerfile` snippet to copy a single-file entrypoint file.
        if self.entrypoint_file is not None:
            entrypoint = dedent(
                f"""
            # Copy function code
            COPY {self.entrypoint_file.name} ${{LAMBDA_TASK_ROOT}}
            """
            )

        dockerfile = dedent(
            f"""
        FROM {self.oci_baseimage}:{self.python_version}

        # Install Git, it is needed for installing Python projects from GitHub.
        # TODO: Make optional.
        # RUN dnf install -y git

        {packages}

        {requirements}

        {entrypoint}

        # Uninstall Git again.
        # TODO: Make optional.
        # RUN dnf remove -y git

        # Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
        CMD [ "{self.entrypoint_handler}" ]
        """
        ).strip()

        return dockerfile

    def copy_handler_file(self, target: Path):
        module = self.entrypoint_handler.rsplit(".", 1)[0]
        mod = importlib.import_module(module)
        if mod.__file__ is None:
            logger.error(f"Module has no __file__: {module}")
            return
        path = Path(mod.__file__)

        search = path.name
        search = "dynamodb_cdc_lambda.py"

        def ignorefunc(src, names):
            ignored = names
            if search in names:
                names.remove(search)
            return ignored

        shutil.copytree(self.find_repository_root("lorrystream"), target / "lorrystream", ignore=ignorefunc)

    def build(self):
        """
        docker build --platform linux/amd64 -t docker-image:build .
        """
        dockerfile = self.get_dockerfile()
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Establish Dockerfile.
            (tmppath / "Dockerfile").write_text(dockerfile)

            # Establish Python `requirements.txt` file.
            if self.requirements_file:
                shutil.copy(self.requirements_file, tmppath / "requirements.txt")

            # Establish single entrypoint file.
            if self.entrypoint_file:
                shutil.copy(self.entrypoint_file, tmppath)

            # Copier for nested files from packages.
            # self.copy_handler_file(tmppath)  # noqa: ERA001

            # Copier for whole development packages.
            for package in self.packages:
                pkg_folder = self.get_package_folder(package)

                def ignorefunc(src, names):
                    ignored = ["dist", "tmp"]
                    for name in names:
                        if name.startswith(".") and name != ".git":
                            ignored.append(name)
                    return ignored

                shutil.copytree(self.find_repository_root(package), tmppath / pkg_folder, ignore=ignorefunc)

            command = f"docker build --platform={self.oci_platform} --tag={self.image_build} ."
            subprocess.run(  # noqa: S603
                shlex.split(command),
                cwd=tmppath,
                env=dict(os.environ) | {"DOCKER_BUILDKIT": "1", "BUILDKIT_PROGRESS": "plain"},
                check=True,
            )

    def test(self):
        """
        FIXME: Make it work.

        docker run --platform linux/amd64 -p 9000:8080 docker-image:build
        curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"payload":"hello world!"}'
        """
        """
        command = f"docker run --platform={self.oci_platform} -p 9000:8080 {self.image_build}"
        print("test-command:", command)
        """
        pass

    def push(self):
        """
        Push OCI image of serverless function (AWS Lambda) to container registry (AWS ECR).

        TODO: Use Docker HTTP client wrapper `docker`, instead of shelling out to the `docker` CLI.

        Abstract:
        docker tag docker-image:build <ECRrepositoryUri>:latest
        docker push ....

        Example:
        docker tag docker-image:build 111122223333.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest
        docker push 111122223333.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest
        """

        # Ensure the image registry exists.
        self.ensure_image_registry()

        # Tag the image with the designated remote image name and version.
        command = f"docker tag {self.image_build} {self.oci_image}:{self.oci_version}"
        subprocess.run(shlex.split(command), check=True)  # noqa: S603

        # Push to container registry.
        command = f"docker push {self.oci_image}:{self.oci_version}"
        subprocess.run(shlex.split(command), check=True)  # noqa: S603

    def ensure_image_registry(self):
        """
        Make sure ECR container registry exists. It is needed to store OCI images for your Lambda functions.

        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 111122223333.dkr.ecr.us-east-1.amazonaws.com
        aws ecr create-repository --repository-name hello-world --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE
        """  # noqa: E501
        pass

    def publish(self):
        """
        This.
        """
        self.build()
        self.test()
        self.push()
