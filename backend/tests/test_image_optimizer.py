import io
import pytest
from PIL import Image

from app.services.image_optimizer import ImageOptimizer
from app.utils.uploads import validate_image_upload, save_image_upload


def create_sample_image_bytes(
    width: int = 100,
    height: int = 100,
    fmt: str = "PNG",
    color: str = "red",
    mode: str = "RGB",
) -> bytes:
    """Helper to generate in-memory image bytes for testing."""
    img = Image.new(mode, (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ==========================================================
# Image Validation Tests
# ==========================================================


def test_validate_image_rejects_empty_data():
    with pytest.raises(ValueError, match="Empty image data"):
        ImageOptimizer.validate_image(b"")


def test_validate_image_rejects_corrupted_bytes():
    with pytest.raises(ValueError, match="Invalid image file"):
        ImageOptimizer.validate_image(b"this is not an image content")


def test_validate_image_rejects_oversized_bytes():
    raw_data = create_sample_image_bytes(50, 50)
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        ImageOptimizer.validate_image(raw_data, max_size_bytes=10)


def test_validate_image_accepts_valid_image():
    raw_data = create_sample_image_bytes(200, 200, fmt="JPEG")
    img = ImageOptimizer.validate_image(raw_data)
    assert isinstance(img, Image.Image)
    assert img.size == (200, 200)


# ==========================================================
# EXIF Stripping Tests
# ==========================================================


def test_strip_exif():
    img = Image.new("RGB", (50, 50), color="green")
    cleaned = ImageOptimizer.strip_exif(img)
    assert cleaned.size == (50, 50)
    assert "exif" not in cleaned.info


# ==========================================================
# Resizing Tests
# ==========================================================


def test_resize_image_downscales_oversized():
    large_img = Image.new("RGB", (3000, 2000), color="blue")
    resized = ImageOptimizer.resize_image(large_img, max_width=1920, max_height=1080)
    assert resized.width <= 1920
    assert resized.height <= 1080
    # Aspect ratio check: 3000/2000 = 1.5 -> 1620/1080 = 1.5
    assert resized.size == (1620, 1080)


def test_resize_image_preserves_smaller_dimensions():
    small_img = Image.new("RGB", (500, 300), color="yellow")
    resized = ImageOptimizer.resize_image(small_img, max_width=1920, max_height=1080)
    assert resized.size == (500, 300)


# ==========================================================
# Compression & WebP Conversion Tests
# ==========================================================


def test_compress_image_converts_to_webp():
    raw_png = create_sample_image_bytes(300, 300, fmt="PNG")
    img = Image.open(io.BytesIO(raw_png))

    webp_bytes = ImageOptimizer.compress_image(img, quality=80, output_format="WEBP")
    assert len(webp_bytes) > 0

    with Image.open(io.BytesIO(webp_bytes)) as webp_img:
        assert webp_img.format == "WEBP"


# ==========================================================
# Thumbnail Generation Tests
# ==========================================================


def test_generate_thumbnail():
    img = Image.new("RGB", (800, 600), color="purple")
    thumb_bytes = ImageOptimizer.generate_thumbnail(
        img, size=(150, 150), output_format="WEBP"
    )

    with Image.open(io.BytesIO(thumb_bytes)) as thumb_img:
        assert thumb_img.format == "WEBP"
        assert thumb_img.width <= 150
        assert thumb_img.height <= 150


# ==========================================================
# End-to-End Pipeline Tests
# ==========================================================


def test_process_image_pipeline():
    raw_png = create_sample_image_bytes(2500, 1500, fmt="PNG", color="orange")
    result = ImageOptimizer.process_image(
        raw_png,
        max_dimensions=(1000, 1000),
        thumb_dimensions=(150, 150),
        quality=80,
        output_format="WEBP",
    )

    assert result["format"] == "WEBP"
    assert result["original_size"] == len(raw_png)
    assert result["optimized_size"] > 0
    assert result["dimensions"][0] <= 1000
    assert result["dimensions"][1] <= 1000
    assert result["thumbnail_bytes"] is not None
    assert result["thumbnail_dimensions"][0] <= 150
    assert result["thumbnail_dimensions"][1] <= 150


# ==========================================================
# Upload Validator and Saver Tests
# ==========================================================


def test_validate_image_upload_rules():
    # Unsupported extension
    with pytest.raises(ValueError, match="Unsupported file extension"):
        validate_image_upload("file.pdf", "image/png", 100)

    # Invalid MIME type
    with pytest.raises(ValueError, match="Please upload a valid image file"):
        validate_image_upload("file.png", "application/octet-stream", 100)

    # Oversized file
    with pytest.raises(ValueError, match="must be smaller than"):
        validate_image_upload("file.png", "image/png", 50 * 1024 * 1024)

    # Valid image upload
    validate_image_upload("avatar.jpg", "image/jpeg", 500 * 1024)


def test_save_image_upload(tmp_path, monkeypatch):
    import app.core.config

    monkeypatch.setattr(app.core.config.settings, "UPLOAD_DIR", str(tmp_path))

    raw_data = create_sample_image_bytes(500, 500, fmt="JPEG")
    result = save_image_upload(
        contents=raw_data,
        filename="test_avatar.jpg",
        subfolder="avatars",
        user_id="testuser123",
    )

    assert result["image_url"].startswith("/uploads/avatars/")
    assert result["image_url"].endswith(".webp")
    assert result["thumbnail_url"].endswith("_thumb.webp")

    # Check generated files on disk
    saved_img_path = tmp_path / "avatars" / result["image_url"].split("/")[-1]
    saved_thumb_path = tmp_path / "avatars" / result["thumbnail_url"].split("/")[-1]

    assert saved_img_path.exists()
    assert saved_thumb_path.exists()

    with Image.open(saved_img_path) as img:
        assert img.format == "WEBP"
