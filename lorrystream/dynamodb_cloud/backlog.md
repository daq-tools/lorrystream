# DynamoDB CDC processing backlog

## Iteration +1
- Improve type mapping.
- Use SQLAlchemy for generating and submitting SQL statement.
- Improve efficiency by using bulk operations when applicable. 

CREATE TABLE transactions (data OBJECT(DYNAMIC));
CREATE TABLE transactions (id INT) WITH (column_policy = 'dynamic');