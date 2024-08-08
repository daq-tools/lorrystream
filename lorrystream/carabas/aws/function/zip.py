import glob
import shutil
import subprocess
import sys
import typing as T
from pathlib import Path
from tempfile import TemporaryDirectory

from aws_lambda_layer.context import BuildContext
from aws_lambda_layer.source import build_source_artifacts
from aws_lambda_layer.vendor.better_pathlib import temp_cwd
from aws_lambda_layer.vendor.hashes import hashes

from lorrystream.carabas.aws.function.model import BundleArchive
from lorrystream.util.python.bundle import collect_requirements


# `build_layer_artifacts` from `aws-lambda-layer` package by Sanhe Hu.
# `build_layer_artifacts` improvements to make it platform-agnostic by Andreas Motl.
# https://github.com/MacHu-GWU/aws_lambda_layer-project/blob/546a711401464/aws_lambda_layer/layer.py#L114-L199
def build_layer_artifacts(
    path_requirements: T.Union[str, Path],
    dir_build: T.Union[str, Path],
    bin_pip: T.Optional[T.Union[str, Path]] = None,
    ignore_package_list: T.Optional[T.List[str]] = None,
    quiet: bool = False,
) -> str:
    """
    Build the AWS Lambda layer artifacts based on the dependencies
    specified in the ``path_requirements``. It utilizes ``bin_pip`` to install
    the dependencies into the ``${dir_build}/python`` folder. Afterwards,
    it compresses the ``${dir_build}/python`` folder into ``${dir_build}/layer.zip``.

    Please note that this function is intended to run in an Amazon Linux-like environment,
    such as CodeBuild, EC2, or Cloud9, as the Amazon managed Lambda function
    also uses Amazon Linux.

    In order to build the layer on Windows or macOS, packages are downloaded from PyPI
    using the `manylinux` platform, to avoid compatibility issues with platform-native
    libraries / wheel packages including binary code.

    :param path_requirements: example: ``/path/to/requirements.txt``.
    :param dir_build: example: ``/path/to/build/lambda``.
    :param bin_pip: example: ``/path/to/.venv/bin/pip``.
    :param ignore_package_list: a list of package names that you want to ignore
        when building the layer.
    :param quiet: whether you want to suppress the output of cli commands.

    :return: the layer content sha256, it is sha256 of the requirements.txt file
    """
    build_context = BuildContext.new(dir_build=dir_build)
    path_requirements = Path(path_requirements).absolute()
    if bin_pip:
        bin_pip = Path(bin_pip).absolute()
    else:
        bin_pip = Path(sys.executable).parent.joinpath("pip").absolute()

    # remove existing artifacts and temp folder
    build_context.path_layer_zip.unlink(missing_ok=True)
    shutil.rmtree(build_context.dir_python, ignore_errors=True)

    # initialize the build/lambda folder
    build_context.dir_build.mkdir(parents=True, exist_ok=True)

    # Platform-agnostic `pip install`.
    # pip install --platform=manylinux2014_x86_64 --only-binary=:all: \
    #   --requirement requirements.txt --target ./build/python/lib/python3.11/site-packages
    # https://github.com/MacHu-GWU/aws_lambda_layer-project/issues/1
    # https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html#python-layer-manylinux
    # https://github.com/awsdocs/aws-lambda-developer-guide/blob/main/sample-apps/layer-python/layer-numpy/1-install.sh
    python_package_path = f"python{sys.version_info.major}.{sys.version_info.minor}"
    pkg_relative_path = Path("lib") / python_package_path / "site-packages"
    target_path = build_context.dir_python / pkg_relative_path
    args = [
        str(bin_pip),
        "install",
        "--platform=manylinux2014_x86_64",
        "--only-binary=:all:",
        f"--requirement={path_requirements}",
        f"--target={target_path}",
    ]
    if quiet:
        args.append("--disable-pip-version-check")
        args.append("--quiet")
    subprocess.run(args, check=True)  # noqa: S603

    # zip the layer file
    # some packages are pre-installed in AWS Lambda runtime, so we don't need to
    # add them to the layer
    if ignore_package_list is None:
        ignore_package_list = [
            "boto3",
            "botocore",
            "s3transfer",
            "urllib3",
            "setuptools",
            "pip",
            "wheel",
            "twine",
            "_pytest",
            "pytest",
        ]
    args = [
        "zip",
        f"{build_context.path_layer_zip}",
        "-r",
        "-9",
    ]
    if quiet:
        args.append("-q")
    # the glob command and zip command depends on the current working directory
    with temp_cwd(build_context.dir_build):
        args.extend(glob.glob("*"))
        if ignore_package_list:
            args.append("-x")
            for package in ignore_package_list:
                ignore_path = Path(build_context.dir_python.name) / pkg_relative_path
                args.append(f"{ignore_path}/{package}*")
        subprocess.run(args, check=True)  # noqa: S603
    layer_sha256 = hashes.of_bytes(path_requirements.read_bytes())
    return layer_sha256


def build_layer(*artifacts: Path, more_requirements: T.Union[T.List[str], None] = None):
    """
    Build an AWS Lambda layer for Python Lamda functions.

    https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html#python-layer-manylinux
    """

    # Build list of requirements specifications.
    more_requirements = more_requirements or []
    requirements = collect_requirements(*artifacts) + more_requirements

    with TemporaryDirectory() as tmpdir:
        # Define build directory.
        tmppath = Path(tmpdir)
        dir_build = tmppath / "build"

        # Write list of requirements to file.
        requirements_file = tmppath.joinpath("requirements.txt")
        requirements_file.write_text("\n".join(requirements))

        # Build AWS Lamda layer Zip archive.
        layer_sha256 = build_layer_artifacts(
            path_requirements=requirements_file,
            dir_build=dir_build,
        )
        archive_file = dir_build / "layer.zip"
        return BundleArchive(name=archive_file.name, content=archive_file.read_bytes(), checksum=layer_sha256)


def build_source(entrypoint_script: Path, *artifacts: Path):
    package_name = "common"
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Populate source package directory.
        dir_build = tmppath / "build"
        dir_lib = tmppath / "lib"
        pkg_dir = dir_lib / package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        for artifact in artifacts:
            shutil.copy(artifact, pkg_dir)

        # Build Zip archive.
        dummy_projectfile = dir_lib / "pyproject.toml"
        source_sha256, path_source_zip = build_source_artifacts(
            path_setup_py_or_pyproject_toml=dummy_projectfile,
            package_name=package_name,
            path_lambda_function=entrypoint_script,
            dir_build=dir_build,
            use_pathlib=True,
        )
        return BundleArchive(name=path_source_zip.name, content=path_source_zip.read_bytes(), checksum=source_sha256)


"""
def upload_source_old(bundle: BundleArchive):
    # bsm = BotoSesManager(profile_name="bmt_app_dev_us_east_1")
    bsm = BotoSesManager()
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "source.zip").write_bytes(bundle.content)
        s3dir_lambda = S3Path(
            f"s3://{bsm.aws_account_id}-{bsm.aws_region}-artifacts/projects/{package_name}/lambda/"
        ).to_dir()
        s3path_source_zip = upload_source_artifacts(
            bsm=bsm,
            version="0.0.1",
            source_sha256=bundle.checksum,
            dir_build=tmppath,
            s3dir_lambda=s3dir_lambda,
            metadata=metadata,
            tags=tags,
        )
        print("s3path_source_zip:", s3path_source_zip)
"""
