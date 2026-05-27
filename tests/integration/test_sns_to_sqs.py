"""Integration tests for SNS-to-SQS message delivery."""

import json

from aws_qa_learning.helpers.sqs import get_queue_arn, receive_messages_from_queue


def test_sns_publish_delivers_to_sqs_subscriber(sqs_client, sns_client, queue_factory, topic_factory):
    """Verify that a message published to an SNS topic is delivered to a subscribed SQS queue."""
    queue_url = queue_factory()

    topic_arn = topic_factory()

    queue_arn = get_queue_arn(sqs_client, queue_url)

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

    sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="sqs",
        Endpoint=queue_arn,
    )

    response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
    assert len(response["Subscriptions"]) == 1

    subscription = response["Subscriptions"][0]
    assert subscription["TopicArn"] == topic_arn
    assert subscription["Endpoint"] == queue_arn
    assert subscription["Protocol"] == "sqs"

    message = "Hello SNS"
    sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
    )

    received_messages = receive_messages_from_queue(sqs_client, queue_url)
    assert len(received_messages) == 1

    sqs_message_body = received_messages[0]["Body"]

    envelope = json.loads(sqs_message_body)
    assert envelope["Message"] == message
    assert envelope["TopicArn"] == topic_arn
