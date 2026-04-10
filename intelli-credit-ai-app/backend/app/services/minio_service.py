"""
File storage — local disk for hackathon demo. No MinIO/S3 required.
Files saved to backend/local_uploads/
"""
from pathlib import Path

_STORE = Path(__file__).parent.parent.parent / "local_uploads"
_STORE.mkdir(parents=True, exist_ok=True)


def _path(object_name: str) -> Path:
    safe = object_name.replace("/", "_")
    return _STORE / safe


def upload_document(object_name: str, file_bytes: bytes, content_type: str = "application/pdf") -> str:
    _path(object_name).write_bytes(file_bytes)
    return f"local://{object_name}"


def download_document(object_name: str) -> bytes:
    p = _path(object_name)
    return p.read_bytes() if p.exists() else b""


def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    return f"local://{object_name}"
