"""Fixtures for SNS tests: topic factory for temporary standard and FIFO topics."""

import uuid
from collections.abc import Callable, Generator

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def topic_factory(sns_client) -> Generator[Callable[[bool], str], None, None]:
    """
    Factory fixture for creating temporary SNS topics.

    Yields a callable that creates a standard or FIFO SNS topic with a unique name.
    All created topics are deleted automatically after the test completes.
    """
    created_topics = []

    def _create_topic(is_fifo: bool = False) -> str:
        topic_name = f"my-topic-{uuid.uuid4()}.fifo" if is_fifo else f"my-topic-{uuid.uuid4()}"
        response = sns_client.create_topic(
            Name=topic_name,
            Attributes={"FifoTopic": "true", "ContentBasedDeduplication": "true"} if is_fifo else {},
        )
        topic_arn = response["TopicArn"]
        created_topics.append(topic_arn)

        return topic_arn

    yield _create_topic

    for topic in created_topics:
        try:
            sns_client.delete_topic(TopicArn=topic)
        except Exception as e:
            print(f"Failed to delete {topic}: {e}")
