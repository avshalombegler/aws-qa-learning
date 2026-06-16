"""Shared fixtures used across all AWS service test suites (S3, SQS, SNS)."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest

from aws_qa_learning.aws_clients import (
    create_dynamodb_client,
    create_lambda_client,
    create_s3_client,
    create_sns_client,
    create_sqs_client,
    create_step_functions_client,
)
from aws_qa_learning.helpers.s3 import (
    delete_bucket_if_exists,
    enable_versioning,
)

pytest_plugins = ['factories']

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope='session')
def s3_client():
    """boto3 Simple Storage Service (S3) client pointed at LocalStack."""
    return create_s3_client()


@pytest.fixture(scope='session')
def sqs_client():
    """boto3 Simple Queue Service (SQS) client pointed at LocalStack."""
    return create_sqs_client()


@pytest.fixture(scope='session')
def sns_client():
    """boto3 Simple Notification Service (SNS) client pointed at LocalStack."""
    return create_sns_client()


@pytest.fixture(scope='session')
def dynamodb_client():
    """boto3 DynamoDB client pointed at LocalStack."""
    return create_dynamodb_client()


@pytest.fixture(scope='session')
def lambda_client():
    """boto3 Lambda client pointed at LocalStack."""
    return create_lambda_client()


@pytest.fixture(scope='session')
def step_functions_client():
    """boto3 Step Functions (SFN) client pointed at LocalStack."""
    return create_step_functions_client()


@pytest.fixture
def temporary_bucket(s3_client) -> Generator[str, Any, None]:
    """
    Create a unique bucket for the test, clean it up after.

    Each test gets a fresh bucket with a unique name (UUID-based),
    preventing collisions between parallel tests.
    """
    bucket_name = f'my-bucket-{uuid.uuid4()}'
    s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    delete_bucket_if_exists(s3_client, bucket_name)


@pytest.fixture
def versioned_bucket(s3_client, temporary_bucket):
    """
    Create a temporary_bucket with versioning enabled.
    """
    enable_versioning(s3_client, temporary_bucket)
    yield temporary_bucket
