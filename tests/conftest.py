"""Shared fixtures used across all AWS service test suites (S3, SQS, SNS)."""

import uuid
from collections.abc import Callable, Generator
from typing import Any

import pytest

from aws_qa_learning.aws_clients import (
    create_s3_client,
    create_sns_client,
    create_sqs_client,
)
from aws_qa_learning.helpers.s3 import (
    delete_bucket_if_exists,
    enable_versioning,
)
from aws_qa_learning.helpers.sqs import (
    delete_queue_if_exists,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def s3_client():
    """boto3 S3 client pointed at LocalStack."""
    return create_s3_client()


@pytest.fixture(scope="session")
def sqs_client():
    """boto3 SQS client pointed at LocalStack."""
    return create_sqs_client()


@pytest.fixture(scope="session")
def sns_client():
    """boto3 SNS client pointed at LocalStack."""
    return create_sns_client()


@pytest.fixture
def queue_factory(sqs_client) -> Generator[str, Any, None]:
    """
    Yield a factory function that creates temporary SQS queues for a test.

    Call the factory with ``is_fifo=True`` to create a FIFO queue (with
    content-based deduplication enabled); omit it for a standard queue.
    All queues created through the factory are deleted automatically after
    the test completes.
    """
    created_queues = []

    def _create_queue(is_fifo: bool = False) -> str:
        queue_name = f"my-queue-{uuid.uuid4()}.fifo" if is_fifo else f"my-queue-{uuid.uuid4()}"
        response = sqs_client.create_queue(
            QueueName=queue_name,
            Attributes={"FifoQueue": "true", "ContentBasedDeduplication": "true"} if is_fifo else {},
        )
        url = response["QueueUrl"]
        created_queues.append(url)
        return url

    yield _create_queue

    for queue in created_queues:
        delete_queue_if_exists(sqs_client, queue)


@pytest.fixture
def topic_factory(sns_client) -> Generator[Callable[[bool], str], None, None]:
    """
    Factory fixture for creating temporary SNS topics.

    Yields a callable that creates a standard or FIFO SNS topic with a unique name.
    All created topics are deleted automatically after the test completes.
    """
    created_topics = []

    def _create_topic(is_fifo: bool = False) -> str:
        topic_name = f"my-topic-{uuid.uuid4()}.fifo" if is_fifo else f"my-topic-{uuid.uuid4()}"
        response = sns_client.create_topic(
            Name=topic_name,
            Attributes={"FifoTopic": "true", "ContentBasedDeduplication": "true"} if is_fifo else {},
        )
        topic_arn = response["TopicArn"]
        created_topics.append(topic_arn)

        return topic_arn

    yield _create_topic

    for topic in created_topics:
        try:
            sns_client.delete_topic(TopicArn=topic)
        except Exception as e:
            print(f"Failed to delete {topic}: {e}")


@pytest.fixture
def temporary_bucket(s3_client) -> Generator[str, Any, None]:
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
