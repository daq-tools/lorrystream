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

    Resources:
    - https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
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

    print("Result of CloudFormation deployment:")
    print(psql_command)

    print("RDS Instance ARN:", stack.get_output_value(stack._bsm, "RDSInstanceArn"))
    print("Stream ARN:", stack.get_output_value(stack._bsm, "StreamArn"))
    print("Replication ARN:", stack.get_output_value(stack._bsm, "ReplicationArn"))


if __name__ == "__main__":
    setup_logging()
    main()
