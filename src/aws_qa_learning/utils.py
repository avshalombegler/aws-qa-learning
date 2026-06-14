"""Shared utility helpers used across AWS service test suites."""

import io
import zipfile


def make_zip_bytes(source_path: str, arcname: str) -> bytes:
    """Zip the file at source_path in memory, storing it under arcname, and return the zip bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        zf.write(source_path, arcname=arcname)  # arcname = name inside the zip
    return buffer.getvalue()
