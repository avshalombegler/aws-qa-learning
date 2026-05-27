"""Tests for S3 event notifications to SQS."""

import json

from aws_qa_learning.helpers.s3 import configure_s3_to_sqs_notification
from aws_qa_learning.helpers.sqs import get_queue_arn


def test_s3_put_triggers_sqs_notification(s3_client, sqs_client, temporary_bucket, queue_factory) -> None:
    """Verify that uploading an object to S3 triggers an SQS notification with correct metadata."""
    queue_url = queue_factory()
    queue_arn = get_queue_arn(sqs_client, queue_url)

    configure_s3_to_sqs_notification(s3_client, temporary_bucket, queue_arn, ["s3:ObjectCreated:*"])

    key = "notification/test.txt"
    body = b"x"
    s3_client.put_object(Bucket=temporary_bucket, Key=key, Body=body)

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=15,
    )

    messages = response.get("Messages", [])

    # Filtering LocalStack test notification
    s3_events = [msg for msg in messages if "Records" in json.loads(msg["Body"])]

    assert len(s3_events) == 1

    event_body = json.loads(s3_events[0]["Body"])
    record = event_body["Records"][0]
    assert record["s3"]["bucket"]["name"] == temporary_bucket
    assert record["s3"]["object"]["key"] == key
    assert record["eventName"] == "ObjectCreated:Put"
