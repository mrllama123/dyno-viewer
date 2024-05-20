import boto3
import moto
import pytest


@pytest.fixture
def dynamodb(aws_credentials):
    with moto.mock_dynamodb():
        yield boto3.resource("dynamodb")


@pytest.fixture
def iam(aws_credentials):
    with moto.mock_iam():
        yield boto3.client("iam")


@pytest.fixture
def sts(aws_credentials):
    with moto.mock_iam():
        yield boto3.client("sts")
