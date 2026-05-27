"""Tests for SQS queue operations: send, receive, message attributes, visibility, and FIFO ordering."""

from aws_qa_learning.helpers.sqs import receive_messages_from_queue, send_message_to_queue


def test_message_can_be_sent_and_received(sqs_client, queue_factory) -> None:
    """Verify that a message sent to a queue can be retrieved and its body matches the original."""
    queue_url = queue_factory()
    body = b"x"

    response = send_message_to_queue(sqs_client, queue_url, str(body))
    expected_message_id = response["MessageId"]

    messages = receive_messages_from_queue(sqs_client, queue_url)
    matching_messages = [msg for msg in messages if expected_message_id == msg["MessageId"]]

    assert str(body) == matching_messages[0]["Body"]


def test_message_attributes_are_preserved(sqs_client, queue_factory) -> None:
    """Verify that custom message attributes sent with a message are returned unchanged on receive."""
    queue_url = queue_factory()
    body = b"x"

    attributes = {
        "test_attr_1": {"DataType": "String", "StringValue": "OrderCreated"},
        "test_attr_2": {"DataType": "Number", "StringValue": "1337"},
    }

    response = send_message_to_queue(sqs_client, queue_url, str(body), attributes)
    expected_message_id = response["MessageId"]

    messages = receive_messages_from_queue(sqs_client, queue_url)
    matching_messages = [msg for msg in messages if expected_message_id == msg["MessageId"]]
    message_attributes = matching_messages[0]["MessageAttributes"]

    assert message_attributes["test_attr_1"]["StringValue"] == "OrderCreated"
    assert message_attributes["test_attr_1"]["DataType"] == "String"
    assert message_attributes["test_attr_2"]["StringValue"] == "1337"
    assert message_attributes["test_attr_2"]["DataType"] == "Number"


def test_received_message_is_invisible_to_subsequent_reads(
    sqs_client, queue_factory
) -> None:
    """Verify that a received message enters the visibility timeout and does not appear in the next poll."""
    queue_url = queue_factory()
    body = b"x"

    response = send_message_to_queue(sqs_client, queue_url, str(body))
    expected_message_id = response["MessageId"]

    messages = receive_messages_from_queue(sqs_client, queue_url)
    matching_messages = [msg for msg in messages if expected_message_id == msg["MessageId"]]
    assert len(matching_messages) == 1, f"Expected one matching message, got {len(matching_messages)}"

    messages = receive_messages_from_queue(sqs_client, queue_url)
    matching_messages = [msg for msg in messages if expected_message_id == msg["MessageId"]]
    assert len(matching_messages) == 0, f"Expected zero matching message, got {len(matching_messages)}"


def test_fifo_queue_preserves_message_order(sqs_client, queue_factory) -> None:
    """Verify that a FIFO queue delivers messages in the same order they were sent within a message group."""
    fifo_queue_url = queue_factory(is_fifo=True)
    bodies = [b"x", b"y", b"z"]
    msg_group_id = "test_group_id"

    send_message_to_queue(sqs_client, fifo_queue_url, str(bodies[0]), msg_group_id=msg_group_id)
    send_message_to_queue(sqs_client, fifo_queue_url, str(bodies[1]), msg_group_id=msg_group_id)
    send_message_to_queue(sqs_client, fifo_queue_url, str(bodies[2]), msg_group_id=msg_group_id)

    messages = receive_messages_from_queue(sqs_client, fifo_queue_url)
    assert len(messages) == 3
    for i, msg in enumerate(messages):
        assert msg["Body"] == str(bodies[i])
