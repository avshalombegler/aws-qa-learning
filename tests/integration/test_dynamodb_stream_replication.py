"""Integration test for a Lambda triggered by a DynamoDB Stream."""

from aws_qa_learning.utils import poll_until


def test_lambda_copies_item_from_stream_to_target_table(
    dynamodb_client, lambda_factory, table_factory, event_source_mapping_factory
) -> None:
    """
    Verify a stream-triggered Lambda replicates a new item to a target table.

    Writes an item to a table with streams enabled, which triggers a Lambda
    (subscribed via an event source mapping) that copies the new image to a
    second table. Polls the target table until the item appears and asserts
    its content matches what was written.
    """
    item_name = 'Avshalom'
    item = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
        'name': {'S': item_name},
    }
    file_path = 'lambdas/stream_handler.py'
    handler = 'handler'

    stream_table_name = table_factory(stream_view_type='NEW_IMAGE')
    desc = dynamodb_client.describe_table(TableName=stream_table_name)
    stream_arn = desc['Table']['LatestStreamArn']

    target_table_name = table_factory()
    environment = {'Variables': {'TARGET_TABLE': target_table_name}}
    function_name = lambda_factory(file_path, handler, environment)

    event_source_mapping_factory(stream_arn, function_name, 'LATEST')

    dynamodb_client.put_item(
        TableName=stream_table_name,
        Item=item,
    )

    def _item_received():
        """Return the replicated item once it exists in the target table, else None."""
        response = dynamodb_client.get_item(
            TableName=target_table_name,
            Key={'PK': {'S': 'CUSTOMER#123'}, 'SK': {'S': 'PROFILE'}},
        )
        return response.get('Item')

    received_item = poll_until(_item_received)

    assert received_item == item
