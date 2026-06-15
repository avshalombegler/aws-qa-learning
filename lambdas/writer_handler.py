"""Lambda handler that"""

import os

import boto3


def handler(event, context):
    """"""
    # print(f'Received event: {event}')

    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    # print(f'AWS_ENDPOINT_URL: {endpoint_url}')

    dynamodb_client = boto3.client('dynamodb', endpoint_url=endpoint_url)
    response = dynamodb_client.put_item(
        TableName=event['table_name'],
        Item=event['item'],
    )
    # print(f'put_item HTTP status: {response["ResponseMetadata"]["HTTPStatusCode"]}')

    return {'put_status_code': response['ResponseMetadata']['HTTPStatusCode']}
