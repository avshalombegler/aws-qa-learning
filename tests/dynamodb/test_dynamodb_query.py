"""Tests for DynamoDB query operations."""

from aws_qa_learning.helpers.dynamodb import put_item_to_db


def test_dynamodb_basic_query(dynamodb_client, table_factory) -> None:
    """Verify that querying by partition key returns all items sharing that key,
    sorted by sort key in descending order when ScanIndexForward is False."""
    table_name = table_factory()
    pk = {'PK': {'S': 'CUSTOMER#123'}}
    sk_1 = {'SK': {'S': 'PROFILE'}}
    sk_2 = {'SK': {'S': 'ORDER#001'}}
    item_1 = {
        **pk,
        **sk_1,
    }
    item_2 = {
        **pk,
        **sk_2,
    }

    put_item_to_db(dynamodb_client, table_name, item_1)

    put_item_to_db(dynamodb_client, table_name, item_2)

    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression='PK = :pk_val',
        ExpressionAttributeValues={':pk_val': pk['PK']},
        ScanIndexForward=False,
    )

    items = response['Items']
    assert len(items) == 2
    assert all(item['PK'] == pk['PK'] for item in items)

    returned_sks = [item['SK']['S'] for item in items]
    assert returned_sks == ['PROFILE', 'ORDER#001']
