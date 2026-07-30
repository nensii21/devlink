import io
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings
from app.utils.media import MediaStorageManager


@pytest.fixture(scope="function", autouse=True)
def temp_media_dir():
    # Override settings.MEDIA_UPLOAD_DIR to a temporary folder inside 'uploads'
    original_dir = settings.MEDIA_UPLOAD_DIR
    temp_dir = Path("uploads/media_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_UPLOAD_DIR = str(temp_dir)
    yield temp_dir
    # Restore original setting
    settings.MEDIA_UPLOAD_DIR = original_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def create_dummy_image(width=100, height=100, color="red", format="PNG") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_validate_image_valid():
    img_data = create_dummy_image()
    # Should not raise any exception
    MediaStorageManager.validate_image(img_data, "test.png", "image/png")
    MediaStorageManager.validate_image(img_data, "test.jpg", "image/jpeg")


def test_validate_image_invalid_extension():
    img_data = create_dummy_image()
    with pytest.raises(ValueError, match="Unsupported image type"):
        MediaStorageManager.validate_image(img_data, "test.txt", "text/plain")


def test_validate_image_too_large():
    img_data = create_dummy_image()
    original_max = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 0  # 0MB limit
    try:
        with pytest.raises(ValueError, match="File size exceeds maximum limit"):
            MediaStorageManager.validate_image(img_data, "test.png", "image/png")
    finally:
        settings.MAX_UPLOAD_SIZE_MB = original_max


def test_validate_image_corrupted():
    corrupted_data = b"not an image file content"
    with pytest.raises(ValueError, match="Invalid or corrupted image file"):
        MediaStorageManager.validate_image(corrupted_data, "test.png", "image/png")


def test_image_optimization():
    # Test that large image is resized
    large_img = create_dummy_image(width=2000, height=1000, color="blue", format="JPEG")
    optimized = MediaStorageManager.optimize_image(large_img)

    # Load optimized image and verify it is WebP and smaller
    with Image.open(io.BytesIO(optimized)) as img:
        assert img.format == "WEBP"
        assert img.width <= settings.MEDIA_MAX_DIMENSION
        assert img.height <= settings.MEDIA_MAX_DIMENSION


def test_thumbnail_generation():
    img_data = create_dummy_image(width=500, height=500)
    thumb = MediaStorageManager.generate_thumbnail(img_data)

    with Image.open(io.BytesIO(thumb)) as img:
        assert img.format == "WEBP"
        assert img.width <= settings.MEDIA_THUMB_DIMENSION
        assert img.height <= settings.MEDIA_THUMB_DIMENSION


def test_duplicate_detection_and_hashed_storage(temp_media_dir):
    img_data = create_dummy_image(color="green")

    # Save once
    res1 = MediaStorageManager.save_media(img_data, "test.png", "image/png")
    assert res1["reused"] is False

    h = res1["hash"]
    # Check if correct nested folders were created
    expected_main_path = temp_media_dir / h[0:2] / h[2:4] / f"{h}.webp"
    expected_thumb_path = temp_media_dir / h[0:2] / h[2:4] / f"{h}-thumb.webp"

    assert expected_main_path.exists()
    assert expected_thumb_path.exists()

    # Save again with same content
    res2 = MediaStorageManager.save_media(img_data, "different_name.jpg", "image/jpeg")
    assert res2["reused"] is True
    assert res2["hash"] == h
    assert res2["url"] == res1["url"]
    assert res2["thumbnail_url"] == res1["thumbnail_url"]


def test_upload_api_endpoint(client: TestClient, register_and_login):
    # Register and login to get auth token
    user_id, token = register_and_login("uploader@example.com", "uploader")
    headers = {"Authorization": f"Bearer {token}"}

    img_data = create_dummy_image(color="yellow")

    # Send request to router
    response = client.post(
        "/api/media/upload",
        headers=headers,
        files={"file": ("test_avatar.png", img_data, "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "hash" in data
    assert "url" in data
    assert "thumbnail_url" in data
    assert data["reused"] is False

    # We should be able to fetch the saved files back from FastAPI static files mounting
    # using client.get
    fetch_main = client.get(data["url"])
    assert fetch_main.status_code == 200
    assert fetch_main.headers["content-type"] in (
        "image/webp",
        "application/octet-stream",
    )

    fetch_thumb = client.get(data["thumbnail_url"])
    assert fetch_thumb.status_code == 200

    # Test upload without auth should fail
    response_no_auth = client.post(
        "/api/media/upload",
        files={"file": ("test_avatar.png", img_data, "image/png")},
    )
    assert response_no_auth.status_code == 401
