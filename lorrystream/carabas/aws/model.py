import logging

import attr
import cottonformation as cf
from aws_cloudformation import Parameter
from boto_session_manager import BotoSesManager

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

    def add(self, thing):
        """
        A shortcut function to add a component to the current template of this Stack.
        """
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

        self.template.batch_tagging(dict(ProjectName=self.project, Stage=self.stage))  # noqa: C408

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
            skip_prompt=True,
        )
        return self
