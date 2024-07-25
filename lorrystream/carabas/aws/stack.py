import logging
import typing as t

import attr
import botocore
from cottonformation import ResourceGroup
from cottonformation.res import awslambda, dynamodb, kinesis
from cottonformation.res.dynamodb import PropTableKinesisStreamSpecification

from lorrystream.carabas.aws.function.model import LambdaFactory, LambdaResource
from lorrystream.carabas.aws.model import GenericEnvStack

logger = logging.getLogger(__name__)


@attr.s
class DynamoDBKinesisPipe(GenericEnvStack):
    """
    A description for an AWS CloudFormation stack, relaying DynamoDB CDC information into a sink.
    It is written down in Python, uses OO, and a fluent API.

    It provides elements to implement this kind of pipeline:

        DynamoDB CDC -> Kinesis Stream -> Python Lambda via OCI -> CrateDB

    See also the canonical AWS documentation about relevant topics.

    - DynamoDB -> Kinesis: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds_gettingstarted.html
    - Kinesis -> Lambda: https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis.html
    """

    table_name: str = attr.ib()
    stream_name: str = attr.ib()

    environment: t.Dict[str, str] = attr.ib(factory=dict)

    _event_source: t.Optional[t.Union[kinesis.Stream]] = None
    _processor: t.Optional[LambdaResource] = None

    def table(self):
        """
        aws dynamodb create-table \
            --table-name table-testdrive \
            --key-schema \
                AttributeName=device,KeyType=HASH \
                AttributeName=timestamp,KeyType=RANGE \
            --attribute-definitions \
                AttributeName=device,AttributeType=S \
                AttributeName=timestamp,AttributeType=S \
            --provisioned-throughput \
                ReadCapacityUnits=1,WriteCapacityUnits=1 \
            --table-class STANDARD
        :return:
        """

        group = ResourceGroup()

        table = dynamodb.Table(
            id="DynamoDBTable",
            p_TableName=self.table_name,
            rp_KeySchema=[
                {"rp_AttributeName": "device", "rp_KeyType": "HASH"},
                {"rp_AttributeName": "timestamp", "rp_KeyType": "RANGE"},
            ],
            p_AttributeDefinitions=[
                {"rp_AttributeName": "device", "rp_AttributeType": "S"},
                {"rp_AttributeName": "timestamp", "rp_AttributeType": "S"},
            ],
            p_TableClass="STANDARD",
            p_ProvisionedThroughput={"rp_ReadCapacityUnits": 1, "rp_WriteCapacityUnits": 1},
            # p_KinesisStreamSpecification=PropTableKinesisStreamSpecification(rp_StreamArn=),
        )

        """
        aws kinesis create-stream --stream-name dynamodb-cdc --shard-count 4

        # Check that the Kinesis stream is active.
        aws kinesis describe-stream --stream-name dynamodb-cdc

        STREAM_ARN=$(aws kinesis describe-stream --stream-name dynamodb-cdc | jq -r .StreamDescription.StreamARN)
        aws dynamodb enable-kinesis-streaming-destination \
          --table-name table-testdrive \
          --stream-arn "${STREAM_ARN}" \
          --enable-kinesis-streaming-configuration ApproximateCreationDateTimePrecision=MICROSECOND
        """

        # TODO: ShardCount is expected when StreamMode=PROVISIONED
        stream = kinesis.Stream(
            id="KinesisStream",
            p_Name=self.stream_name,
            p_StreamModeDetails={"rp_StreamMode": "ON_DEMAND"},
        )
        group.add(stream)
        self._event_source = stream

        table.p_KinesisStreamSpecification = PropTableKinesisStreamSpecification(rp_StreamArn=stream.rv_Arn)
        group.add(table)

        return self.add(group)

    def processor(self, proc: LambdaFactory):
        """
        Manifest the main processor component of this pipeline.
        """
        self._processor = proc.make(self, environment=self.environment)
        return self.add(self._processor.group)

    def connect(self):
        """
        Connect the event source to the processor.

        https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-create.html
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-startingposition

        aws kinesis register-stream-consumer \
        --consumer-name con1 \
        --stream-arn arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream

        aws lambda create-event-source-mapping \
        --function-name MyFunction \
        --event-source-arn arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream \
        --starting-position LATEST \
        --batch-size 100
        """
        if not self._processor:
            raise RuntimeError("No processor defined")
        if not self._event_source:
            raise RuntimeError("No event source defined")

        # Get a handle to the AWS Lambda for dependency management purposes.
        awsfunc = self._processor.function

        # Create a mapping and add it to the stack.
        mapping = awslambda.EventSourceMapping(
            id="EventSourceToLambdaMapping",
            rp_FunctionName=awsfunc.p_FunctionName,
            p_EventSourceArn=self._event_source.rv_Arn,
            p_BatchSize=2500,
            # LATEST - Read only new records.
            # TRIM_HORIZON - Process all available records.
            # AT_TIMESTAMP - Specify a time from which to start reading records.
            p_StartingPosition="TRIM_HORIZON",
            ra_DependsOn=awsfunc,
        )
        return self.add(mapping)

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
