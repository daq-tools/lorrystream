
.. code-block:: console

    lorry relay "amqp://guest:guest@localhost:5672/%2F?content-type=json"

    DATA='{"id": "device-42", "temperature": 42.42, "humidity": "84.84"}'
    echo "${DATA}" | amqp-publish --url='amqp://guest:guest@localhost:5672/%2F' \
        --exchange=message --routing-key=example.text

    lorry relay \
        "amqp://guest:guest@localhost:5672/%2F" \
        "sqlite:///data.sqlite/?table=testdrive"

    lorry relay \
        "amqp://guest:guest@localhost:5672/%2F" \
        "crate://localhost/?table=testdrive"

    echo "${DATA}" | \
        lorry publish "amqp://guest:guest@localhost:5672/%2F?exchange=foo&routing-key=bar"


    echo "${DATA}" | amqp-publish \
        --url='amqp://guest:guest@localhost:5672/%2F' \
        --exchange=message --routing-key=example.text


    echo 'hello' | amqp-publish \
        --url='amqp://guest:guest@localhost:5672/%2F' \
        --exchange=message --routing-key=example.text
