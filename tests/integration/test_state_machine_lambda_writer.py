"""Integration tests for Step Functions state machines invoking Lambda functions."""

import json
import time

import pytest


def test_state_machine_writes_item_to_dynamodb(
    step_functions_client, dynamodb_client, lambda_client, state_machine_factory, table_factory, lambda_factory
) -> None:
    """Run a state machine that invokes a Lambda writer, then verify the item lands in DynamoDB."""
    file_path = 'lambdas/writer_handler.py'
    handler = 'handler'
    item_name = 'Avshalom'
    item = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
        'name': {'S': item_name},
    }

    table_name = table_factory()

    function_name = lambda_factory(file_path, handler)

    function_arn = lambda_client.get_function(FunctionName=function_name)['Configuration']['FunctionArn']

    definition = {
        'StartAt': 'FirstState',
        'States': {
            'FirstState': {'Type': 'Task', 'Resource': function_arn, 'End': True},
        },
    }

    execution_input = {
        'table_name': table_name,
        'item': item,
    }

    state_machine_arn = state_machine_factory(definition)

    execution_arn = step_functions_client.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(execution_input),
    )['executionArn']

    timeout_seconds = 10
    poll_interval_seconds = 0.5
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        response = step_functions_client.describe_execution(executionArn=execution_arn)
        if response['status'] != 'RUNNING':
            break
        time.sleep(poll_interval_seconds)
    else:
        pytest.fail(f'Execution did not reach a terminal state within {timeout_seconds}s')

    assert response['status'] == 'SUCCEEDED'

    stored = dynamodb_client.get_item(
        TableName=table_name,
        Key={'PK': {'S': 'CUSTOMER#123'}, 'SK': {'S': 'PROFILE'}},
    )

    assert 'Item' in stored
    assert stored['Item'] == item
