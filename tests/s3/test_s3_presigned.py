"""Tests for S3 presigned URL functionality — verifying that temporary URLs grant access without AWS credentials."""

import requests


def test_presigned_get_url_allows_download_without_credentials(s3_client, temporary_bucket) -> None:
    """Verify that a presigned GET URL returns the object's content without AWS credentials."""
    key = 'presigned/file.txt'
    body = b'test_get'
    s3_client.put_object(Bucket=temporary_bucket, Key=key, Body=body)
    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': temporary_bucket, 'Key': key},
        ExpiresIn=3600,
    )

    response = requests.get(url)
    assert response.status_code == 200
    assert response.content == body


def test_presigned_put_url_allows_upload_without_credentials(s3_client, temporary_bucket) -> None:
    """
    Verify that a presigned PUT URL allows uploading an object without AWS credentials,
    and that the content is stored correctly.
    """
    key = 'presigned/file.txt'
    body = b'new content'
    url = s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={'Bucket': temporary_bucket, 'Key': key},
        ExpiresIn=3600,
    )

    put_response = requests.put(url, data=body)
    assert put_response.ok

    s3_response = s3_client.get_object(Bucket=temporary_bucket, Key=key)
    assert s3_response['Body'].read() == body
