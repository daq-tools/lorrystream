# DynamoDB CDC to CrateDB using Kinesis


## Introduction
> DynamoDB Streams captures a time-ordered sequence of item-level modification
> in any DynamoDB table and stores this information in a log for up to 24 hours.
>
> Applications can access this log and view the data items as they appeared
> before and after they were modified, in near-real time.
>
> -- [Change data capture for DynamoDB Streams]


## About
A [change data capture (CDC)] pipeline made of a DynamoDB
egress CDC processor, sinking data into the CrateDB
OLAP database, using Kinesis.

> Kinesis Data Streams captures item-level modifications in any DynamoDB
> table and replicates them to a Kinesis data stream.
>
> -- [Using Kinesis Data Streams to capture changes to DynamoDB]


## What's Inside

- Completely on AWS' premises, there is a process which relays CDC data
  from a [DynamoDB] table to a [Kinesis] stream, configured using AWS'
  APIs.

- On a compute-environment of your choice, supporting Python, a traditional
  KCL v2 application subscribes to the [Kinesis] stream, in order to receive
  published CDC opslog messages.

- On the egress side, the application re-materializes the items of the
  operations log into any database with [SQLAlchemy] support.


## Setup
Create a database table in DynamoDB, and enable a Kinesis Stream on its
operations log.

This section reflects configuration settings stored in
[dynamodb_cdc_processor.properties](../../../lorrystream/spike/kcl_dynamodb/dynamodb_cdc_processor.properties).

We recommend to run through the setup procedure of [](kinesis.md)
beforehand, because it conveys relevant setup instructions about IAM
policies, which are obligatory to permit Kinesis access to DynamoDB for
storing a "lease table".

### DynamoDB Table
```shell
# Optionally, drop the table.
aws dynamodb delete-table \
    --table-name table-testdrive

# Create table (DDL).
# - It defines a composite primary key. 
#   - "device" is the partition key
#   - "timestamp" is the sort key
# - It does not define auxiliary field names,
#   they can be added dynamically.
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

# Display all table names on DynamoDB.
aws dynamodb list-tables

# Check table status.
aws dynamodb describe-table --table-name table-testdrive | grep TableStatus
```

### CrateDB Table
The destination table name in CrateDB is currently hard-coded. Please use
this command to create the `transactions` table, where the CDC record
processor will re-materialize CDC events into.
```shell
crash -c "CREATE TABLE transactions (data OBJECT(DYNAMIC));"
```

### Kinesis Stream
Capture DynamoDB table operations and relay them to a Kinesis stream.
```shell
# Create a Kinesis Data Stream.
aws kinesis create-stream --stream-name dynamodb-cdc --shard-count 4

# Check that the Kinesis stream is active.
aws kinesis describe-stream --stream-name dynamodb-cdc

# Enable Kinesis streaming on the DynamoDB table.
# Replace the `stream-arn` value with the one returned by
# `describe-stream` in the previous step.
STREAM_ARN=$(aws kinesis describe-stream --stream-name dynamodb-cdc | jq -r .StreamDescription.StreamARN)
aws dynamodb enable-kinesis-streaming-destination \
  --table-name table-testdrive \
  --stream-arn "${STREAM_ARN}" \
  --enable-kinesis-streaming-configuration ApproximateCreationDateTimePrecision=MICROSECOND

# Check if Kinesis streaming is active on the table.
aws dynamodb describe-kinesis-streaming-destination --table-name table-testdrive
```

Note that you need to re-run the linking procedure after dropping and
re-creating the DynamoDB table.

```shell
aws kinesis list-streams
aws kinesis delete-stream --stream-name dynamodb-cdc --enforce-consumer-deletion
```

### KCL Stream Processor

Acquire sources and initialize sandbox.
```shell
git clone https://github.com/daq-tools/lorrystream --branch=kinesis
cd lorrystream
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies, mainly the [amazon-kclpy] package.
```shell
cd lorrystream/dynamodb_cloud
pip install wheel
pip install --verbose -r requirements.txt
```


## Usage
You will need multiple terminal windows. Within both of them, activate the
virtualenv on the top-level directory. Then, navigate to the playground
directory, and seed AWS credentials.
```shell
source .venv/bin/activate
cd lorrystream/dynamodb_cloud
export AWS_ACCESS_KEY=...
export AWS_SECRET_ACCESS_KEY=...
```

Launch the stream processor, subscribing to the DynamoDB CDC operations feed
over a Kinesis stream.
```shell
sh launch.sh dynamodb_cdc_processor.properties
```

Watch actions of the CDC processor.
```shell
tail -F dynamodb_cdc_processor.log
```

Insert record into database table.
```shell
READING_SQL="{'timestamp': '2024-07-12T01:17:42', 'device': 'foo', 'temperature': 42.42, 'humidity': 84.84}"
aws dynamodb execute-statement --statement \
  "INSERT INTO \"table-testdrive\" VALUE ${READING_SQL};"
