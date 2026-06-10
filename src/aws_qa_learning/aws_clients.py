"""Centralized AWS client creation for LocalStack interactions.

This module is the single source of truth for creating boto3 clients
pointed at LocalStack. Both scripts and pytest fixtures import from here.
"""

import os

import boto3

LOCALSTACK_ENDPOINT = 'http://localhost:4566'
TEST_REGION = 'us-east-1'


def setup_aws_credentials() -> None:
    """Set fake AWS credentials so boto3 doesn't complain.

    LocalStack accepts any credentials, but boto3 requires them to be set.
    Uses setdefault to avoid overriding real credentials if they exist.
    """
    os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test')
    os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test')
    os.environ.setdefault('AWS_DEFAULT_REGION', TEST_REGION)


def create_s3_client():
    """Create a boto3 S3 client pointed at LocalStack."""
    setup_aws_credentials()
    return boto3.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)


def create_sqs_client():
    """Create a boto3 SQS client pointed at LocalStack."""
    setup_aws_credentials()
    return boto3.client('sqs', endpoint_url=LOCALSTACK_ENDPOINT)


def create_sns_client():
    """Create a boto3 SNS client pointed at LocalStack."""
    setup_aws_credentials()
    return boto3.client('sns', endpoint_url=LOCALSTACK_ENDPOINT)


def create_dynamodb_client():
    """Create a boto3 DynamoDB client pointed at LocalStack."""
    setup_aws_credentials()
    return boto3.client('dynamodb', endpoint_url=LOCALSTACK_ENDPOINT)
