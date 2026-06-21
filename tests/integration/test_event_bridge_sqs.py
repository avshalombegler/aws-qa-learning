"""Integration test verifying EventBridge delivers events to an SQS queue target."""

import json

from aws_qa_learning.helpers.sqs import get_queue_arn, receive_messages_from_queue
from aws_qa_learning.utils import poll_until


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

    def _message_received():
        """Return the parsed body of the first SQS message once one arrives, else None."""
        received_messages = receive_messages_from_queue(sqs_client, queue_url)
        if received_messages:
            return json.loads(received_messages[0]['Body'])
        return None

    received_message_body = poll_until(_message_received)

    assert received_message_body['detail'] == item
