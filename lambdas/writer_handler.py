"""Lambda handler that writes an item to a DynamoDB table."""

import os

import boto3


def handler(event, context):
    """
    Put an item into a DynamoDB table.

    Expects ``event['table_name']`` (the target table name) and
    ``event['item']`` (the item in DynamoDB's attribute-value format).
    Returns a dict with the ``put_item`` call's HTTP status code.
    """
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

    dynamodb_client = boto3.client('dynamodb', endpoint_url=endpoint_url)
    response = dynamodb_client.put_item(
        TableName=event['table_name'],
        Item=event['item'],
    )

    return {'put_status_code': response['ResponseMetadata']['HTTPStatusCode']}
