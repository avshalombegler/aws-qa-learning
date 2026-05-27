"""Basic tests for SNS topic operations."""


def test_basic_sns_interaction(sns_client, topic_factory) -> None:
    """Verify that a topic can be created, a message published, and topic attributes retrieved."""
    topic_arn = topic_factory()

    response = sns_client.publish(
        TopicArn=topic_arn,
        Message="Hello SNS",
    )
    assert response["MessageId"]

    topic_attributes = sns_client.get_topic_attributes(TopicArn=topic_arn)

    assert topic_attributes["Attributes"]["TopicArn"] == topic_arn
