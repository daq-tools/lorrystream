#!/usr/bin/python3

# Copyright 2014-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from __future__ import print_function

import json
import logging
import logging.handlers as handlers
import os
import time
import typing as t

from amazon_kclpy import kcl
from amazon_kclpy.v3 import processor
from commons_codec.transform.dynamodb import DynamoCDCTranslatorCrateDB
from cratedb_toolkit.util import DatabaseAdapter

logger = logging.getLogger(__name__)

IntOrNone = t.Union[int, None]
FloatOrNone = t.Union[float, None]


def setup_logging(logfile: str):
    """
    Configure Python logger to write to file, because stdout is used by MultiLangDaemon.
    """
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(module)s] %(levelname)s  %(funcName)s - %(message)s", "%H:%M:%S"
    )
    handler = handlers.RotatingFileHandler(logfile, maxBytes=10**6, backupCount=5)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RecordProcessor(processor.RecordProcessorBase):
    """
    Process data from a shard in a stream. Its methods will be called with this pattern:

    * initialize will be called once
    * process_records will be called zero or more times
    * shutdown will be called if this MultiLangDaemon instance loses the lease to this shard, or the shard ends due
        a scaling change.
    """

    def __init__(self, sqlalchemy_url: t.Optional[str], table_name: t.Optional[str]):
        self._SLEEP_SECONDS = 5
        self._CHECKPOINT_RETRIES = 5
        self._CHECKPOINT_FREQ_SECONDS = 60
        self._largest_seq: t.Tuple[IntOrNone, IntOrNone] = (None, None)
        self._largest_sub_seq = None
        self._last_checkpoint_time: FloatOrNone = None

        self.sqlalchemy_url = sqlalchemy_url
        self.table_name = table_name

        # Sanity checks.
        if self.sqlalchemy_url is None:
            raise ValueError("SQLAlchemy URL must not be empty")
        if self.table_name is None:
            raise ValueError("Target CDC table name must not be empty")

        self.cratedb = DatabaseAdapter(dburi=self.sqlalchemy_url)
        self.table_name = self.table_name
        self.cdc = DynamoCDCTranslatorCrateDB(table_name=self.table_name)

    def initialize(self, initialize_input):
        """
        Called once by a KCLProcess before any calls to process_records

        :param amazon_kclpy.messages.InitializeInput initialize_input: Information about the lease that this record
            processor has been assigned.
        """
        self._largest_seq = (None, None)
        self._last_checkpoint_time = time.time()

    def checkpoint(self, checkpointer, sequence_number=None, sub_sequence_number=None):
        """
        Checkpoints with retries on retryable exceptions.

        :param amazon_kclpy.kcl.Checkpointer checkpointer: the checkpointer provided to either process_records
            or shutdown
        :param str or None sequence_number: the sequence number to checkpoint at.
        :param int or None sub_sequence_number: the sub sequence number to checkpoint at.
        """
        for n in range(0, self._CHECKPOINT_RETRIES):
            try:
                checkpointer.checkpoint(sequence_number, sub_sequence_number)
                return
            except kcl.CheckpointError as e:
                if "ShutdownException" == e.value:
                    #
                    # A ShutdownException indicates that this record processor should be shutdown. This is due to
                    # some failover event, e.g. another MultiLangDaemon has taken the lease for this shard.
                    #
                    logging.error("Encountered shutdown exception, skipping checkpoint")
                    return
                elif "ThrottlingException" == e.value:
                    #
                    # A ThrottlingException indicates that one of our dependencies is is over burdened, e.g. too many
                    # dynamo writes. We will sleep temporarily to let it recover.
                    #
                    if self._CHECKPOINT_RETRIES - 1 == n:
                        logging.error("Failed to checkpoint after {n} attempts, giving up.\n".format(n=n))
                        return
                    else:
                        logging.info(
                            "Was throttled while checkpointing, will attempt again in {s} seconds".format(
                                s=self._SLEEP_SECONDS
                            )
                        )
                elif "InvalidStateException" == e.value:
                    logging.error("MultiLangDaemon reported an invalid state while checkpointing.\n")
                else:  # Some other error
                    logging.error("Encountered an error while checkpointing, error was {e}.\n".format(e=e))
            time.sleep(self._SLEEP_SECONDS)

    def process_record(self, data, partition_key, sequence_number, sub_sequence_number):
        """
        Convert record, which is a DynamoDB CDC event item, into an SQL statement,
        and submit to downstream database.

        :param str data: The blob of data that was contained in the record.
        :param str partition_key: The key associated with this recod.
        :param int sequence_number: The sequence number associated with this record.
        :param int sub_sequence_number: the sub sequence number associated with this record.
        """

        sql = None
        try:
            cdc_event = json.loads(data)
            logger.info("CDC event: %s", cdc_event)

            sql = self.cdc.to_sql(cdc_event)
            logger.info("SQL: %s", sql)
        except Exception:
            logger.exception("Decoding CDC event failed")

        if not sql:
            return

        try:
            self.cratedb.run_sql(sql)
        except Exception:
            logger.exception("Writing CDC event to sink database failed")

    def should_update_sequence(self, sequence_number, sub_sequence_number):
        """
        Determines whether a new larger sequence number is available

        :param int sequence_number: the sequence number from the current record
        :param int sub_sequence_number: the sub sequence number from the current record
        :return boolean: true if the largest sequence should be updated, false otherwise
        """
        return (
            self._largest_seq == (None, None)
            or sequence_number > self._largest_seq[0]
            or (sequence_number == self._largest_seq[0] and sub_sequence_number > self._largest_seq[1])
        )

    def process_records(self, process_records_input):
        """
        Called by a KCLProcess with a list of records to be processed and a checkpointer which accepts sequence numbers
        from the records to indicate where in the stream to checkpoint.

        :param amazon_kclpy.messages.ProcessRecordsInput process_records_input: the records, and metadata about the
            records.
        """
        try:
            for record in process_records_input.records:
                data = record.binary_data
                seq = int(record.sequence_number)
                sub_seq = record.sub_sequence_number
                key = record.partition_key
                self.process_record(data, key, seq, sub_seq)
                if self.should_update_sequence(seq, sub_seq):
                    self._largest_seq = (seq, sub_seq)

            #
            # Checkpoints every self._CHECKPOINT_FREQ_SECONDS seconds
            #
            if self._last_checkpoint_time and time.time() - self._last_checkpoint_time > self._CHECKPOINT_FREQ_SECONDS:
                self.checkpoint(process_records_input.checkpointer, str(self._largest_seq[0]), self._largest_seq[1])
                self._last_checkpoint_time = time.time()

        except Exception as e:
            logging.error("Encountered an exception while processing records. Exception was {e}\n".format(e=e))

    def lease_lost(self, lease_lost_input):
        logging.warn("Lease has been lost")

    def shard_ended(self, shard_ended_input):
        logging.warn("Shard has ended checkpointing")
        shard_ended_input.checkpointer.checkpoint()

    def shutdown_requested(self, shutdown_requested_input):
        logging.warn("Shutdown has been requested, checkpointing.")
        shutdown_requested_input.checkpointer.checkpoint()


def main():
    # Set up logging.
    logfile = os.environ.get("CDC_LOGFILE", "cdc.log")
    setup_logging(logfile)

    # Setup processor.
    sqlalchemy_url = os.environ.get("CDC_SQLALCHEMY_URL")
    table_name = os.environ.get("CDC_TABLE_NAME")
    kcl_processor = RecordProcessor(sqlalchemy_url=sqlalchemy_url, table_name=table_name)

    # Invoke machinery.
    kcl_process = kcl.KCLProcess(kcl_processor)
    kcl_process.run()


if __name__ == "__main__":
    main()