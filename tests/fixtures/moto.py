import boto3
from moto import mock_aws
import pytest


@pytest.fixture
def dynamodb(aws_credentials):
    with mock_aws():
        yield boto3.resource("dynamodb")
@pytest.fixture
def dynamodb_client(aws_credentials):
    with mock_aws():
        yield boto3.client("dynamodb")


@pytest.fixture
def iam(aws_credentials):
    with mock_aws():
        yield boto3.client("iam")


@pytest.fixture
def sts(aws_credentials):
    with mock_aws():
        yield boto3.client("sts")
