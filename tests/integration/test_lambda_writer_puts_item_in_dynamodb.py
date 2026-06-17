"""Tests for the writer Lambda handler that writes items to DynamoDB."""

import json


def test_lambda_writer_puts_item_in_dynamodb(lambda_client, dynamodb_client, lambda_factory, table_factory) -> None:
    """Verify that invoking the writer Lambda puts the item into DynamoDB and returns a 200 status."""

    file_path = 'lambdas/writer_handler.py'
    handler = 'handler'
    item_name = 'Avshalom'
    item = {
        'PK': {'S': 'CUSTOMER#123'},
        'SK': {'S': 'PROFILE'},
        'name': {'S': item_name},
    }

    table_name = table_factory()

    payload = {
        'table_name': table_name,
        'item': item,
    }

    function_name = lambda_factory(file_path, handler)

    response = lambda_client.invoke(
        FunctionName=function_name,
        Payload=json.dumps(payload).encode(),
    )

    assert response['StatusCode'] == 200
    assert 'FunctionError' not in response

    received_payload = json.loads(response['Payload'].read())
    assert received_payload['put_status_code'] == 200

    received = dynamodb_client.get_item(
        TableName=table_name,
        Key={'PK': {'S': 'CUSTOMER#123'}, 'SK': {'S': 'PROFILE'}},
    )
    assert 'Item' in received
    assert received['Item']['name']['S'] == item_name
