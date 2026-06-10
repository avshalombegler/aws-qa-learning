"""Tests for DynamoDB put_item behavior with and without condition expressions."""

import pytest

from aws_qa_learning.helpers.dynamodb import get_item_from_db, put_item_to_db


def test_put_item_twice_without_condition_expression(dynamodb_client, table_factory) -> None:
    """Verify that a second put_item without a condition expression overwrites the existing item."""
    table_name = table_factory()
    item_name = 'Avshalom'
    item_age = '34'
    changed_name = 'Avsha'
    key = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
    }
    item = {
        **key,
        'name': {'S': item_name},
        'age': {'N': item_age},
    }
    changed_item = {
        **key,
        'name': {'S': changed_name},
    }

    put_item_to_db(dynamodb_client, table_name, item)

    put_item_to_db(dynamodb_client, table_name, changed_item)

    received_item = get_item_from_db(dynamodb_client, table_name, key)

    assert 'Item' in received_item
    assert 'age' not in received_item['Item']
    assert received_item['Item']['name']['S'] == changed_name


def test_put_item_twice_with_condition_expression(dynamodb_client, table_factory) -> None:
    """
    Verify that a second put_item with a condition expression raises ConditionalCheckFailedException
    and leaves the existing item unchanged.
    """
    table_name = table_factory()
    item_name = 'Avshalom'
    item_age = '34'
    changed_name = 'Avsha'
    key = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
    }
    item = {
        **key,
        'name': {'S': item_name},
        'age': {'N': item_age},
    }
    changed_item = {
        **key,
        'name': {'S': changed_name},
    }
    condition_expression = 'attribute_not_exists(PK)'

    put_item_to_db(dynamodb_client, table_name, item, condition_expression)

    with pytest.raises(dynamodb_client.exceptions.ConditionalCheckFailedException):
        put_item_to_db(dynamodb_client, table_name, changed_item, condition_expression)

    received_item = get_item_from_db(dynamodb_client, table_name, key)

    assert 'Item' in received_item
    assert received_item['Item']['name']['S'] == item_name
    assert received_item['Item']['age']['N'] == item_age
