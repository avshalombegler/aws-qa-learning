"""Shared utility helpers used across AWS service test suites."""

import io
import time
import zipfile

import pytest


def make_zip_bytes(source_path: str, arcname: str) -> bytes:
    """Zip the file at source_path in memory, storing it under arcname, and return the zip bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.write(source_path, arcname=arcname)  # arcname = name inside the zip
    return buffer.getvalue()


def poll_until(predicate, timeout_seconds=10, poll_interval_seconds=0.5):
    """
    Call predicate repeatedly until it returns a non-None value, then return that value.

    Fails the test via pytest.fail if no non-None value is produced within timeout_seconds.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result is not None:
            return result
        time.sleep(poll_interval_seconds)
    pytest.fail(f'Condition not met within {timeout_seconds}s')