```

Query database table.
```shell
aws dynamodb execute-statement --statement \
  "SELECT * FROM \"table-testdrive\";"
```

Run UPDATE and DELETE statements, in order to sample the two other DML operations.
```shell
aws dynamodb execute-statement --statement \
  "UPDATE \"table-testdrive\" SET temperature=55.55 WHERE \"device\"='foo' AND \"timestamp\"='2024-07-12T01:17:42';"
```
```shell
aws dynamodb execute-statement --statement \
  "DELETE FROM \"table-testdrive\" WHERE \"device\"='foo' AND \"timestamp\"='2024-07-12T01:17:42';"
```

Alternative for displaying table contents.
```shell
aws dynamodb scan --table-name table-testdrive
```

## Software Tests
```shell
pytest
```

## Appendix

### DynamoDB data types

The following is a complete list of DynamoDB data type descriptors:

    S – String
    N – Number
    B – Binary
    BOOL – Boolean
    NULL – Null
    M – Map
    L – List
    SS – String Set
    NS – Number Set
    BS – Binary Set

### Opslog processor samples
```
01:25:17.632 [dynamodb_cdc_processor] INFO  process_record - {"awsRegion":"us-east-1","eventID":"b015b5f0-c095-4b50-8ad0-4279aa3d88c6","eventName":"INSERT","userIdentity":null,"recordFormat":"application/json","tableName":"table-testdrive","dynamodb":{"ApproximateCreationDateTime":1720740233012995,"Keys":{"device":{"S":"qux"},"timestamp":{"S":"2024-07-12T01:17:42"}},"NewImage":{"humidity":{"N":"84.84"},"temperature":{"N":"42.42"},"device":{"S":"qux"},"timestamp":{"S":"2024-07-12T01:17:42"}},"SizeBytes":99,"ApproximateCreationDateTimePrecision":"MICROSECOND"},"eventSource":"aws:dynamodb"}
01:58:22.371 [dynamodb_cdc_processor] INFO  process_record - {"awsRegion":"us-east-1","eventID":"24757579-ebfd-480a-956d-a1287d2ef707","eventName":"MODIFY","userIdentity":null,"recordFormat":"application/json","tableName":"table-testdrive","dynamodb":{"ApproximateCreationDateTime":1720742302233719,"Keys":{"device":{"S":"foo"},"timestamp":{"S":"2024-07-12T01:17:42"}},"NewImage":{"humidity":{"N":"84.84"},"temperature":{"N":"55.66"},"device":{"S":"foo"},"timestamp":{"S":"2024-07-12T01:17:42"}},"OldImage":{"humidity":{"N":"84.84"},"temperature":{"N":"42.42"},"device":{"S":"foo"},"timestamp":{"S":"2024-07-12T01:17:42"}},"SizeBytes":161,"ApproximateCreationDateTimePrecision":"MICROSECOND"},"eventSource":"aws:dynamodb"}
01:58:42.510 [dynamodb_cdc_processor] INFO  process_record - {"awsRegion":"us-east-1","eventID":"ff4e68ab-0820-4a0c-80b2-38753e8e00e5","eventName":"REMOVE","userIdentity":null,"recordFormat":"application/json","tableName":"table-testdrive","dynamodb":{"ApproximateCreationDateTime":1720742321848352,"Keys":{"device":{"S":"foo"},"timestamp":{"S":"2024-07-12T01:17:42"}},"OldImage":{"humidity":{"N":"84.84"},"temperature":{"N":"55.66"},"device":{"S":"foo"},"timestamp":{"S":"2024-07-12T01:17:42"}},"SizeBytes":99,"ApproximateCreationDateTimePrecision":"MICROSECOND"},"eventSource":"aws:dynamodb"}
```


## Documentation
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds_gettingstarted.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/getting-started-step-1.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/getting-started-step-2.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/example_dynamodb_Scenario_GettingStartedMovies_section.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/streamsmain.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html#HowItWorks.CoreComponents.PrimaryKey
- https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_CreateTable.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ql-reference.update.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html#HowItWorks.CoreComponents.TablesItemsAttributes
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/streamsmain.html

## Resources
- https://aws.amazon.com/blogs/database/choose-the-right-change-data-capture-strategy-for-your-amazon-dynamodb-applications/
- https://www.singlestore.com/blog/cdc-data-from-dynamodb-to-singlestore-using-dynamodb-streams/
- https://medium.com/event-driven-utopia/aws-dynamodb-streams-change-data-capture-for-dynamodb-tables-d4c92f9639d3


[change data capture (CDC)]: https://en.wikipedia.org/wiki/Change_data_capture
[Change data capture for DynamoDB Streams]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
[DynamoDB]: https://aws.amazon.com/dynamodb/
[Kinesis]: https://aws.amazon.com/kinesis/
[SQLAlchemy]: https://www.sqlalchemy.org/
[Using Kinesis Data Streams to capture changes to DynamoDB]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/kds.html
