"""Pytest fixtures providing factory functions for creating temporary AWS resources in tests."""

import json
import uuid
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

from aws_qa_learning.helpers.sqs import (
    delete_queue_if_exists,
)
from aws_qa_learning.utils import make_zip_bytes

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
    Global Secondary Index to the table. Pass ``stream_view_type`` (e.g.
    ``'NEW_AND_OLD_IMAGES'``) to enable a DynamoDB stream on the table.
    All tables created during the test are deleted during teardown.
    """
    created_tables = []

    def _create_table(
        gsi_name: str | None = None,
        gsi_pk: str | None = None,
        gsi_sk: str | None = None,
        projection: dict | None = None,
        stream_view_type: str | None = None,
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

        if stream_view_type is not None:
            kwargs['StreamSpecification'] = {'StreamEnabled': True, 'StreamViewType': stream_view_type}

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

    def _create_lambda(file_path: str, handler: str, environment: dict | None = None) -> str:
        path = Path(file_path)
        file_name = path.name
        function_name = f'{path.stem}-{uuid.uuid4()}'
        code = make_zip_bytes(file_path, file_name)
        kwargs = {
            'FunctionName': function_name,
            'Runtime': 'python3.12',
            'Role': 'arn:aws:iam::000000000000:role/lambda-role',
            'Handler': f'{path.stem}.{handler}',
            'Code': {'ZipFile': code},
        }

        if environment is not None:
            kwargs['Environment'] = environment

        lambda_client.create_function(**kwargs)

        created_functions.append(function_name)

        lambda_function_active_waiter = lambda_client.get_waiter('function_active_v2')
        lambda_function_active_waiter.wait(FunctionName=function_name)

        return function_name

    yield _create_lambda

    for function_name in created_functions:
        lambda_client.delete_function(FunctionName=function_name)


@pytest.fixture
def event_source_mapping_factory(lambda_client) -> Generator[Callable[..., str], Any, None]:
    """
    Yield a factory function that creates Lambda event source mappings.

    Call the factory with an event source ARN, the target Lambda function
    name, and a starting position (e.g. ``'LATEST'`` or ``'TRIM_HORIZON'``)
    to wire up the mapping. All mappings created through the factory are
    deleted automatically after the test completes.
    """
    created_mapping_uuids = []

    def _create_mapping(event_source_arn: str, function_name: str, starting_position: str) -> str:
        response = lambda_client.create_event_source_mapping(
            EventSourceArn=event_source_arn,
            FunctionName=function_name,
            StartingPosition=starting_position,
        )
        mapping_uuid = response['UUID']
        created_mapping_uuids.append(mapping_uuid)
        return mapping_uuid

    yield _create_mapping

    for mapping_uuid in created_mapping_uuids:
        lambda_client.delete_event_source_mapping(UUID=mapping_uuid)


@pytest.fixture
def state_machine_factory(step_functions_client) -> Generator[Callable[..., str], Any, None]:
    """
    Yield a factory function that creates temporary Step Functions state machines.

    Call the factory with an optional ``definition`` dict describing the
    state machine's Amazon States Language definition; omit it to create a
    state machine without a definition. All state machines created through
    the factory are deleted automatically after the test completes.
    """
    created_state_machine_arns = []

    def _create_state_machine(definition: dict | None = None) -> str:
        kwargs = {
            'name': f'my-state-machine-{uuid.uuid4()}',
            'roleArn': 'arn:aws:iam::000000000000:role/state-machine-role',
        }

        if definition is not None:
            kwargs['definition'] = json.dumps(definition)

        state_machine_arn = step_functions_client.create_state_machine(**kwargs)['stateMachineArn']

        created_state_machine_arns.append(state_machine_arn)

        return state_machine_arn

    yield _create_state_machine

    for state_machine_arn in created_state_machine_arns:
        step_functions_client.delete_state_machine(stateMachineArn=state_machine_arn)


@pytest.fixture
def event_bus_factory(event_bridge_client) -> Generator[Callable[..., str], Any, None]:
    """
    Yield a factory function that creates temporary EventBridge event buses.

    Call the factory with no arguments to create an event bus with a unique
    name. All event buses created through the factory are deleted
    automatically after the test completes.
    """
    created_event_bus_names = []

    def _create_event_bus() -> str:
        event_bus_name = f'my-event-bus-{uuid.uuid4()}'

        event_bridge_client.create_event_bus(
            Name=event_bus_name,
        )

        created_event_bus_names.append(event_bus_name)

        return event_bus_name

    yield _create_event_bus

    for event_bus_name in created_event_bus_names:
        event_bridge_client.delete_event_bus(Name=event_bus_name)


@pytest.fixture
def rule_targets_factory(event_bridge_client) -> Generator[Callable[..., None], Any, None]:
    """
    Yield a factory function that creates a temporary EventBridge rule with a target.

    Call the factory with an event bus name, an event pattern, and the ARN of
    the target (e.g. an SQS queue) to create a rule that routes matching
    events to that target. All rules and targets created through the factory
    are removed automatically after the test completes.
    """
    created_rule_targets = []

    def _put_rule_targets(event_bus_name: str, event_bus_pattern: str, target_arn: str) -> None:
        rule_name = f'my-rule-{uuid.uuid4()}'
        role_arn = 'arn:aws:iam::000000000000:role/rule-role'
        targets_id = f'my-target-id-{uuid.uuid4()}'
        created_rule_targets.append({'Rule': rule_name, 'EventBusName': event_bus_name, 'Targets': [targets_id]})

        rule_kwargs = {
            'Name': rule_name,
            'EventPattern': event_bus_pattern,
            'RoleArn': role_arn,
            'EventBusName': event_bus_name,
        }

        targets = [
            {'Arn': target_arn, 'Id': targets_id, 'RoleArn': role_arn},
        ]

        event_bridge_client.put_rule(**rule_kwargs)

        event_bridge_client.put_targets(
            Rule=rule_name,
            EventBusName=event_bus_name,
            Targets=targets,
        )

    yield _put_rule_targets

    for rule_targets in created_rule_targets:
        event_bridge_client.remove_targets(
            Rule=rule_targets['Rule'], EventBusName=rule_targets['EventBusName'], Ids=rule_targets['Targets']
        )
        event_bridge_client.delete_rule(
            Name=rule_targets['Rule'],
            EventBusName=rule_targets['EventBusName'],
        )
