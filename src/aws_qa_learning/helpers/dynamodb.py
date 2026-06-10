"""Helper functions for DynamoDB operations used in tests and scripts."""

from typing import Any


def put_item_to_db(
    dynamodb_client: Any,
    table_name: str,
    item: dict,
    condition_expression: str | None = None,
) -> None:
    """Put an item into a DynamoDB table, optionally with a condition expression."""
    kwargs = {'TableName': table_name, 'Item': item}
    if condition_expression is not None:
        kwargs['ConditionExpression'] = condition_expression
    dynamodb_client.put_item(**kwargs)


def get_item_from_db(
    dynamodb_client: Any,
    table_name: str,
    key: dict,
) -> dict:
    """Get an item from a DynamoDB table by its key."""
    received_item = dynamodb_client.get_item(
        TableName=table_name,
        Key=key,
    )

    return received_item
