"""Tests for DynamoDB global secondary index (GSI) queries."""

from aws_qa_learning.helpers.dynamodb import put_item_to_db
from aws_qa_learning.utils import poll_until


def test_gsi(dynamodb_client, table_factory) -> None:
    """Verify that querying a GSI returns only items matching the index's
    partition key, regardless of their table partition key."""
    gsi_name = 'email-index'
    gsi_pk = 'email'
    projection = {'ProjectionType': 'ALL'}
    sk_1 = {'SK': {'S': 'ORDER#001'}}
    sk_2 = {'SK': {'S': 'ORDER#002'}}
    sk_3 = {'SK': {'S': 'ORDER#003'}}
    email_a = 'a@test.com'
    email_b = 'b@test.com'
    item_1 = {'PK': {'S': 'CUSTOMER#123'}, **sk_1, 'email': {'S': email_a}}
    item_2 = {'PK': {'S': 'CUSTOMER#999'}, **sk_2, 'email': {'S': email_a}}
    item_3 = {'PK': {'S': 'CUSTOMER#123'}, **sk_3, 'email': {'S': email_b}}

    table_name = table_factory(gsi_name=gsi_name, gsi_pk=gsi_pk, projection=projection)

    put_item_to_db(dynamodb_client, table_name, item_1)
    put_item_to_db(dynamodb_client, table_name, item_2)
    put_item_to_db(dynamodb_client, table_name, item_3)

    # In real AWS, a GSI is eventually consistent: a query immediately after a write
    # may return stale/empty results until the index propagates. Production code must
    # poll with a timeout rather than query once (and never use a fixed sleep, which is
    # either too slow or flaky). LocalStack updates the GSI synchronously, so this loop
    # typically succeeds on the first attempt here.
    def _items_received():
        """Return the queried items once both expected items appear, else None."""
        response = dynamodb_client.query(
            TableName=table_name,
            IndexName=gsi_name,
            KeyConditionExpression='email = :email_val',
            ExpressionAttributeValues={':email_val': {'S': email_a}},
        )
        items = response['Items']
        if len(items) == 2:
            return items
        return None

    received_items = poll_until(_items_received)

    returned_pks = {item['PK']['S'] for item in received_items}
    assert returned_pks == {'CUSTOMER#123', 'CUSTOMER#999'}

    returned_emails = [item['email']['S'] for item in received_items]
    assert all(email == email_a for email in returned_emails)
