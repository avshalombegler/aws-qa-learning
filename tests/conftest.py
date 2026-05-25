"""Pytest configuration and shared fixtures for AWS QA learning project."""

import uuid

import pytest

from aws_qa_learning.aws_clients import (
    create_s3_client,
    create_sqs_client,
)
from aws_qa_learning.helpers.s3 import (
    delete_bucket_if_exists,
    enable_versioning,
)
from aws_qa_learning.helpers.sqs import (
    delete_queue_if_exists,
)


@pytest.fixture(scope="session")
def s3_client():
    """boto3 S3 client pointed at LocalStack."""
    return create_s3_client()


@pytest.fixture(scope="session")
def sqs_client():
    """boto3 SQS client pointed at LocalStack."""
    return create_sqs_client()


@pytest.fixture
def temporary_bucket(s3_client):
    """
    Create a unique bucket for the test, clean it up after.

    Each test gets a fresh bucket with a unique name (UUID-based),
    preventing collisions between parallel tests.
    """
    bucket_name = f"my-bucket-{uuid.uuid4()}"
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


@pytest.fixture
def temporary_queue(sqs_client):
    """
    Create a unique queue for the test, clean it up after.

    Each test gets a fresh queue with a unique name (UUID-based),
    preventing collisions between parallel tests.
    """
    queue_name = f"my-queue-{uuid.uuid4()}"
    response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = response["QueueUrl"]
    yield queue_url
    delete_queue_if_exists(sqs_client, queue_url)
