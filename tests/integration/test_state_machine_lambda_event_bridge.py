"""Integration tests for EventBridge triggering Step Functions state machines that invoke Lambda functions."""

import json

from aws_qa_learning.utils import poll_until


def test_event_bridge_triggers_state_machine_lambda_writer(
    dynamodb_client,
    lambda_client,
    event_bridge_client,
    table_factory,
    lambda_factory,
    state_machine_factory,
    event_bus_factory,
    rule_targets_factory,
) -> None:
    """Put an EventBridge event that triggers a state machine invoking a Lambda writer, then verify the stored item."""

    file_path = 'lambdas/writer_handler.py'
    handler = 'handler'
    item = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
        'name': {'S': 'Avshalom'},
    }

    table_name = table_factory()

    function_name = lambda_factory(file_path, handler)

    function_arn = lambda_client.get_function(FunctionName=function_name)['Configuration']['FunctionArn']

    definition = {
        'StartAt': 'FirstState',
        'States': {
            'FirstState': {'Type': 'Task', 'Resource': function_arn, 'InputPath': '$.detail', 'End': True},
        },
    }

    execution_input = {
        'table_name': table_name,
        'item': item,
    }

    state_machine_arn = state_machine_factory(definition)

    my_source = 'my.app'
    event_pattern = json.dumps({'source': ['my.app'], 'detail-type': ['Test']})

    event_bus_name = event_bus_factory()

    rule_targets_factory(event_bus_name, event_pattern, state_machine_arn)

    entries = [
        {
            'Source': my_source,
            'DetailType': 'Test',
            'Detail': json.dumps(execution_input),
            'EventBusName': event_bus_name,
        },
    ]

    event_bridge_client.put_events(Entries=entries)

    def _item_received():
        """Return the stored item once it exists in the table, else None."""
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={'PK': {'S': 'CUSTOMER#123'}, 'SK': {'S': 'PROFILE'}},
        )
        return response.get('Item')

    received_item = poll_until(_item_received)

    assert received_item == item
