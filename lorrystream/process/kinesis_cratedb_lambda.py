# Copyright (c) 2024 The Panodata Developers and contributors.
# Distributed under the terms of the Apache 2 license.
"""
Using an AWS Lambda, consume an AWS Kinesis Stream of CDC data, and relay
into CrateDB, re-materializing the original information into an OBJECT
column `data`.

Currently supported CDC message formats:

- AWS DMS
- AWS DynamoDB

Details:
When using `ON_ERROR = exit`, the processor uses Linux exit codes for
signalling error conditions, see https://stackoverflow.com/a/76187305.

Resources:
- https://docs.aws.amazon.com/lambda/latest/dg/with-kinesis-example.html
- https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html
"""
# In order to run, this module/program needs the following
# 3rd party libraries, defined using inline script metadata.
#
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "commons-codec",
#   "sqlalchemy-cratedb>=0.38.0",
# ]
# ///
import base64
import json
import logging
import os
import sys

import sqlalchemy as sa
from commons_codec.exception import UnknownOperationError
from commons_codec.model import ColumnMappingStrategy, ColumnTypeMapStore
from commons_codec.transform.aws_dms import DMSTranslatorCrateDB, DMSTranslatorCrateDBRecordFactory
from commons_codec.transform.dynamodb import DynamoDBCDCTranslator
from sqlalchemy.util import asbool

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
USE_BATCH_PROCESSING: bool = asbool(os.environ.get("USE_BATCH_PROCESSING", "false"))
ON_ERROR: str = os.environ.get("ON_ERROR", "exit")
SQL_ECHO: bool = asbool(os.environ.get("SQL_ECHO", "false"))

MESSAGE_FORMAT: str = os.environ.get("MESSAGE_FORMAT", "unknown")
COLUMN_TYPES: str = os.environ.get("COLUMN_TYPES", "")
SINK_SQLALCHEMY_URL: str = os.environ.get("SINK_SQLALCHEMY_URL", "crate://")
SINK_TABLE: str = os.environ.get("SINK_TABLE", "default")

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)


# Sanity checks.
# If any value is invalid, terminate by signalling "22 - Invalid argument".
error_strategies = ["exit", "ignore", "raise"]
message_formats = ["dms", "dynamodb"]
if ON_ERROR not in error_strategies:
    message = f"Invalid value for ON_ERROR: {ON_ERROR}. Use one of: {error_strategies}"
    logger.fatal(message)
    sys.exit(22)
if MESSAGE_FORMAT not in message_formats:
    message = f"Invalid value for MESSAGE_FORMAT: {MESSAGE_FORMAT}. Use one of: {message_formats}"
    logger.fatal(message)
    sys.exit(22)
try:
    column_types = ColumnTypeMapStore.from_json(COLUMN_TYPES)
except Exception as ex:
    message = f"Invalid value for COLUMN_TYPES: {COLUMN_TYPES}. Reason: {ex}. Use JSON."
    logger.fatal(message)
    sys.exit(22)

# TODO: Automatically create destination table.
# TODO: Propagate mapping definitions and other settings.
# TODO: Propagate column mapping strategy.
if MESSAGE_FORMAT == "dms":
    DMSTranslatorCrateDBRecordFactory.DEFAULT_MAPPING_STRATEGY = ColumnMappingStrategy.UNIVERSAL
    cdc = DMSTranslatorCrateDB(column_types=column_types)
elif MESSAGE_FORMAT == "dynamodb":
    cdc = DynamoDBCDCTranslator(table_name=SINK_TABLE)

# Create the database connection outside the handler to allow
# connections to be re-used by subsequent function invocations.
# TODO: Examine long-running jobs about successful reconnection behavior.
try:
    engine = sa.create_engine(SINK_SQLALCHEMY_URL, echo=SQL_ECHO)
    connection: sa.engine.Connection = engine.connect()
    logger.info(f"Connection to sink database succeeded: {SINK_SQLALCHEMY_URL}")
except Exception as ex:
    logger.exception(f"Connection to sink database failed: {SINK_SQLALCHEMY_URL}")
    if ON_ERROR == "exit":
        # Signal "Resource temporarily unavailable" when connection to database fails.
        sys.exit(11)
    elif ON_ERROR == "ignore":
        pass
    elif ON_ERROR == "raise":
        raise ex


def handler(event, context):
    """
    Implement partial batch response for Lambda functions that receive events from
    a Kinesis stream. The function reports the batch item failures in the response,
    signaling to Lambda to retry those messages later.
    """

    cur_record_sequence_number = ""
    logger.debug("context: %s", context)

    for record in event["Records"]:
        logger.debug(f"Record: {record}")
        event_id = record["eventID"]
        try:

            # Log and decode event.
            # TODO: Remove log statements for better performance?
            logger.debug(f"Processed Kinesis Event - EventID: {event_id}")
            record_data = json.loads(base64.b64decode(record["kinesis"]["data"]).decode("utf-8"))
            logger.debug(f"Record Data: {record_data}")

            # Process record.
            operation = cdc.to_sql(record_data)
            connection.execute(sa.text(operation.statement), operation.parameters)
            connection.commit()  # type: ignore[attr-defined]

            # Bookkeeping.
            cur_record_sequence_number = record["kinesis"]["sequenceNumber"]

        except UnknownOperationError as ex:
            logger.warning(f"Ignoring message. Reason: {ex}. Record: {ex.record}")

        except Exception as ex:
            error_message = f"An error occurred processing event: {event_id}"
            logger.exception(error_message)
            if USE_BATCH_PROCESSING:
                # Return failed record's sequence number.
                return {"batchItemFailures": [{"itemIdentifier": cur_record_sequence_number}]}
            if ON_ERROR == "exit":
                # Signal "Input/output error" when error happens while processing data.
                sys.exit(5)
            elif ON_ERROR == "ignore":
                pass
            elif ON_ERROR == "raise":
                raise ex

    logger.info(f"Successfully processed {len(event['Records'])} records")
    if USE_BATCH_PROCESSING:
        return {"batchItemFailures": []}
    return None
