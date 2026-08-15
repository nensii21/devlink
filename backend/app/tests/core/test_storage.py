from unittest.mock import MagicMock, patch
import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO

from app.core.storage import CloudStorageService
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(settings, "AWS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setattr(settings, "AWS_REGION", "us-east-1")
    monkeypatch.setattr(settings, "ALLOWED_IMAGE_TYPES", "image/png,image/jpeg")
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 5)


@pytest.fixture
def mock_upload_file():
    file = MagicMock(spec=UploadFile)
    file.filename = "test.png"
    file.content_type = "image/png"
    file.file = BytesIO(b"fake image content")
    file.size = 1000
    return file


@patch("boto3.client")
def test_storage_service_init_s3(mock_boto3, mock_settings):
    service = CloudStorageService()
    assert service.provider == "s3"
    assert service.bucket_name == "test-bucket"
    mock_boto3.assert_called_once_with(
        "s3",
        endpoint_url=None,
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        region_name="us-east-1",
    )


@patch("boto3.client")
def test_storage_service_upload_success(mock_boto3, mock_settings, mock_upload_file):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client

    service = CloudStorageService()
    result = service.upload_file(mock_upload_file, directory="avatars")

    assert result.startswith("avatars/")
    assert result.endswith(".png")
    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key=result,
        Body=b"fake image content",
        ContentType="image/png",
    )


@patch("boto3.client")
def test_storage_service_upload_invalid_type(
    mock_boto3, mock_settings, mock_upload_file
):
    mock_upload_file.content_type = "application/pdf"
    service = CloudStorageService()

    with pytest.raises(HTTPException) as exc:
        service.upload_file(mock_upload_file)

    assert exc.value.status_code == 400
    assert "not allowed" in exc.value.detail


@patch("boto3.client")
def test_storage_service_upload_invalid_size(
    mock_boto3, mock_settings, mock_upload_file
):
    mock_upload_file.size = 10 * 1024 * 1024  # 10MB, limit is 5MB
    service = CloudStorageService()

    with pytest.raises(HTTPException) as exc:
        service.upload_file(mock_upload_file)

    assert exc.value.status_code == 400
    assert "exceeds maximum limit" in exc.value.detail


@patch("boto3.client")
def test_storage_service_generate_presigned_url(mock_boto3, mock_settings):
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = (
        "https://s3.amazonaws.com/test-bucket/test.png?sig=123"
    )
    mock_boto3.return_value = mock_client

    service = CloudStorageService()
    url = service.generate_presigned_url("test.png")

    assert url == "https://s3.amazonaws.com/test-bucket/test.png?sig=123"
    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "test-bucket", "Key": "test.png"},
        ExpiresIn=3600,
    )


@patch("boto3.client")
def test_storage_service_delete_file(mock_boto3, mock_settings):
    mock_client = MagicMock()
    mock_boto3.return_value = mock_client

    service = CloudStorageService()
    result = service.delete_file("test.png")

    assert result is True
    mock_client.delete_object.assert_called_once_with(
        Bucket="test-bucket", Key="test.png"
    )
