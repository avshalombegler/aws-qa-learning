"""Lambda handler that copies new items from a DynamoDB Stream onto a target table."""

import os

import boto3


def handler(event, context) -> None:
    """
    Write each new image from a DynamoDB Stream event to the target table.

    Reads the destination table name from the TARGET_TABLE environment
    variable and, for every record in the event, puts the record's
    NewImage into that table unchanged.
    """
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')

    target_table = os.environ.get('TARGET_TABLE')

    dynamodb_client = boto3.client('dynamodb', endpoint_url=endpoint_url)

    # put_item is idempotent: DynamoDB Streams delivers at-least-once and retries
    # failed batches, so the handler may run on the same record more than once.
    for record in event['Records']:
        new_image = record['dynamodb']['NewImage']
        dynamodb_client.put_item(TableName=target_table, Item=new_image,)
