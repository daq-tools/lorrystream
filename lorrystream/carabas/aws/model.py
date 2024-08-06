import logging
import typing as t

import attr
import botocore
import cottonformation as cf
from aws_cloudformation import Parameter
from boto_session_manager import BotoSesManager
from cottonformation.res import kinesis

if t.TYPE_CHECKING:
    from lorrystream.carabas.aws.function.model import LambdaResource

logger = logging.getLogger(__name__)


@attr.s
class GenericEnvStack(cf.Stack):
    project: str = attr.ib()
    stage: str = attr.ib()
    region: str = attr.ib()
    description: str = attr.ib()

    _bsm: BotoSesManager

    param_env_name = cf.Parameter(
        "EnvName",
        Type=cf.Parameter.TypeEnum.String,
    )

    def post_hook(self):
        self._bsm = BotoSesManager(region_name=self.region)
        self.template.Description = self.description
        self.define_parameters()

    def add(self, *things):
        """
        A shortcut function to add a component to the current template of this Stack.
        """
        for thing in things:
            self.template.add(thing)
        return self

    @property
    def env_name(self):
        """
        The environment name is a composite.

        Made from an arbitrary project name, and a name of the stage the Stack is running in.
        """
        return f"{self.project}-{self.stage}"

    @property
    def stack_name(self):
        """
        Stack name equals environment name.
        """
        return self.env_name

    def define_parameters(self):
        """
        Define Stack parameters.
        """
        # Define parameter: Environment name.
        self.template.add(self.param_env_name)

    @property
    def parameters(self):
        """
        Return Stack parameters suitable for deployment.
        """
        return [
            Parameter(key="EnvName", value=self.stack_name),
        ]

    def deploy(self, respawn: bool = False):
        """
        Deploy AWS CloudFormation Stack.
        """
        logger.info("Deploying CloudFormation stack")
        parameters = self.parameters or []

        self.template.batch_tagging(dict(ProjectName=self.project, Stage=self.stage), mode_overwrite=True)  # noqa: C408

        env = cf.Env(bsm=self._bsm)
        if respawn:
            env.delete(stack_name=self.stack_name, skip_prompt=True)

        env.deploy(
            template=self.template,
            stack_name=self.stack_name,
            parameters=parameters,
            include_iam=True,
            include_named_iam=True,
            verbose=True,
            skip_prompt=False,
            # 300 seconds are not enough to wait for RDS PostgreSQL, for example.
            # 500 seconds are not enough for a complete stack including a DMS instance, for example.
            # on 110 th attempt, elapsed 555 seconds, remain 445 seconds ...
            timeout=750,
        )
        return self


@attr.s
class GenericProcessorStack(GenericEnvStack):

    _processor: t.Optional["LambdaResource"] = None

    def deploy_processor_image(self):
        """
        Make an already running Lambda pick up a newly published OCI image.

        This is an imperative function executed orthogonally to the CloudFormation deployment.

        It follows this procedure:
        - Acquire the `<FunctionName>Arn` Output of the Stack's core processor Lambda.
        - Use it to look up a handle to the actual Lambda information.
        - From the information unit, extract the OCI image URI.
        - Instruct the machinery to update the Lambda function code,
          effectively respawning the container running it.
        """
        if not self._processor:
            logger.warning("No processor defined, skip deploying processor OCI image")
            return None
        function_id = self._processor.function.id

        # Inquire Stack Output.
        logger.info(f"Discovering Lambda function existence: {function_id}")
        output_id = f"{function_id}Arn"
        try:
            function_arn = self.get_output_value(self._bsm, output_id)
        except botocore.exceptions.ClientError as ex:
            if "does not exist" not in str(ex):
                raise
            logger.info(f"Stack not found or incomplete: {self.stack_name}")
            return None
        except KeyError:
            logger.info(f"Stack not found or incomplete. Output not found: {output_id}")
            return None

        # Inquire AWS API and eventually update Lambda code.
        client = self._bsm.get_client("lambda")
        try:
            if func := client.get_function(FunctionName=function_arn):
                logger.info(f"Found Lambda function: {function_arn}")
                oci_uri = func["Code"]["ImageUri"]
                logger.info(f"Deploying new OCI image to Lambda function: {oci_uri}")
                response = client.update_function_code(FunctionName=function_arn, ImageUri=oci_uri)
                last_status_message = response["LastUpdateStatusReason"]
                logger.info(f"Lambda update status response: {last_status_message}")
        except Exception as ex:
            if ex.__class__.__name__ != "ResourceNotFoundException":
                raise
            logger.info(f"Lambda function to update OCI image not found: {function_arn}")

        return self


@attr.s
class KinesisProcessorStack(GenericProcessorStack):

    _stream_source: t.Union[kinesis.Stream, None] = None
