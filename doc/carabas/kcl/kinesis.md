# Kinesis Streams to CrateDB

## About
A stream processor component using the [Kinesis Client Library (KCL)].
It is written in Python, and uses the [amazon-kclpy] Python SDK for KCL
([GitHub][amazon-kclpy-github]).
 
## What's Inside
- Publishing and subscribing to [Kinesis] streams, using Python.

## Setup
Create a Kinesis stream, and set up a Python sandbox for connecting
to it using KCL v2.

This section reflects configuration settings stored in
[record_processor.properties](../../../lorrystream/spike/kcl_kinesis/record_processor.properties).

### AWS
Configure a Kinesis Stream, and an IAM policy, because Kinesis needs to create
and maintain a "[leases table]" stored in DynamoDB, so it requires corresponding
permissions to do so.

- Create a [Kinesis] stream called `testdrive-stream`, per [Kinesis Console].
- [Create an IAM Policy and User], applying the permissions outlined on this page.
  Two example ARN IDs, that address relevant resources in Kinesis and DynamoDB, are:
  ```text
  arn:aws:kinesis:us-east-1:841394475918:stream/testdrive-stream
  arn:aws:dynamodb:us-east-1:841394475918:table/stream-demo
  ```
- The leases table in DynamoDB will be automatically created when the first
  stream consumer (the KCL application) becomes active.

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
cd lorrystream/kinesis
pip install wheel
pip install --verbose -r requirements.txt
```
Note that the first installation of the [amazon-kclpy] package on your machine
will take a while, because it will download a bunch of JAR files, defined by a
traditional [pom.xml] recipe, before embedding them into the Python package.

On subsequent installations, as long as you don't switch versions, that package
will install from your local package cache, so it will be much faster.

Alternative: Use ready-made wheel package. Note to self: Need to provide this to
the colleagues.
```shell
pip install ./dist/amazon_kclpy-2.1.5-py3-none-any.whl
```

## Usage
You will need multiple terminal windows. Within both of them, activate the
virtualenv on the top-level directory. Then, navigate to the playground
directory, and seed AWS credentials.
```shell
source .venv/bin/activate
cd lorrystream/kinesis
export AWS_ACCESS_KEY=...
export AWS_SECRET_ACCESS_KEY=...
```

Launch the stream processor, subscribing to the stream.
```shell
$(sh launch.sh record_processor.properties)
```

Watch actions of the record processor.
```shell
tail -F record_processor.log
```

Publish a demo message to the stream.
```shell
python publish.py
```

## Documentation
- https://docs.aws.amazon.com/streams/latest/dev/building-consumers.html

## Resources
- https://dev.solita.fi/2020/05/28/kinesis-streams-part-1.html
- https://dev.solita.fi/2020/12/21/kinesis-streams-part-2.html
- https://github.com/aws-samples/amazon-kinesis-data-processor-aws-fargate


[amazon-kclpy]: https://pypi.org/project/amazon-kclpy
[amazon-kclpy-github]: https://github.com/awslabs/amazon-kinesis-client-python
[Create an IAM Policy and User]: https://docs.aws.amazon.com/streams/latest/dev/tutorial-stock-data-kplkcl2-iam.html
[DynamoDB]: https://aws.amazon.com/dynamodb/
[DynamoDB Console]: https://console.aws.amazon.com/dynamodbv2/
[Kinesis]: https://aws.amazon.com/kinesis/
[Kinesis Console]: https://console.aws.amazon.com/kinesis/
[Kinesis Client Library (KCL)]: https://docs.aws.amazon.com/streams/latest/dev/shared-throughput-kcl-consumers.html
[leases table]: https://aws.amazon.com/blogs/big-data/processing-amazon-dynamodb-streams-using-the-amazon-kinesis-client-library/
[pom.xml]: https://github.com/awslabs/amazon-kinesis-client-python/blob/v2.1.5/pom.xml
