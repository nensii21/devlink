from __future__ import annotations

import io
from typing import Any, Final
from PIL import Image, ImageOps

from app.core.config import settings

# Allowed image formats for optimization
SUPPORTED_FORMATS: Final[set[str]] = {"JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF"}
DEFAULT_MAX_DIMENSIONS: Final[tuple[int, int]] = (1920, 1080)
DEFAULT_THUMB_DIMENSIONS: Final[tuple[int, int]] = (150, 150)
DEFAULT_QUALITY: Final[int] = 85


def _get_lanczos_resample():
    """Returns PIL LANCZOS resampling enum across PIL versions."""
    return getattr(getattr(Image, "Resampling", Image), "LANCZOS")


class ImageOptimizer:
    """
    Service for processing, resizing, compressing, stripping EXIF,
    and generating thumbnails for uploaded images.
    """

    @staticmethod
    def validate_image(
        contents: bytes, max_size_bytes: int | None = None
    ) -> Image.Image:
        """
        Validates raw bytes as a valid image and checks size bounds.
        Returns a PIL Image object.
        """
        if not contents:
            raise ValueError("Empty image data provided.")

        max_allowed = max_size_bytes or (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024)
        if len(contents) > max_allowed:
            raise ValueError(
                f"Image file size exceeds maximum limit of {max_allowed / (1024 * 1024):.1f}MB."
            )

        try:
            buf = io.BytesIO(contents)
            img = Image.open(buf)
            img.verify()
        except Exception as exc:
            raise ValueError("Invalid image file or corrupted data.") from exc

        # Reopen image because verify() invalidates the image instance state
        buf.seek(0)
        img = Image.open(buf)

        if img.format and img.format.upper() not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {img.format}")

        return img

    @staticmethod
    def strip_exif(image: Image.Image) -> Image.Image:
        """
        Strips EXIF metadata (geolocation, camera details) for user privacy.
        """
        # Create clean copy without info/EXIF metadata
        clean_img = Image.new(image.mode, image.size)
        get_data_fn = getattr(image, "get_flattened_data", image.getdata)
        clean_img.putdata(list(get_data_fn()))
        return clean_img

    @staticmethod
    def resize_image(
        image: Image.Image,
        max_width: int = DEFAULT_MAX_DIMENSIONS[0],
        max_height: int = DEFAULT_MAX_DIMENSIONS[1],
        preserve_aspect_ratio: bool = True,
    ) -> Image.Image:
        """
        Resizes an image down if its dimensions exceed (max_width, max_height)
        using high-quality LANCZOS resampling.
        """
        width, height = image.size
        if width <= max_width and height <= max_height:
            return image.copy()

        resample = _get_lanczos_resample()

        if preserve_aspect_ratio:
            ratio = min(max_width / width, max_height / height)
            new_width = max(1, int(width * ratio))
            new_height = max(1, int(height * ratio))
            return image.resize((new_width, new_height), resample=resample)
        else:
            return image.resize((max_width, max_height), resample=resample)

    @staticmethod
    def compress_image(
        image: Image.Image,
        quality: int = DEFAULT_QUALITY,
        output_format: str = "WEBP",
    ) -> bytes:
        """
        Compresses image and converts to the target format (default WebP).
        Returns raw image bytes.
        """
        fmt = output_format.upper()
        img = image

        # Ensure compatibility with output format mode
        if fmt in {"JPEG", "JPG"} and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif fmt == "WEBP" and img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")

        buffer = io.BytesIO()
        save_kwargs: dict[str, Any] = {"format": fmt, "optimize": True}

        if fmt in {"WEBP", "JPEG", "JPG"}:
            save_kwargs["quality"] = quality

        img.save(buffer, **save_kwargs)
        return buffer.getvalue()

    @staticmethod
    def generate_thumbnail(
        image: Image.Image,
        size: tuple[int, int] = DEFAULT_THUMB_DIMENSIONS,
        crop_to_fit: bool = False,
        quality: int = DEFAULT_QUALITY,
        output_format: str = "WEBP",
    ) -> bytes:
        """
        Generates a thumbnail variant of the image.
        """
        resample = _get_lanczos_resample()
        if crop_to_fit:
            thumb = ImageOps.fit(image, size, method=resample)
        else:
            thumb = image.copy()
            thumb.thumbnail(size, resample=resample)

        return ImageOptimizer.compress_image(
            thumb, quality=quality, output_format=output_format
        )

    @classmethod
    def process_image(
        cls,
        contents: bytes,
        max_dimensions: tuple[int, int] = DEFAULT_MAX_DIMENSIONS,
        thumb_dimensions: tuple[int, int] | None = DEFAULT_THUMB_DIMENSIONS,
        quality: int = DEFAULT_QUALITY,
        output_format: str = "WEBP",
        max_size_bytes: int | None = None,
    ) -> dict[str, Any]:
        """
        Executes the full image optimization pipeline:
        1. Validate image
        2. Strip EXIF
        3. Resize image
        4. Compress image
        5. Generate thumbnail (if requested)
        Returns metadata dictionary including raw byte buffers and dimensions.
        """
        original_size = len(contents)
        img = cls.validate_image(contents, max_size_bytes=max_size_bytes)
        original_fmt = img.format or "UNKNOWN"

        # Privacy EXIF strip
        clean_img = cls.strip_exif(img)

        # Resize oversized images
        resized_img = cls.resize_image(
            clean_img,
            max_width=max_dimensions[0],
            max_height=max_dimensions[1],
            preserve_aspect_ratio=True,
        )

        # Compress to WebP / target format
        optimized_bytes = cls.compress_image(
            resized_img, quality=quality, output_format=output_format
        )

        # Generate thumbnail
        thumb_bytes = None
        thumb_size = None
        if thumb_dimensions is not None:
            thumb_bytes = cls.generate_thumbnail(
                resized_img,
                size=thumb_dimensions,
                quality=quality,
                output_format=output_format,
            )

            # Get actual thumbnail dimensions
            thumb_buf = io.BytesIO(thumb_bytes)
            with Image.open(thumb_buf) as t_img:
                thumb_size = t_img.size

        return {
            "optimized_bytes": optimized_bytes,
            "thumbnail_bytes": thumb_bytes,
            "original_format": original_fmt,
            "format": output_format.upper(),
            "original_size": original_size,
            "optimized_size": len(optimized_bytes),
            "dimensions": resized_img.size,
            "thumbnail_dimensions": thumb_size,
        }
