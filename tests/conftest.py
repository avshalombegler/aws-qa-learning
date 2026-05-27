"""Shared fixtures used across all AWS service test suites (S3, SQS, SNS)."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest

from aws_qa_learning.aws_clients import (
    create_s3_client,
    create_sns_client,
    create_sqs_client,
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
