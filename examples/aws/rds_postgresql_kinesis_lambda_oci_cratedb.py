import logging

from lorrystream.carabas.aws import RDSPostgreSQLDMSKinesisPipe
from lorrystream.util.common import setup_logging

logger = logging.getLogger(__name__)


def main():
    """
    A recipe to deploy a data migration stack to Amazon AWS.

    Pipeline:
    - RDS PostgreSQL -> DMS -> Kinesis Stream -> Python Lambda via OCI -> CrateDB

    Ingredients:
    - DMS, RDS PostgreSQL, Kinesis
    - Lambda function, shipped per OCI image
    - CrateDB Cloud

    Prerequisites: Register an OCI repository.
    """

    # Build and publish OCI image that includes the AWS Lambda function.
    """
    python_image = LambdaPythonImage(
        name="cratedb-kinesis-lambda",
        entrypoint_file=Path("./lorrystream/process/kinesis_cratedb_lambda.py"),
        entrypoint_handler="kinesis_cratedb_lambda.handler",
    )
    python_image.publish()
    """

    # Define an AWS CloudFormation software stack.
    stack = RDSPostgreSQLDMSKinesisPipe(
        project="testdrive-dms-postgresql",
        stage="dev",
        region="eu-central-1",
        description="RDS PostgreSQL > DMS -> Kinesis Stream -> Python Lambda via OCI -> CrateDB",
        db_username="dynapipe",
        db_password="secret11",  # noqa: S106
        environment={
            "SINK_SQLALCHEMY_URL": "crate://admin:dZ..qB@example.eks1.eu-west-1.aws.cratedb.net:4200/?ssl=true",
            "SINK_TABLE": "transactions",
        },
    )

    # Add components to the stack.
    """
    stack.table().processor(
        LambdaFactory(
            name="DynamoDBCrateDBProcessor",
            oci_uri=python_image.uri,
            handler=python_image.entrypoint_handler,
        )
    ).connect()
    """
    stack.vpc().database().stream().dms()  # .table()

    # Deploy stack.
    stack.deploy()
    logger.info(f"Deployed stack: {stack}")

    # Refresh the OCI image.
    # TODO: Detect when changed.
    stack.deploy_processor_image()

    PublicDbEndpoint = stack.get_output_value(stack._bsm, "PublicDbEndpoint")
    PublicDbPort = stack.get_output_value(stack._bsm, "PublicDbPort")
    psql_command = (
        f'psql "postgresql://{stack.db_username}:{stack.db_password}@{PublicDbEndpoint}:{PublicDbPort}/postgres"'
    )
    print(psql_command)

    print("Stream ARN:", stack.get_output_value(stack._bsm, "StreamArn"))

    """
    aws dms describe-replications
    aws dms start-replication \
        --start-replication-type=start-replication \
        --replication-config-arn arn:aws:dms:eu-central-1:931394475905:replication-config:LB2JAGY7XFB7PA7HEX3MI36CUA

    aws logs describe-log-groups
    aws logs start-live-tail --log-group-identifiers \
        arn:aws:logs:eu-central-1:931394475905:log-group:/aws/rds/instance/testdrive-dms-postgresql-dev-db/postgresql \
        arn:aws:logs:eu-central-1:931394475905:log-group:dms-serverless-replication-LB2JAGY7XFB7PA7HEX3MI36CUA

    aws cloudformation continue-update-rollback --stack-name testdrive-dms-postgresql-dev
    aws cloudformation delete-stack --stack-name testdrive-dms-postgresql-dev
    """
    """
    - https://docs.aws.amazon.com/dms/latest/APIReference/API_StartReplication.html#DMS-StartReplication-request-StartReplicationType
    - https://docs.aws.amazon.com/cli/latest/reference/dms/start-replication-task.html

    Possible values:

    - start-replication
    - resume-processing
    - reload-target
    """


if __name__ == "__main__":
    setup_logging()
    main()
