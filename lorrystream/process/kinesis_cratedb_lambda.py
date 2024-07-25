# Copyright (c) 2024 The Kotori developers and contributors.
# Distributed under the terms of the Apache 2 license.
"""
Consume an AWS Kinesis Stream and relay into CrateDB.
- https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis-example.html
- https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html

In order to run, this module/program needs the following
3rd party libraries, defined using inline script metadata.
"""
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "commons-codec==0.0.2",
#   "sqlalchemy-cratedb==0.38.0",
# ]
# ///
import base64
import json
import logging
import os
import sys
import typing as t

import sqlalchemy as sa
from commons_codec.transform.dynamodb import DynamoCDCTranslatorCrateDB
from sqlalchemy.util import asbool

ON_ERROR_TYPE = t.Literal["exit", "ignore", "raise"]

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
USE_BATCH_PROCESSING: bool = asbool(os.environ.get("USE_BATCH_PROCESSING", "false"))
ON_ERROR: ON_ERROR_TYPE = t.cast(ON_ERROR_TYPE, os.environ.get("ON_ERROR", "exit"))
SQL_ECHO: bool = asbool(os.environ.get("SQL_ECHO", "false"))
SINK_SQLALCHEMY_URL: str = os.environ.get("SINK_SQLALCHEMY_URL", "crate://")
SINK_TABLE: str = os.environ.get("SINK_TABLE", "default")

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
engine = sa.create_engine(SINK_SQLALCHEMY_URL, echo=SQL_ECHO)

# TODO: Automatically create destination table.
cdc = DynamoCDCTranslatorCrateDB(table_name=SINK_TABLE)

# Create the database connection outside the handler to allow
# connections to be re-used by subsequent function invocations.
try:
    connection = engine.connect()
except Exception:
    logger.exception("Connection to sink database failed")

logger.info("Connected to sink database")


def handler(event, context):
    """
    Implement partial batch response for Lambda functions that receive events from
    a Kinesis stream. The function reports the batch item failures in the response,
    signaling to Lambda to retry those messages later.
    """

    cur_record_sequence_number = ""
    logger.debug("context: %s", context)

    for record in event["Records"]:
        event_id = record["eventID"]
        try:

            # Log and decode event.
            # TODO: Remove log statements for better performance?
            logger.debug(f"Processed Kinesis Event - EventID: {event_id}")
            record_data = json.loads(base64.b64decode(record["kinesis"]["data"]).decode("utf-8"))
            logger.debug(f"Record Data: {record_data}")

            # Process record.
            sql = cdc.to_sql(record_data)
            connection.execute(sa.text(sql))
            connection.commit()

            # Bookkeeping.
            cur_record_sequence_number = record["kinesis"]["sequenceNumber"]

        except Exception as ex:
            error_message = f"An error occurred processing event: {event_id}"
            logger.exception(error_message)
            if USE_BATCH_PROCESSING:
                # Return failed record's sequence number.
                return {"batchItemFailures": [{"itemIdentifier": cur_record_sequence_number}]}
            if ON_ERROR == "exit":
                sys.exit(6)
            elif ON_ERROR == "ignore":
                pass
            elif ON_ERROR == "raise":
                raise ex
            else:
                raise ValueError(f"Invalid value for ON_ERROR: {ON_ERROR}") from ex

    logger.info(f"Successfully processed {len(event['Records'])} records")
    if USE_BATCH_PROCESSING:
        return {"batchItemFailures": []}
    return None
