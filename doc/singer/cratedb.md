# Singer components for CrateDB

## CrateDB
[CrateDB] is a distributed and scalable SQL database for storing and analyzing
massive amounts of data in near real-time, even with complex queries. It is
PostgreSQL-compatible, and based on [Apache Lucene].

CrateDB offers a Python SQLAlchemy dialect, in order to plug into the
comprehensive Python data-science and -wrangling ecosystems.

## SQLAlchemy
> [SQLAlchemy] is the leading Python SQL toolkit and Object Relational Mapper
that gives application developers the full power and flexibility of SQL.
>
> It provides a full suite of well known enterprise-level persistence patterns,
designed for efficient and high-performing database access, adapted into a
simple and Pythonic domain language.

## Resources
- [meltano-tap-cratedb]
- [meltano-target-cratedb]


[Apache Lucene]: https://lucene.apache.org/
[CrateDB]: https://cratedb.com/product
[CrateDB Cloud]: https://console.cratedb.cloud/
[meltano-tap-cratedb]: https://github.com/crate-workbench/meltano-tap-cratedb
[meltano-target-cratedb]: https://github.com/crate-workbench/meltano-target-cratedb
[SQLAlchemy]: https://www.sqlalchemy.org/
[vanilla package on PyPI]: https://pypi.org/project/meltano-target-cratedb/
