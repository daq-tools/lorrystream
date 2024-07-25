#!/bin/sh

# Configure record processor.
export CDC_SQLALCHEMY_URL=crate://
export CDC_TABLE_NAME=transactions
export CDC_LOGFILE=dynamodb_cdc_processor.log

# Invoke KCL launcher.
KCLPY_PATH=$(python -c 'import amazon_kclpy; print(amazon_kclpy.__path__[0])')
/usr/bin/java \
  -DstreamName=dynamodb-cdc-nested \
  -cp "${KCLPY_PATH}/jars/*" \
  software.amazon.kinesis.multilang.MultiLangDaemon \
  --properties-file "$1" \
  --log-configuration logback.xml
