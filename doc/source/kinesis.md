# Amazon Kinesis Source

## LocalStack Testbed
The recipe uses the LocalStack AWS environment to run an Amazon Kinesis surrogate.
The walkthrough follows the [Get started with Kinesis on LocalStack] tutorial.

Start the LocalStack service using Docker.
```shell
docker run \
  --rm -it \
  -p 127.0.0.1:4566:4566 \
  -p 127.0.0.1:4510-4559:4510-4559 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  localstack/localstack:3.6
```
:::{tip}
LocalStack is a cloud service emulator that runs in a single container on your
laptop or in your CI environment. With LocalStack, you can run your AWS
applications or Lambdas entirely on your local machine without connecting to
a remote cloud provider.
:::

Install LorryStream including LocalStack CLI programs.
```shell
pip install lorrystream
```
Create a Kinesis Data Stream called `testdrive`.
```shell
awslocal kinesis create-stream \
  --stream-name testdrive \
  --shard-count 1
```
Check the status of your streams.
```shell
awslocal kinesis list-streams
```
```shell
awslocal kinesis describe-stream \
  --stream-name testdrive
```
Display Stream ARN.
```shell
awslocal kinesis describe-stream --stream-name testdrive | jq -r .StreamDescription.StreamARN
```

Submit an item to the data stream, using `awslocal`.
```shell
awslocal kinesis put-record \
    --stream-name testdrive \
    --partition-key 1 \
    --data '{"device": "foo", "temperature": 42.42, "humidity": 84.84}'
```

Submit an item to the data stream, using Python.
```shell
export AWS_ENDPOINT_URL="http://localhost:4566"
python examples/aws/kinesis_publish.py testdrive
```

Consume data stream, printing received payloads to STDOUT.
This is suitable for debugging purposes.
```shell
export AWS_ENDPOINT_URL="http://localhost:4566"
python examples/aws/kinesis_subscribe.py testdrive
```

[Get started with Kinesis on LocalStack]: https://docs.localstack.cloud/user-guide/aws/kinesis/
