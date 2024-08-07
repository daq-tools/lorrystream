(aws-dms-handbook)=
# AWS DMS Handbook

A few useful AWSCLI commands to check the status of the DMS engine and
relevant pipeline elements. You can also use the AWS Web Console to
inspect and commandeer the same details.


## Status Checks
Display ARNs of all replication instances.
```shell
aws dms describe-replication-instances | jq -r '.ReplicationInstances[].ReplicationInstanceArn'
```
Display replication endpoints and relevant connection settings.
```shell
aws dms describe-endpoints
```
Invoke connection test on given DMS endpoint.
```shell
aws dms test-connection \
  --replication-instance-arn arn:aws:dms:eu-central-1:831394476016:rep:JD2LL6OM35BJZNKZIRSOE2FXIY \
  --endpoint-arn arn:aws:dms:eu-central-1:831394476016:endpoint:3IVDGL6E4RDNBF2LFBYF6DYV3Y
```
Display connection test results.
```shell
aws dms describe-connections
```


## Operations
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


## Logging
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


## CloudFormation
When the CloudFormation deployment is stuck, or if you want to start from scratch,
those commands are useful.
```shell
aws cloudformation continue-update-rollback --stack-name testdrive-dms-postgresql-dev
aws cloudformation delete-stack --stack-name testdrive-dms-postgresql-dev
```
