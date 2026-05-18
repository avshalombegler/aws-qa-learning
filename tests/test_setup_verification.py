"""Verification tests - prove the full setup works end-to-end."""
import pytest


def test_localstack_is_reachable(s3_client) -> None:
    """boto3 can talk to LocalStack at all."""
    response = s3_client.list_buckets()
    assert "Buckets" in response


def test_can_create_and_delete_bucket(s3_client) -> None:
    """Full lifecycle: create, verify, delete, verify gone."""
    bucket_name = "setup-verification-bucket"

    # Create
    s3_client.create_bucket(Bucket=bucket_name)

    # Verify it exists
    buckets = s3_client.list_buckets()["Buckets"]
    bucket_names = [b["Name"] for b in buckets]
    assert bucket_name in bucket_names

    # Cleanup
    s3_client.delete_bucket(Bucket=bucket_name)

    # Verify it's gone
    buckets = s3_client.list_buckets()["Buckets"]
    bucket_names = [b["Name"] for b in buckets]
    assert bucket_name not in bucket_names