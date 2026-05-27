"""Helper functions for SQS operations used in tests and scripts."""

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
    max_messages: int = 10,
    wait_seconds: int = 5,
    visibility_timeout: int = 30,
) -> list[dict[str, Any]]:
    """Poll an SQS queue and return up to max_messages messages, using long polling by default."""
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MessageAttributeNames=["All"],
        MaxNumberOfMessages=max_messages,
        VisibilityTimeout=visibility_timeout,
        WaitTimeSeconds=wait_seconds,
    )
    return response.get("Messages", [])
