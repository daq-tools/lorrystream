# DynamoDB CDC processing backlog

## Iteration +1
- [x] Improve type mapping
- [x] Generalize CDC event -> SQL translator
- [ ] Distill into a Lambda variant
- [ ] Automation!
  - [ ] DDL: CREATE TABLE <tablename> (data OBJECT(DYNAMIC));
  - [ ] Wrap KCL launcher into manager component

## Iteration +2
- [ ] Performance improvements (simdjson?)
- [ ] Use SQLAlchemy for generating and submitting SQL statement
- [ ] Improve efficiency by using bulk operations when applicable

## Research
- https://pypi.org/project/core-cdc
- https://github.com/sshd123/pypgoutput
- https://pypi.org/project/pypg-cdc/
- https://github.com/hcevikGA/dynamo-wrapper
- https://pypi.org/project/dynamo-pandas/
- https://aws.amazon.com/de/blogs/opensource/announcing-partiql-one-query-language-for-all-your-data/
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ql-reference.html
- https://partiql.org/dql/overview.html
