"""
MinIO service — raw document upload/download.
"""
import io
from minio import Minio
from minio.error import S3Error
from app.config import settings

_client: Minio | None = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        # Ensure bucket exists
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
    return _client


def upload_document(object_name: str, file_bytes: bytes, content_type: str = "application/pdf") -> str:
    """Upload file bytes to MinIO. Returns the object path."""
    client = get_minio()
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return f"{settings.minio_bucket}/{object_name}"


def download_document(object_name: str) -> bytes:
    """Download file bytes from MinIO."""
    client = get_minio()
    response = client.get_object(settings.minio_bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    """Get a presigned download URL for a document."""
    from datetime import timedelta
    client = get_minio()
    return client.presigned_get_object(
        settings.minio_bucket,
        object_name,
        expires=timedelta(hours=expires_hours),
    )