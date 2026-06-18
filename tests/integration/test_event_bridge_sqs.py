"""Integration test verifying EventBridge delivers events to an SQS queue target."""

import json
import time

import pytest

from aws_qa_learning.helpers.sqs import get_queue_arn, receive_messages_from_queue


def test_eventbridge_routes_event_to_sqs_queue(
    sqs_client, event_bus_factory, event_bridge_client, queue_factory, rule_targets_factory
) -> None:
    """Publish an event to EventBridge and assert it lands on the target SQS queue."""
    my_source = 'my.app'
    event_pattern = json.dumps({'source': ['my.app'], 'detail-type': ['Test']})
    item = {
        'id': 'CUSTOMER#123',
        'name': 'Avshalom',
    }
    queue_url = queue_factory()

    queue_arn = get_queue_arn(sqs_client, queue_url)

    event_bus_name = event_bus_factory()

    rule_targets_factory(event_bus_name, event_pattern, queue_arn)

    entries = [
        {
            'Source': my_source,
            'DetailType': 'Test',
            'Detail': json.dumps(item),
            'EventBusName': event_bus_name,
        },
    ]

    event_bridge_client.put_events(Entries=entries)

    timeout_seconds = 10
    poll_interval_seconds = 0.5
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        received_messages = receive_messages_from_queue(sqs_client, queue_url)
        if received_messages:
            break
        time.sleep(poll_interval_seconds)
    else:
        pytest.fail(f'Message was not received within {timeout_seconds}s')

    received_message_body = json.loads(received_messages[0]['Body'])
    assert received_message_body['detail'] == item
