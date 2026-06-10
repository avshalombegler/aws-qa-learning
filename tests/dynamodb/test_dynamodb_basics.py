"""Tests for basic DynamoDB operations: put, get, and round-trip data integrity."""


def test_put_get_round_trip(dynamodb_client, table_factory) -> None:
    """Verify that an item written via put_item can be retrieved intact via get_item."""
    table_name = table_factory()
    item_name = 'Avshalom'

    dynamodb_client.put_item(
        TableName=table_name,
        Item={
            'PK': {'S': 'CUSTOMER#123'},
            'SK': {'S': 'PROFILE'},
            'name': {'S': item_name},
        },
    )

    received_item = dynamodb_client.get_item(
        TableName=table_name,
        Key={
            'PK': {'S': 'CUSTOMER#123'},
            'SK': {'S': 'PROFILE'},
        },
    )

    assert 'Item' in received_item
    received_item_name = received_item['Item']['name']['S']
    assert received_item_name == item_name
