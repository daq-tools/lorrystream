from pathlib import Path

from cottonformation.res import awslambda

from lorrystream.carabas.aws import LambdaFactory, LambdaPythonImage
from lorrystream.carabas.aws.model import GenericEnvStack


def test_python_dockerfile():
    python_image = LambdaPythonImage(
        name="kinesis-cratedb-lambda",
        entrypoint_file=Path("./lorrystream/process/kinesis_cratedb_lambda.py"),
        entrypoint_handler="kinesis_cratedb_lambda.handler",
    )
    dockerfile = python_image.get_dockerfile()
    assert "FROM public.ecr.aws/lambda/python:" in dockerfile
    assert "COPY kinesis_cratedb_lambda.py ${LAMBDA_TASK_ROOT}" in dockerfile


def test_lambda_python():
    python_image = LambdaPythonImage(
        name="kinesis-cratedb-lambda",
        entrypoint_file=Path("./lorrystream/process/kinesis_cratedb_lambda.py"),
        entrypoint_handler="kinesis_cratedb_lambda.handler",
    )
    lf = LambdaFactory(
        name="FoobarProcessor",
        oci_uri=python_image.uri,
        handler=python_image.entrypoint_handler,
    )
    assert "kinesis-cratedb-lambda:latest" in lf.oci_uri

    stack = GenericEnvStack(
        project="testdrive",
        stage="test",
        region="eu-central-1",
        description="Foobar Pipeline",
    )
    lambda_function = lf.make(stack)
    assert isinstance(lambda_function.function, awslambda.Function)
