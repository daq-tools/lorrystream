import logging
import typing as t

import attr
from cottonformation import ResourceGroup
from cottonformation.res import awslambda, dynamodb, kinesis
from cottonformation.res.dynamodb import PropTableKinesisStreamSpecification

from lorrystream.carabas.aws.function.model import LambdaFactory
from lorrystream.carabas.aws.model import KinesisProcessorStack

logger = logging.getLogger(__name__)


@attr.s
class DynamoDBKinesisPipe(KinesisProcessorStack):
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
