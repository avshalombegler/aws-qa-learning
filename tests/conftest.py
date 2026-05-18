"""Pytest configuration and shared fixtures for AWS QA learning project."""
import os

import boto3
import pytest
from botocore.config import Config

# LocalStack endpoint - all AWS calls go here
LOCALSTACK_ENDPOINT = "http://localhost:4566"
TEST_REGION = "us-east-1"

# Set fake AWS credentials so boto3 doesn't complain.
# LocalStack accepts any credentials, but boto3 requires them to be set.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", TEST_REGION)


@pytest.fixture(scope="session")
def aws_config() -> Config:
    """Standard boto3 config for LocalStack interactions."""
    return Config(
        region_name=TEST_REGION,
        retries={"max_attempts": 3, "mode": "standard"},
    )


@pytest.fixture(scope="session")
def s3_client(aws_config: Config):
    """boto3 S3 client pointed at LocalStack."""
    return boto3.client(
        "s3",
        endpoint_url=LOCALSTACK_ENDPOINT,
        config=aws_config,
    )