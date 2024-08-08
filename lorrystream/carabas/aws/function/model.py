import dataclasses
import logging
import typing as t
from pathlib import Path
from tempfile import TemporaryDirectory

import attr
import cottonformation as cf
from cottonformation import ResourceGroup
from cottonformation.res import awslambda, iam

from lorrystream.carabas.aws.model import GenericEnvStack

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BundleArchive:
    """
    Manage a Zip archive.
    """

    name: str
    content: bytes
    checksum: t.Optional[str] = None

    def to_file(self, name: str):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            path = tmppath / name
            path.write_bytes(self.content)
            yield path


@attr.s
class LambdaResource:
    """
    Manage a Lambda resource.
    """

    group: ResourceGroup = attr.ib()
    function: awslambda.Function = attr.ib()


@attr.s
class LambdaFactory:
    """
    Create a Lambda.
    """

    name: str = attr.ib()
    handler: str = attr.ib()
    code: str = attr.ib(default=None)
    oci_uri: str = attr.ib(default=None)
    role_id: str = attr.ib(default="IamRoleForLambdaExecution")

    @property
    def function_id(self):
        return self.name

    def __attrs_post_init__(self):
        self.validate()

    def validate(self):
        if self.code is None and self.oci_uri is None:
            raise ValueError("Please configure either `code` or `image`")

    def make(self, stack: GenericEnvStack, environment: t.Dict[str, str] = None) -> LambdaResource:
        environment = environment or {}
        group = ResourceGroup()

        # IAM role for executing the Lambda function.
        iam_role_for_lambda = iam.Role(
            id=self.role_id,
            # you don't need to remember the exact name or syntax for
            # trusted entity / assume role policy, cottonformation has a helper for this
            rp_AssumeRolePolicyDocument=cf.helpers.iam.AssumeRolePolicyBuilder(
                cf.helpers.iam.ServicePrincipal.awslambda()
            ).build(),
            p_RoleName=cf.Sub("${EnvName}-iam-role-for-lambda", {"EnvName": stack.param_env_name.ref()}),
            p_Description="IAM lambda execution role",
            # you don't need to remember the exact ARN for aws managed policy.
            # cottonformation has a helper for this
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.AWSLambdaBasicExecutionRole,
                # https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-create.html
                cf.helpers.iam.AwsManagedPolicy.AWSLambdaKinesisExecutionRole,
            ],
        )
        group.add(iam_role_for_lambda)

        out_lambda_role_arn = cf.Output(
            id=f"{self.role_id}Arn",
            Description="IAM lambda execution role name",
            Value=iam_role_for_lambda.rv_Arn,
        )
        group.add(out_lambda_role_arn)

        # Define Lambda function.
        """
        - rp_ means "Required Property", it will gives you parameter-hint
          for all valid required properties.
        - rv_ means "Return Value", allowing you to instantly reference the
          attribute. Otherwise, you would need to explicitly invoke `GetAtt`,
          to acquire ARNs of previously created resources.
        - p_ means "Property".

        aws lambda create-function \
          --function-name hello-world \
          --package-type Image \
          --code ImageUri=111122223333.dkr.ecr.us-east-1.amazonaws.com/hello-world:latest \
          --role arn:aws:iam::111122223333:role/lambda-ex
        """
        if self.code:
            rp_code = awslambda.PropFunctionCode(
                p_ZipFile=self.code,
            )
        elif self.oci_uri:
            rp_code = awslambda.PropFunctionCode(
                p_ImageUri=self.oci_uri,
            )
        else:
            raise ValueError("Lambda function is invalid without code definition")

        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html
        # Runtime and Handler are mandatory parameters for functions created with deployment packages
        # The Runtime and Handler parameters are not supported for functions created with container images.
        lambda_function = awslambda.Function(
            id=self.function_id,
            p_FunctionName=cf.Sub("${EnvName}-lambda-processor", {"EnvName": stack.param_env_name.ref()}),
            rp_Code=rp_code,
            p_PackageType="Image",
            p_Environment=awslambda.PropFunctionEnvironment(p_Variables=environment),
            rp_Role=iam_role_for_lambda.rv_Arn,
            p_MemorySize=512,
            p_Timeout=3,
            ra_DependsOn=iam_role_for_lambda,
        )

        # TODO: Add Zip archive case.
        # TODO: Add Python 3.10bis
        """
        # p_Runtime=cf.helpers.awslambda.LambdaRuntime.python39,
        # p_Runtime="python3.12",
        # p_Handler="index.handler",
        # p_Handler=self.handler,
        """
        group.add(lambda_function)

        out_lambda_func_arn = cf.Output(
            id=f"{self.function_id}Arn",
            Description="Lambda Function ARN",
            Value=lambda_function.rv_Arn,
        )
        group.add(out_lambda_func_arn)

        return LambdaResource(group=group, function=lambda_function)
