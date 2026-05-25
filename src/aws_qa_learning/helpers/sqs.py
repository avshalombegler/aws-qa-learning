"""Helper functions for SQS operations used in tests and scripts."""

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
