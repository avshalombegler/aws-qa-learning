"""Helper functions for SQS operations used in tests and scripts."""

import json
from typing import Any

from botocore.exceptions import ClientError


def delete_queue_if_exists(sqs_client, queue_url: str) -> None:
    """Delete an SQS queue, ignoring the error if it does not exist."""
    try:
        sqs_client.delete_queue(QueueUrl=queue_url)
    except ClientError as e:
        if e.response["Error"]["Code"] != "AWS.SimpleQueueService.NonExistentQueue":
            raise


def get_queue_arn(sqs_client, queue_url: str) -> str:
    """Return the ARN of an SQS queue given its URL."""
    response = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])
    return response["Attributes"]["QueueArn"]


def send_message_to_queue(
    sqs_client: Any,
    queue_url: str,
    body: str,
    attributes: dict | None = None,
    msg_group_id: str | None = None,
) -> dict:
    """Send a message to an SQS queue, optionally with message attributes and a group ID for FIFO queues."""
    kwargs = {"QueueUrl": queue_url, "MessageBody": body}
    if attributes is not None:
        kwargs["MessageAttributes"] = attributes
    if msg_group_id is not None:
        kwargs["MessageGroupId"] = msg_group_id
    return sqs_client.send_message(**kwargs)


def receive_messages_from_queue(
    sqs_client: Any,
    queue_url: str,
    attribute_names: list | None = None,
    message_attribute_names: list | None = None,
    max_messages: int = 10,
    wait_seconds: int = 5,
    visibility_timeout: int = 20,
) -> list[dict[str, Any]]:
    """Poll an SQS queue and return up to max_messages messages, using long polling by default."""
    if attribute_names is None:
        attribute_names = ["All"]

    if message_attribute_names is None:
        message_attribute_names = ["All"]

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        AttributeNames=attribute_names,
        MessageAttributeNames=message_attribute_names,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_seconds,
        VisibilityTimeout=visibility_timeout,
    )
    return response.get("Messages", [])


def allow_sns_to_send_to_queue(sqs_client, queue_url, queue_arn, topic_arn) -> None:
    """Allow the given SNS topic to send messages to the given SQS queue."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sns.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": queue_arn,
                "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
            }
        ],
    }

    sqs_client.set_queue_attributes(QueueUrl=queue_url, Attributes={"Policy": json.dumps(policy)})
