# Pipelines with AWS DMS

_AWS DMS to Kinesis to CrateDB._

## What's Inside
- [Using a PostgreSQL database as an AWS DMS source]
- [Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service]
- Full load and CDC
- Source: RDS PostgreSQL
- Target: CrateDB Cloud


## Infrastructure Setup

### CrateDB Table
The destination table name in CrateDB, where the CDC record
processor will re-materialize CDC events into.
```shell
pip install crash
crash -c "CREATE TABLE public.foo (data OBJECT(DYNAMIC));"
```

### Deploy
The following walkthrough describes a full deployment of AWS DMS including relevant
outbound data processors for demonstration purposes. In order to run it in production,
you are welcome to derive from it and tweak it for your own purposes.

Configure CrateDB database sink address.
```shell
export SINK_SQLALCHEMY_URL='crate://admin:dZ..qB@example.eks1.eu-west-1.aws.cratedb.net:4200/?ssl=true'
```

Invoking the IaC driver program in order to deploy relevant resources on AWS
using CloudFormation is fundamental.
```shell
python examples/aws/rds_postgresql_kinesis_lambda_oci_cratedb.py
```

After deployment succeeded, you will be presented a corresponding
response including relevant information about entrypoints to the software
stack you've just created. 
```text
Result of CloudFormation deployment:
psql command: psql "postgresql://dynapipe:secret11@testdrive-dms-postgresql-dev-db.czylftvqn1ed.eu-central-1.rds.amazonaws.com:5432/postgres"
RDS Instance ARN: arn:aws:rds:eu-central-1:831394476016:db:testdrive-dms-postgresql-dev-db
Stream ARN: arn:aws:kinesis:eu-central-1:831394476016:stream/testdrive-dms-postgresql-dev-stream
Replication ARN: arn:aws:dms:eu-central-1:831394476016:replication-config:EAM3JEHXGBGZBPN5PLON7NPDEE
```

### Status Checks

Display ARN of replication instances.
```shell
aws dms describe-replication-instances | jq -r '.ReplicationInstances[].ReplicationInstanceArn'
```

Display replication endpoints and relevant connection settings.
```shell
aws dms describe-endpoints
```

```shell
aws dms test-connection \
  --replication-instance-arn arn:aws:dms:eu-central-1:831394476016:rep:JD2LL6OM35BJZNKZIRSOE2FXIY \
  --endpoint-arn arn:aws:dms:eu-central-1:831394476016:endpoint:3IVDGL6E4RDNBF2LFBYF6DYV3Y

aws dms describe-connections
```


## Usage

### Prerequisites
First of all, activate the `pglocical` extension on your RDS PostgreSQL instance.
```sql
CREATE EXTENSION pglogical;
SELECT * FROM pg_catalog.pg_extension WHERE extname='pglogical';
```

### Data in Source
After that, connect to RDS PostgreSQL, and provision a little bunch of data.
```sql
DROP TABLE IF EXISTS foo CASCADE;
CREATE TABLE foo (id INT PRIMARY KEY, name TEXT, age INT, attributes JSONB);
INSERT INTO foo (id, name, age, attributes) VALUES (42, 'John', 30, '{"foo": "bar"}');
INSERT INTO foo (id, name, age, attributes) VALUES (43, 'Jane', 31, '{"baz": "qux"}');
```

### Data in Target
```sql
cr> SELECT * FROM public.foo;
```
```postgresql
+---------------------------------------------------------------------+
| data                                                                |
+---------------------------------------------------------------------+
| {"age": 30, "attributes": {"foo": "bar"}, "id": 42, "name": "John"} |
| {"age": 31, "attributes": {"baz": "qux"}, "id": 43, "name": "Jane"} |
+---------------------------------------------------------------------+
```

### Operations
Enumerate all configured replication tasks with compact output.
```shell
aws dms describe-replication-tasks | \
  jq '.ReplicationTasks[] | {ReplicationTaskIdentifier, ReplicationTaskArn, MigrationType, StartReplicationType, Status, StopReason, FailureMessages, ProvisionData}'
```
Start replication task with given ARN.
```shell
aws dms start-replication-task \
  --start-replication-task-type start-replication --replication-task-arn \
  arn:aws:dms:eu-central-1:831394476016:task:7QBLNBTPCNDEBG7CHI3WA73YFA
```
Stop replication task with given ARN.
```shell
aws dms stop-replication-task --replication-task-arn \
  arn:aws:dms:eu-central-1:831394476016:task:7QBLNBTPCNDEBG7CHI3WA73YFA
```


### Logging

To see detailed progress about the replication process, use CloudWatch to
inspect corresponding log output.

Enumerate all log groups.
```shell
aws logs describe-log-groups
```

Get log output history.
```shell
aws logs get-log-events \
  --log-group-name dms-tasks-testdrive-dms-instance \
  --log-stream-name dms-task-7QBLNBTPCNDEBG7CHI3WA73YFA | jq .events[].message
```

Start watching the log output using the `start-live-tail` CloudWatch operation.
```shell
aws logs start-live-tail --log-group-identifiers \
    arn:aws:logs:eu-central-1:831394476016:log-group:/aws/rds/instance/testdrive-dms-postgresql-dev-db/postgresql \
    arn:aws:logs:eu-central-1:831394476016:log-group:dms-tasks-testdrive-dms-instance
```


## Appendix

### CloudFormation

```shell
aws cloudformation continue-update-rollback --stack-name testdrive-dms-postgresql-dev
aws cloudformation delete-stack --stack-name testdrive-dms-postgresql-dev
```

```sql
SHOW shared_preload_libraries;
SELECT name, setting FROM pg_settings WHERE name in ('rds.logical_replication','shared_preload_libraries');
```

- https://docs.aws.amazon.com/dms/latest/APIReference/API_StartReplication.html#DMS-StartReplication-request-StartReplicationType
- https://docs.aws.amazon.com/cli/latest/reference/dms/start-replication-task.html

Possible values for `--start-replication-type`:

- start-replication
- resume-processing
- reload-target    

```sql
update foo set age=32 where name='Jane';
update foo set age=33 where id=43;
update foo set age=33 where attributes->>'foo'='bar';
update foo set attributes = jsonb_set(attributes, '{last_name}', '"Doe"', true) where name='John';
```
```sql
delete from foo where name='Jane';
delete from foo where name='John';
```


[AWS::DMS::ReplicationConfig]: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-dms-replicationconfig.html
[Using a PostgreSQL database as an AWS DMS source]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html
[Using Amazon Kinesis Data Streams as a target for AWS Database Migration Service]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html
[Using object mapping to migrate data to a Kinesis data stream]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html#CHAP_Target.Kinesis.ObjectMapping
