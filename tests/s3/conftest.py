"""Fixtures for S3 tests: temporary buckets and versioned bucket setup."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest

from aws_qa_learning.helpers.s3 import (
    delete_bucket_if_exists,
    enable_versioning,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
