"""Tests for S3 basic operations - mirrors the s3_basics.py script."""


def test_can_upload_objects(s3_client, temporary_bucket) -> None:
    """Verify put_object works."""
    s3_client.put_object(
        Bucket=temporary_bucket,
        Key='greetings/hello.txt',
        Body=b'Hello, World!',
        ContentType='text/plain',
    )

    response = s3_client.list_objects_v2(Bucket=temporary_bucket)
    keys = [obj['Key'] for obj in response.get('Contents', [])]
    assert 'greetings/hello.txt' in keys


def test_can_download_object_content(s3_client, temporary_bucket) -> None:
    """Verify get_object returns the same content we uploaded."""
    key = 'greetings/hello.txt'
    expected_content = b'Hello, World!'

    s3_client.put_object(Bucket=temporary_bucket, Key=key, Body=expected_content)

    response = s3_client.get_object(Bucket=temporary_bucket, Key=key)
    actual_content = response['Body'].read()

    assert actual_content == expected_content


def test_content_type_metadata_is_preserved(s3_client, temporary_bucket) -> None:
    """Verify ContentType is stored and returned."""
    s3_client.put_object(
        Bucket=temporary_bucket,
        Key='image.jpg',
        Body=b'fake-image-bytes',
        ContentType='image/jpeg',
    )

    response = s3_client.get_object(Bucket=temporary_bucket, Key='image.jpg')
    assert response['ContentType'] == 'image/jpeg'


def test_listing_with_prefix_filters_results(s3_client, temporary_bucket) -> None:
    """Verify Prefix parameter filters list_objects_v2 results."""
    s3_client.put_object(Bucket=temporary_bucket, Key='greetings/hello.txt', Body=b'x')
    s3_client.put_object(Bucket=temporary_bucket, Key='greetings/bye.txt', Body=b'x')
    s3_client.put_object(Bucket=temporary_bucket, Key='other/data.txt', Body=b'x')

    response = s3_client.list_objects_v2(Bucket=temporary_bucket, Prefix='greetings/')
    keys = [obj['Key'] for obj in response.get('Contents', [])]

    assert len(keys) == 2
    assert all(key.startswith('greetings/') for key in keys)


def test_delete_removes_object(s3_client, temporary_bucket) -> None:
    """Verify delete_object removes the object."""
    key = 'to-delete.txt'
    s3_client.put_object(Bucket=temporary_bucket, Key=key, Body=b'goodbye')

    s3_client.delete_object(Bucket=temporary_bucket, Key=key)

    response = s3_client.list_objects_v2(Bucket=temporary_bucket)
    keys = [obj['Key'] for obj in response.get('Contents', [])]
    assert key not in keys
