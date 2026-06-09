"""Integration tests for SNS fan-out to multiple SQS subscribers."""

import json

from aws_qa_learning.helpers.sqs import allow_sns_to_send_to_queue, get_queue_arn, receive_messages_from_queue


def test_sns_publish_fans_out_to_multiple_sqs_subscribers(sqs_client, sns_client, queue_factory, topic_factory) -> None:
    """Verify that publishing to an SNS topic delivers the message to all subscribed SQS queues."""
    queue_url_1 = queue_factory()
    queue_url_2 = queue_factory()

    topic_arn = topic_factory()

    queue_arn_1 = get_queue_arn(sqs_client, queue_url_1)
    queue_arn_2 = get_queue_arn(sqs_client, queue_url_2)

    allow_sns_to_send_to_queue(sqs_client, queue_url_1, queue_arn_1, topic_arn)
    allow_sns_to_send_to_queue(sqs_client, queue_url_2, queue_arn_2, topic_arn)

    sns_client.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn_1)
    sns_client.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn_2)

    subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)['Subscriptions']
    assert len(subscriptions) == 2
    assert all(sub['TopicArn'] == topic_arn for sub in subscriptions)

    message = 'Hello'
    message_id = sns_client.publish(TopicArn=topic_arn, Message=message)['MessageId']

    messages_1 = receive_messages_from_queue(sqs_client, queue_url_1)
    assert len(messages_1) == 1
    envelope_1 = json.loads(messages_1[0]['Body'])

    messages_2 = receive_messages_from_queue(sqs_client, queue_url_2)
    assert len(messages_2) == 1
    envelope_2 = json.loads(messages_2[0]['Body'])

    for envelope in (envelope_1, envelope_2):
        assert envelope['MessageId'] == message_id
        assert envelope['Message'] == message

    assert envelope_1['TopicArn'] == envelope_2['TopicArn']
