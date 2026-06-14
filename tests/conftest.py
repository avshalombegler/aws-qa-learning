"""Shared fixtures used across all AWS service test suites (S3, SQS, SNS)."""

import json
import uuid
from collections.abc import Callable, Generator
from typing import Any

import pytest

from aws_qa_learning.aws_clients import (
    create_dynamodb_client,
    create_lambda_client,
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
from aws_qa_learning.utils import make_zip_bytes

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope='session')
def s3_client():
    """boto3 S3 client pointed at LocalStack."""
    return create_s3_client()


@pytest.fixture(scope='session')
def sqs_client():
    """boto3 SQS client pointed at LocalStack."""
    return create_sqs_client()


@pytest.fixture(scope='session')
def sns_client():
    """boto3 SNS client pointed at LocalStack."""
    return create_sns_client()


@pytest.fixture(scope='session')
def dynamodb_client():
    """boto3 DynamoDB client pointed at LocalStack."""
    return create_dynamodb_client()


@pytest.fixture(scope='session')
def lambda_client():
    """boto3 Lambda client pointed at LocalStack."""
    return create_lambda_client()


@pytest.fixture
def queue_factory(sqs_client) -> Generator[str, Any, None]:
    """
    Yield a factory function that creates temporary SQS queues for a test.

    Call the factory with ``is_fifo=True`` to create a FIFO queue (with
    content-based deduplication enabled); omit it for a standard queue.
    Pass ``redrive_policy`` as a dict (e.g. ``{"deadLetterTargetArn": ...,
    "maxReceiveCount": N}``) to attach a DLQ redrive policy to the queue.
    All queues created through the factory are deleted automatically after
    the test completes.
    """
    created_queues = []

    def _create_queue(is_fifo: bool = False, redrive_policy: dict | None = None) -> str:
        attributes = {}
        if is_fifo:
            queue_name = f'my-queue-{uuid.uuid4()}.fifo'
            attributes.update({'FifoQueue': 'true', 'ContentBasedDeduplication': 'true'})
        else:
            queue_name = f'my-queue-{uuid.uuid4()}'

        if redrive_policy:
            attributes.update({'RedrivePolicy': json.dumps(redrive_policy)})

        response = sqs_client.create_queue(
            QueueName=queue_name,
            Attributes=attributes,
        )
        url = response['QueueUrl']
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
        topic_name = f'my-topic-{uuid.uuid4()}.fifo' if is_fifo else f'my-topic-{uuid.uuid4()}'
        response = sns_client.create_topic(
            Name=topic_name,
            Attributes={'FifoTopic': 'true', 'ContentBasedDeduplication': 'true'} if is_fifo else {},
        )
        topic_arn = response['TopicArn']
        created_topics.append(topic_arn)

        return topic_arn

    yield _create_topic

    for topic in created_topics:
        try:
            sns_client.delete_topic(TopicArn=topic)
        except Exception as e:
            print(f'Failed to delete {topic}: {e}')


@pytest.fixture
def table_factory(dynamodb_client) -> Generator[Callable[[], str], Any, None]:
    """
    Fixture that yields a callable for creating isolated DynamoDB tables with a PK/SK key schema.

    Each call creates a uniquely named table and waits until it is active.
    Optionally accepts gsi_name, gsi_pk, gsi_sk, and projection to add a
    Global Secondary Index to the table.
    All tables created during the test are deleted during teardown.
    """
    created_tables = []

    def _create_table(
        gsi_name: str | None = None,
        gsi_pk: str | None = None,
        gsi_sk: str | None = None,
        projection: dict | None = None,
    ) -> str:
        table_name = f'my-table-{uuid.uuid4()}'

        kwargs = {
            'TableName': table_name,
            'AttributeDefinitions': [
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
            ],
            'KeySchema': [
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'},
            ],
            'BillingMode': 'PAY_PER_REQUEST',
        }

        if gsi_pk is not None:
            gsi_key_schema = [{'AttributeName': gsi_pk, 'KeyType': 'HASH'}]
            if gsi_sk is not None:
                gsi_key_schema.append({'AttributeName': gsi_sk, 'KeyType': 'RANGE'})

            kwargs['GlobalSecondaryIndexes'] = [
                {
                    'IndexName': gsi_name,
                    'KeySchema': gsi_key_schema,
                    'Projection': projection,
                }
            ]

            kwargs['AttributeDefinitions'].append({'AttributeName': gsi_pk, 'AttributeType': 'S'})
            if gsi_sk is not None:
                kwargs['AttributeDefinitions'].append({'AttributeName': gsi_sk, 'AttributeType': 'S'})

        dynamodb_client.create_table(**kwargs)

        created_tables.append(table_name)

        dynamodb_table_exists_waiter = dynamodb_client.get_waiter('table_exists')
        dynamodb_table_exists_waiter.wait(TableName=table_name)

        return table_name

    yield _create_table

    for table in created_tables:
        dynamodb_client.delete_table(TableName=table)


@pytest.fixture
def lambda_factory(lambda_client) -> Generator[Callable[..., str], Any, None]:
    """
    Yield a factory function that deploys temporary Lambda functions from local source files.

    Call the factory with the path to a Python file and the name of its
    handler function (e.g. ``handler``); the file is zipped and uploaded as
    the function code. The factory waits until the function is active before
    returning its name. All functions created through the factory are
    deleted automatically after the test completes.
    """
    created_functions = []

    def _create_lambda(file_path: str, handler: str) -> str:
        function_name = f'my-lambda-{uuid.uuid4()}'
        file_name = file_path.split('/')[-1]
        code = make_zip_bytes(file_path, file_name)
        kwargs = {
            'FunctionName': function_name,
            'Runtime': 'python3.12',
            'Role': 'arn:aws:iam::000000000000:role/lambda-role',
            'Handler': f'{file_name.split(".")[0]}.{handler}',
            'Code': {'ZipFile': code},
        }

        lambda_client.create_function(**kwargs)

        created_functions.append(function_name)

        lambda_function_active_waiter = lambda_client.get_waiter('function_active_v2')
        lambda_function_active_waiter.wait(FunctionName=function_name)

        return function_name

    yield _create_lambda

    for function_name in created_functions:
        lambda_client.delete_function(FunctionName=function_name)


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
