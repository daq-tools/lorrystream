# Pipelines with AWS Lambda


## What's inside
- A convenient [Infrastructure as code (IaC)] procedure to define data pipelines on [AWS].
- Written in Python, using [AWS CloudFormation] stack deployments. To learn
  what's behind, see also [How CloudFormation works].
- Code for running on [AWS Lambda] is packaged into [OCI] images, for efficient
  delta transfers, built-in versioning, and testing purposes.


## Details
- This specific document has a few general guidelines, and a
  a few specifics coming from `examples/aws/dynamodb_kinesis_lambda_oci_cratedb.py`.
- That program defines a pipeline which looks like this:
  
  DynamoDB CDC -> Kinesis Stream -> Python Lambda via OCI -> CrateDB


## OCI image
In order to package code for AWS Lambda functions packages into OCI images,
and use them, you will need to publish them to the AWS ECR container image
registry.

You will need to authenticate your local Docker environment, and create a
container image repository once for each project using a different runtime
image.

### Authenticate
Define your AWS ID, region label, and repository name, to be able to use
the templated commands 1:1.
```shell
aws_id=831394476016
aws_region=eu-central-1
repository_name=cratedb-kinesis-lambda
```
```shell
aws ecr get-login-password --region=${aws_region} | \
    docker login --username AWS --password-stdin ${aws_id}.dkr.ecr.${aws_region}.amazonaws.com
```

(ecr-repository)=
### ECR Repository
Just once, before proceeding, create an image repository hosting the runtime
code for your Lambda function.
```shell
aws ecr create-repository --region=${aws_region} \
    --repository-name=${repository_name} --image-tag-mutability=MUTABLE
```
In order to allow others to pull that image, you will need to define a
[repository policy] using the [set-repository-policy] subcommend of the AWS CLI.
In order to invoke that command, put the [](project:#ecr-repository-policy)
JSON definition into a file called `policy.json`.
```shell
aws ecr set-repository-policy --repository-name=${repository_name} --policy-text file://policy.json
```

### Troubleshooting
If you receive such an error message, your session has expired, and you need
to re-run the authentication step.
```text
denied: Your authorization token has expired. Reauthenticate and try again.
```

This error message indicates your ECR repository does not exist. The solution
is to create it, using the command shared above.
```text
name unknown: The repository with name 'cratedb-kinesis-lambda' does
not exist in the registry with id '831394476016'
```


## CrateDB Table
The destination table name in CrateDB, where the CDC record
processor will re-materialize CDC events into.
```shell
pip install crash
crash -c "CREATE TABLE transactions (data OBJECT(DYNAMIC));"
```


## Install
In order to exercise the example outlined below, you need to install
LorryStream.
```shell
pip install lorrystream
```


## Usage
For exercising an AWS pipeline, you need two components: The IaC description,
and a record processor implementation for the AWS Lambda. For example, choose
those two variants:

- IaC driver: [dynamodb_kinesis_lambda_oci_cratedb.py]
- Record processor: [kinesis_cratedb_lambda.py]

Putting them next to each other into a directory, and adjusting
`LambdaPythonImage(entrypoint_file=...)` should be enough to get you started.
Sure enough, you will also need to configure the `CRATEDB_SQLALCHEMY_URL`
environment variable properly.

Then, just invoke the IaC program to spin up the defined infrastructure on AWS.


## Operations
There are a few utility commands that help you operate the stack, that have not
been absorbed yet. See also [Monitoring and troubleshooting Lambda functions].

### Utilities
Check status of Lambda function.
```shell
aws lambda get-function \
  --function-name arn:aws:lambda:eu-central-1:831394476016:function:testdrive-dynamodb-dev-lambda-processor
```
Check status of stream mapping(s).
```shell
aws lambda list-event-source-mappings
```
Check logs.
```shell
aws logs describe-log-groups
aws logs start-live-tail --log-group-identifiers arn:aws:logs:eu-central-1:831394476016:log-group:/aws/lambda/DynamoDBCrateDBProcessor
```

### Test Flight I
Invoke the Lambda function for testing purposes.
```shell
aws lambda invoke \
    --function-name DynamoDBCrateDBProcessor \
    --payload file://records.json outputfile.txt
```
Pick `records.json` from [](project:#kinesis-example-event), it is a basic
example of an AWS Kinesis event message.

:::{note}
On AWS CLI v2, you may need that additional command line option.
```shell
--cli-binary-format raw-in-base64-out
```
:::

### Test Flight II
Trigger a real event by running two DML operations on the source database table.
```shell
READING_SQL="{'timestamp': '2024-07-12T01:17:42', 'device': 'foo', 'temperature': 42.42, 'humidity': 84.84}"

aws dynamodb execute-statement --statement \
  "INSERT INTO \"table-testdrive\" VALUE ${READING_SQL};"

aws dynamodb execute-statement --statement \
  "UPDATE \"table-testdrive\" SET temperature=43.59 WHERE \"device\"='foo' AND \"timestamp\"='2024-07-12T01:17:42';"
```


## Appendix

(ecr-repository-policy)=
### ECR Repository Policy
```json
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Sid": "allow public pull",
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ]
    }
  ]
}
```

(kinesis-example-event)=
### Kinesis Example Event
```json
{
  "Records": [
    {
      "kinesis": {
        "kinesisSchemaVersion": "1.0",
        "partitionKey": "1",
        "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
        "data": "SGVsbG8sIHRoaXMgaXMgYSB0ZXN0Lg==",
        "approximateArrivalTimestamp": 1545084650.987
      },
      "eventSource": "aws:kinesis",
      "eventVersion": "1.0",
      "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
      "eventName": "aws:kinesis:record",
      "invokeIdentityArn": "arn:aws:iam::111122223333:role/lambda-kinesis-role",
      "awsRegion": "us-east-2",
      "eventSourceARN": "arn:aws:kinesis:us-east-2:111122223333:stream/lambda-stream"
    }
  ]
}
```


[AWS]: https://en.wikipedia.org/wiki/Amazon_Web_Services
[AWS CloudFormation]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html 
[AWS Lambda]: https://en.wikipedia.org/wiki/AWS_Lambda
[dynamodb_kinesis_lambda_oci_cratedb.py]: https://github.com/daq-tools/lorrystream/blob/main/examples/aws/dynamodb_kinesis_lambda_oci_cratedb.py
[example program]: https://github.com/daq-tools/lorrystream/tree/main/examples/aws
[How CloudFormation works]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-overview.html
[Infrastructure as code (IaC)]: https://en.wikipedia.org/wiki/Infrastructure_as_code
[kinesis_cratedb_lambda.py]: https://github.com/daq-tools/lorrystream/blob/main/lorrystream/process/kinesis_cratedb_lambda.py
[Monitoring and troubleshooting Lambda functions]: https://docs.aws.amazon.com/lambda/latest/dg/lambda-monitoring.html 
[OCI]: https://en.wikipedia.org/wiki/Open_Container_Initiative
[repository policy]: https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#gettingstarted-images-permissions
[set-repository-policy]: https://docs.aws.amazon.com/cli/latest/reference/ecr/set-repository-policy.html
