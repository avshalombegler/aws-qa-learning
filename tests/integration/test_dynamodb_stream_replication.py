"""Integration test for a Lambda triggered by a DynamoDB Stream."""

import time


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
    stream_table_name = table_factory(stream_view_type='NEW_IMAGE')
    desc = dynamodb_client.describe_table(TableName=stream_table_name)
    stream_arn = desc['Table']['LatestStreamArn']
    target_table_name = table_factory()
    file_path = 'lambdas/stream_handler.py'
    handler = 'handler'
    environment = {'Variables': {'TARGET_TABLE': target_table_name}}
    item_name = 'Avshalom'
    item = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
        'name': {'S': item_name},
    }

    function_name = lambda_factory(file_path, handler, environment)

    event_source_mapping_factory(stream_arn, function_name, 'LATEST')

    dynamodb_client.put_item(
        TableName=stream_table_name,
        Item=item,
    )

    # The stream → Lambda flow is asynchronous: the write to table A triggers the
    # Lambda eventually, not immediately. Poll table B with a timeout until the item
    # appears (never a fixed sleep, which is too slow or flaky).
    timeout_seconds = 10
    poll_interval_seconds = 0.5
    deadline = time.monotonic() + timeout_seconds
    received = None

    while time.monotonic() < deadline:
        response = dynamodb_client.get_item(
            TableName=target_table_name,
            Key={'PK': {'S': 'CUSTOMER#123'}, 'SK': {'S': 'PROFILE'}},  # the key the Lambda writes to B
        )
        if 'Item' in response:  # success condition: the item appeared
            received = response
            break
        time.sleep(poll_interval_seconds)

    assert received is not None  # fail-fast if the timeout passed without the item
    assert received['Item'] == item  # then assert on the content
