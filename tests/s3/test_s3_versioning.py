"""Tests for S3 versioning behavior: multiple versions and delete markers."""

import pytest
from botocore.exceptions import ClientError


def test_put_object_twice_creates_two_versions(s3_client, versioned_bucket) -> None:
    """Uploading the same key twice in a versioned bucket creates two distinct versions with independent content."""
    key = 'versioning/test.txt'

    response_v1 = s3_client.put_object(Bucket=versioned_bucket, Key=key, Body=b'first')
    version_id_v1 = response_v1['VersionId']

    response_v2 = s3_client.put_object(Bucket=versioned_bucket, Key=key, Body=b'second')
    version_id_v2 = response_v2['VersionId']

    assert version_id_v1 != version_id_v2  # Different version IDs

    response = s3_client.get_object(Bucket=versioned_bucket, Key=key, VersionId=version_id_v1)
    assert response['Body'].read() == b'first'

    response = s3_client.get_object(Bucket=versioned_bucket, Key=key, VersionId=version_id_v2)
    assert response['Body'].read() == b'second'


def test_delete_in_versioned_bucket_creates_delete_marker(s3_client, versioned_bucket) -> None:
    """Deleting an object in a versioned bucket inserts a delete marker instead of removing the version."""
    key = 'versioning/test.txt'
    s3_client.put_object(Bucket=versioned_bucket, Key=key, Body=b'first')
    s3_client.delete_object(Bucket=versioned_bucket, Key=key)

    with pytest.raises(ClientError) as exc_info:
        s3_client.get_object(Bucket=versioned_bucket, Key=key)
    assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'

    response = s3_client.list_object_versions(Bucket=versioned_bucket, Prefix=key)
    assert len(response.get('Versions', [])) == 1

    markers = response.get('DeleteMarkers', [])
    assert len(markers) == 1
