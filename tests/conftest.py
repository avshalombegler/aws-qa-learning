"""Pytest configuration and shared fixtures for AWS QA learning project."""

import pytest

from aws_qa_learning.aws_clients import create_s3_client


@pytest.fixture(scope="session")
def s3_client():
    """boto3 S3 client pointed at LocalStack."""
    return create_s3_client()
