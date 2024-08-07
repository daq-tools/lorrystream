(aws-dms-postgresql)=
# AWS DMS with PostgreSQL source

## What's Inside
- [Using a PostgreSQL database as an AWS DMS source]

### Prerequisites
First of all, activate the `pglocical` extension on your RDS PostgreSQL instance.
```sql
CREATE EXTENSION pglogical;
SELECT * FROM pg_catalog.pg_extension WHERE extname='pglogical';
```

```sql
SHOW shared_preload_libraries;
SELECT name, setting FROM pg_settings WHERE name in ('rds.logical_replication','shared_preload_libraries');
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



```sql
UPDATE foo SET age=32 WHERE name='Jane';
UPDATE foo SET age=33 WHERE id=43;
UPDATE foo SET age=33 WHERE attributes->>'foo'='bar';
UPDATE foo SET attributes = jsonb_set(attributes, '{last_name}', '"Doe"', true) WHERE name='John';
```
```sql
DELETE FROM foo WHERE name='Jane';
DELETE FROM foo WHERE name='John';
```



[Using a PostgreSQL database as an AWS DMS source]: https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html
