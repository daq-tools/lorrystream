# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import logging
import re
import typing as t

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import Engine
from streamz import Sink, Stream

from lorrystream.exceptions import InvalidSinkError

logger = logging.getLogger(__name__)


@Stream.register_api()
class dataframe_to_sql(Sink):
    """
    Store data into SQLAlchemy-compatible database.

    Requires ``sqlalchemy``

    :param dburi: str
        SQLAlchemy connection URI.
    :param engine_options:
        Propagated to SQLAlchemy's ``create_engine(**kwargs)``.
    """

    def __init__(self, upstream, dburi, engine_options=None, **kwargs):
        self.dburi = dburi
        self.engine: t.Union[Engine, None] = None
        self.engine_options = engine_options or {}
        self.table_name = None
        self.if_exists = "append"
        self.method = None
        self.chunksize = 10_000
        super().__init__(upstream, ensure_io_loop=True, **kwargs)

    def update(self, x, who=None, metadata=None):
        """
        Store packets into database.
        """
        df: pd.DataFrame = x
        logger.info(f"to_sql.update: who={who}, metadata={metadata}")
        df.info()
        print(df)  # noqa: T201

        if self.engine is None:
            logger.info(f"Connecting to {self.dburi}")
            # TODO: Improve.
            matches = re.match(r"^.*table=(\w*)", self.dburi)
            if matches:
                self.table_name = matches.group(1)
            else:
                raise InvalidSinkError("Unable to obtain table name")
            matches = re.match(r"^.*if_exists=(\w*)", self.dburi)
            if matches:
                self.if_exists = matches.group(1)
            dburi = re.sub(r"\?.*", "", self.dburi)
            logger.info(f"Effective dburi: {dburi}")
            logger.info(f"Writing to table: {self.table_name}, if_exists={self.if_exists}")
            self.engine = sa.create_engine(dburi, **self.engine_options)

            # Use CrateDB bulk operations endpoint for improved efficiency.
            if self.dburi.startswith("crate"):
                self.method = self.insert_bulk

        df.to_sql(
            name=self.table_name,
            con=self.engine,
            if_exists=self.if_exists,
            index=False,
            chunksize=self.chunksize,
            method=self.method,
        )

    @staticmethod
    def insert_bulk(pd_table, conn, keys, data_iter):
        """
        A fast insert method for pandas and Dask, using CrateDB's "bulk operations" endpoint.

        The idea is to break out of SQLAlchemy, compile the insert statement, and use the raw
        DBAPI connection client, in order to invoke a request using `bulk_parameters`::

            cursor.execute(sql=sql, bulk_parameters=data)

        - https://crate.io/docs/crate/reference/en/5.2/interfaces/http.html#bulk-operations
        """

        """
        # Vanilla
        # This is the regular implementation, using SQLAlchemy.
        data = [dict(zip(keys, row)) for row in data_iter]
        conn.execute(pd_table.table.insert(), data)
        """

        # Bulk
        sql = str(pd_table.table.insert().compile(bind=conn))
        data = list(data_iter)

        logger.info(f"Bulk SQL:     {sql}")
        logger.info(f"Bulk records: {len(data)}")

        cursor = conn._dbapi_connection.cursor()
        cursor.execute(sql=sql, bulk_parameters=data)
        cursor.close()

    def destroy(self):
        if self.engine is not None:
            logger.info(f"Disconnecting from {self.dburi}")
            self.engine.dispose()
        super().destroy()
