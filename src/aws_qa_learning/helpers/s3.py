"""Helper functions for S3 operations used in tests and scripts."""

from botocore.exceptions import ClientError


def enable_versioning(s3_client, bucket_name: str) -> None:
    """Enable versioning on the bucket."""
    s3_client.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={'Status': 'Enabled'},
    )


def empty_bucket(s3_client, bucket_name: str) -> None:
    """Delete all object versions in a versioned bucket."""
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name):
        versions = page.get('Versions', [])
        markers = page.get('DeleteMarkers', [])
        all_items = versions + markers
        if all_items:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': [{'Key': item['Key'], 'VersionId': item['VersionId']} for item in all_items]},
            )


def delete_bucket_if_exists(s3_client, bucket_name: str) -> None:
    """Empty and delete a bucket/versioned bucket, ignoring NoSuchBucket errors."""
    try:
        empty_bucket(s3_client, bucket_name)
        s3_client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchBucket':
            raise


def configure_s3_to_sqs_notification(s3_client, bucket_name, queue_arn, events: list[str]) -> None:
    """Configure an S3 bucket to send event notifications to an SQS queue."""
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'QueueConfigurations': [
                {
                    'QueueArn': queue_arn,
                    'Events': events,
                }
            ]
        },
    )
