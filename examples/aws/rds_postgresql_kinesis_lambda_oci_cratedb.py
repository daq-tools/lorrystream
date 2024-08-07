import logging
import os
from pathlib import Path

from commons_codec.model import ColumnType, ColumnTypeMapStore, TableAddress

from lorrystream.carabas.aws import LambdaFactory, LambdaPythonImage, RDSPostgreSQLDMSKinesisPipe
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
    python_image = LambdaPythonImage(
        name="kinesis-cratedb-lambda",
        entrypoint_file=Path("./lorrystream/process/kinesis_cratedb_lambda.py"),
        entrypoint_handler="kinesis_cratedb_lambda.handler",
    )
    python_image.publish()

    # Define an AWS CloudFormation software stack.
    stack = RDSPostgreSQLDMSKinesisPipe(
        project="testdrive-dms-postgresql",
        stage="dev",
        region="eu-central-1",
        description="RDS PostgreSQL > DMS -> Kinesis Stream -> Python Lambda via OCI -> CrateDB",
        db_username="dynapipe",
        db_password="secret11",  # noqa: S106
    )

    # Exclusively deploy the VPC elements of the stack.
    # Do that on the first invocation, but nothing else.
    # Warning: When doing it subsequently, it will currently delete the whole RDS substack.
    # Warning: When doing it and directly proceed to RDS creation, it will fail:
    #          The specified VPC has no internet gateway attached. Update the VPC and then try again.
    # TODO: Introduce a little CLI controller for invoking different deployment steps conveniently.
    # TODO: Refactor by splitting into different stacks.
    # stack.vpc().deploy(); return  # noqa: ERA001

    # Deploy the full RDS+DMS demo stack.
    stack.vpc().database().stream().dms()  # .deploy(); return

    # Define mapping rules for replication.
    # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html
    # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TableMapping.html
    # TODO: Currently hard-coded to table `public.foo`.
    map_to_kinesis = {
        "rules": [
            {
                "rule-type": "selection",
                "rule-id": "1",
                "rule-name": "DefaultInclude",
                "rule-action": "include",
                "object-locator": {"schema-name": "public", "table-name": "foo"},
                "filters": [],
            },
            # Using the percent wildcard ("%") in "table-settings" rules is
            # not supported for source databases as shown following.
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TableMapping.SelectionTransformation.Tablesettings.html#CHAP_Tasks.CustomizingTasks.TableMapping.SelectionTransformation.Tablesettings.Wildcards
            # Here: Exact schema and table required when using object mapping rule with '3.5' engine.
            {
                "rule-type": "object-mapping",
                "rule-id": "2",
                "rule-name": "DefaultMapToKinesis",
                "rule-action": "map-record-to-record",
                "object-locator": {"schema-name": "public", "table-name": "foo"},
                "filters": [],
            },
        ]
    }

    # Define column type mapping for CrateDB processor.
    column_types = ColumnTypeMapStore().add(
        table=TableAddress(schema="public", table="foo"),
        column="attributes",
        type_=ColumnType.MAP,
    )

    # Add a DMS replication pipeline element to the stack.
    stack.replication(dms_table_mapping=map_to_kinesis)

    # Add custom processing components to the stack.
    stack.processor(
        factory=LambdaFactory(
            name="DMSCrateDBProcessor",
            oci_uri=python_image.uri,
            handler=python_image.entrypoint_handler,
        ),
        environment={
            "MESSAGE_FORMAT": "dms",
            "COLUMN_TYPES": column_types.to_json(),
            "SINK_SQLALCHEMY_URL": os.environ.get("SINK_SQLALCHEMY_URL", "crate://"),
        },
    ).connect(
        batch_size=2_500,
        # - LATEST - Read only new records.
        # - TRIM_HORIZON - Process all available records.
        # - AT_TIMESTAMP - Specify a time from which to start reading records.
        starting_position="TRIM_HORIZON",
        # starting_position_timestamp=1722986869.0,  # noqa: ERA001
    )

    # Deploy stack.
    stack.deploy()
    logger.info(f"Deployed stack: {stack}")

    # Refresh the OCI image.
    # TODO: Detect when changed.
    stack.deploy_processor_image()

    database_host = stack.get_output_value(stack._bsm, "DatabaseHost")
    database_port = stack.get_output_value(stack._bsm, "DatabasePort")
    psql_command = (
        f'psql "postgresql://{stack.db_username}:{stack.db_password}@{database_host}:{database_port}/postgres"'
    )

    print("Result of CloudFormation deployment:")
    print("psql command:", psql_command)

    print("RDS Instance ARN:", stack.get_output_value(stack._bsm, "RDSInstanceArn"))
    print("Stream ARN:", stack.get_output_value(stack._bsm, "StreamArn"))
    print("Replication ARN:", stack.get_output_value(stack._bsm, "ReplicationTaskArn"))


if __name__ == "__main__":
    setup_logging()
    main()
