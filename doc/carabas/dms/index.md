(aws-dms)=
# Pipelines with AWS DMS

_AWS DMS to Kinesis to CrateDB._

## What's Inside
- [Working with AWS DMS tasks]
- [Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service]
- An IaC driver program based on [AWS CloudFormation] technologies using the
  [cottonformation] Python API. It can be used to set up infrastructure on AWS
  without much ado.
- DMS: Full load and CDC
- DMS Source: RDS PostgreSQL
- DMS Target: Amazon Kinesis
- CDC Target: CrateDB Cloud


## AWS Infrastructure Setup
The following walkthrough describes a full deployment of AWS DMS including
relevant outbound data processors for demonstration purposes.

In order to run it in production, you are welcome to derive from it and tweak
it for your own purposes. YMMV. If you need support, don't hesitate to ask for
help.

### Install
Install LorryStream.
```shell
pip install lorrystream
```
Acquire IaC driver program.
```shell
wget https://github.com/daq-tools/lorrystream/raw/main/examples/aws/rds_postgresql_kinesis_lambda_oci_cratedb.py
```

### Configure
Please configure endpoint and replication settings within the source code
of the IaC program you just acquired, and presented next.

### Deploy
First, prepare an AWS ECR repository for publishing the OCI image including your
downstream processor element that is consuming the replication data stream from
Amazon Kinesis, and runs it into CrateDB. To learn about how this works, please
visit the documentation section about the [](project:#ecr-repository).

Configure CrateDB database sink address.
```shell
export SINK_SQLALCHEMY_URL='crate://admin:dZ..qB@example.eks1.eu-west-1.aws.cratedb.net:4200/?ssl=true'
```

Invoke the IaC driver program in order to deploy relevant resources on AWS.
```shell
python examples/aws/rds_postgresql_kinesis_lambda_oci_cratedb.py
```

After deployment succeeded, you will be presented a corresponding response including
relevant information about entrypoints to the software stack you've just created.
```text
Result of CloudFormation deployment:
psql command: psql "postgresql://dynapipe:secret11@testdrive-dms-postgresql-dev-db.czylftvqn1ed.eu-central-1.rds.amazonaws.com:5432/postgres"
RDS Instance ARN: arn:aws:rds:eu-central-1:831394476016:db:testdrive-dms-postgresql-dev-db
Stream ARN: arn:aws:kinesis:eu-central-1:831394476016:stream/testdrive-dms-postgresql-dev-stream
Replication ARN: arn:aws:dms:eu-central-1:831394476016:replication-config:EAM3JEHXGBGZBPN5PLON7NPDEE
```

:::{note}
Please note this is a demonstration stack, deviating from typical real-world situations.

- Contrary to this stack, which includes an RDS PostgreSQL instance, a database instance
  will already be up and running, so the remaining task is to just configure the Kinesis
  Data Stream and consume it.

- Contrary to this stack, which uses AWS Lambda to host the downstream processor element,
  when aiming for better cost-effectiveness, you will run corresponding code on a dedicated
  computing environment.
:::


## Operations
Please consult the [](project:#aws-dms-handbook) to learn about commands
suitable for operating the AWS DMS engine.

:::{toctree}
:hidden:

handbook
:::



## Usage

### DMS
AWS DMS provides `full-load` and `full-load-and-cdc` migration types.
For a `full-load-and-cdc` task, AWS DMS migrates table data, and then applies
data changes that occur on the source, automatically establishing continuous
replication.

When starting a replication task using [StartReplicationTask], you can use those
possible values for `--start-replication-task-type`, see also [start-replication-task]:

:start-replication:
    The only valid value for the first run of the task when the migration type is
    `full-load` or `full-load-and-cdc`

:resume-processing:
    Not applicable for any full-load task, because you can't resume partially loaded
    tables during the full load phase. Use it to replicate the changes from the last
    stop position.
    
:reload-target:
    For a `full-load-and-cdc` task, load all the tables again, and start capturing
    source changes.


## Migration by DMS Source
This section enumerates specific information to consider when aiming to use DMS
for your database as a source element.

:::{toctree}
:maxdepth: 2

postgresql
mysql
:::



[AWS CloudFormation]: https://en.wikipedia.org/wiki/AWS_CloudFormation
[cottonformation]: https://pypi.org/project/cottonformation/
[StartReplicationTask]: https://docs.aws.amazon.com/dms/latest/APIReference/API_StartReplicationTask.html
[start-replication-task]: https://docs.aws.amazon.com/cli/latest/reference/dms/start-replication-task.html
[Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html
[Using object mapping to migrate data to a Kinesis data stream]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html#CHAP_Target.Kinesis.ObjectMapping
[Working with AWS DMS tasks]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.html
