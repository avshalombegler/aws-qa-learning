"""Integration tests for SQS Dead Letter Queue (DLQ) behavior."""

import time

from aws_qa_learning.helpers.sqs import (
    get_approximate_number_of_messages,
    get_queue_arn,
    receive_messages_from_queue,
    send_message_to_queue,
)


def test_message_receive_in_dlq(sqs_client, queue_factory) -> None:
    """Verify that a message is moved to the DLQ after exceeding the max receive count."""
    dlq_url = queue_factory()
    dlq_arn = get_queue_arn(sqs_client, dlq_url)

    max_receive_count = 2
    queue_url = queue_factory(redrive_policy={"deadLetterTargetArn": dlq_arn, "maxReceiveCount": max_receive_count})

    message = "Hello"
    message_id = send_message_to_queue(sqs_client, queue_url, message)["MessageId"]

    for _ in range(max_receive_count + 1):
        receive_messages_from_queue(sqs_client, queue_url, visibility_timeout=1)
        time.sleep(1.5)

    received_messages = receive_messages_from_queue(sqs_client, queue_url)
    assert len(received_messages) == 0

    approximate_number_of_messages = get_approximate_number_of_messages(sqs_client, queue_url)
    assert approximate_number_of_messages == 0

    received_messages_from_dlq = receive_messages_from_queue(sqs_client, dlq_url)
    assert len(received_messages_from_dlq) == 1
    assert received_messages_from_dlq[0]["MessageId"] == message_id
    assert received_messages_from_dlq[0]["Body"] == message
    assert int(received_messages_from_dlq[0]["Attributes"]["ApproximateReceiveCount"]) == max_receive_count + 1
