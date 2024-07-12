# DynamoDB CDC to CrateDB using DynamoDB Streams Kinesis Adapter


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
OLAP database, using the [DynamoDB Streams Kinesis Adapter]
([GitHub][DynamoDB Streams Kinesis Adapter for Java]).

> Using the Amazon Kinesis Adapter is the recommended way to
> consume streams from Amazon DynamoDB.
>
> -- [Using the DynamoDB Streams Kinesis adapter to process stream records]


## What's Inside

- On a compute-environment of your choice, supporting Python, a traditional
  KCL v2 application using the client-side DynamoDB Streams Kinesis Adapter,
  subscribes to a DynamoDB Change Stream, which is pretending to be a Kinesis
  Stream, in order to receive published CDC opslog messages.

- On the egress side, the application re-materializes the items of the
  operations log into any database with [SQLAlchemy] support.


## Holzweg!

It looks like the "DynamoDB Streams Kinesis Adapter" project is dead.

- https://github.com/awslabs/dynamodb-streams-kinesis-adapter/issues/40
- https://github.com/awslabs/dynamodb-streams-kinesis-adapter/issues/42
- https://github.com/awslabs/dynamodb-streams-kinesis-adapter/issues/46

There would be an option to try this by downgrading to KCL v1. We are not
sure if it is worth to try it, though.


[change data capture (CDC)]: https://en.wikipedia.org/wiki/Change_data_capture
[Change data capture for DynamoDB Streams]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
[DynamoDB]: https://aws.amazon.com/dynamodb/
[DynamoDB Streams Kinesis Adapter]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.KCLAdapter.html
[DynamoDB Streams Kinesis Adapter for Java]: https://github.com/awslabs/dynamodb-streams-kinesis-adapter
[Kinesis]: https://aws.amazon.com/kinesis/
[SQLAlchemy]: https://www.sqlalchemy.org/
[Using the DynamoDB Streams Kinesis adapter to process stream records]: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.KCLAdapter.html 
