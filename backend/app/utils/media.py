from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from PIL import Image, ImageOps

from app.core.config import settings


class MediaStorageManager:
    """
    Manager for optimizing, thumbnailing, hashing, and storing uploaded media files.
    """

    @staticmethod
    def validate_image(file_contents: bytes, filename: str, content_type: str) -> None:
        """
        Validate that the uploaded file is within size limits and is a supported image type.
        """
        # Validate file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_contents) > max_bytes:
            raise ValueError(
                f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Validate file extension and mimetype
        ext = os.path.splitext(filename.lower())[1]
        allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        allowed_mimetypes = set(settings.allowed_image_types)

        is_allowed_mime = content_type and content_type.lower() in allowed_mimetypes
        is_allowed_ext = ext in allowed_extensions

        if not (is_allowed_mime or is_allowed_ext):
            raise ValueError(
                f"Unsupported image type. Allowed types: {settings.ALLOWED_IMAGE_TYPES}"
            )

        # Validate image integrity using Pillow
        try:
            with Image.open(io.BytesIO(file_contents)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError("Invalid or corrupted image file.") from exc

    @staticmethod
    def get_content_hash(file_contents: bytes) -> str:
        """
        Generate SHA-256 hash of image contents for duplicate detection.
        """
        return hashlib.sha256(file_contents).hexdigest()

    @staticmethod
    def optimize_image(image_bytes: bytes) -> bytes:
        """
        Process the image:
        - Auto-orient based on EXIF data.
        - Resize if dimensions exceed configured maximum while preserving aspect ratio.
        - Convert to optimized WebP.
        """
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Handle color profiles/transparency
            if img.mode in ("RGBA", "LA", "P"):
                # WebP supports alpha channel, so we can keep it
                pass
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Correct orientation if EXIF tags exist
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # Resize if larger than maximum dimension
            max_dim = settings.MEDIA_MAX_DIMENSION
            if img.width > max_dim or img.height > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            # Compress and export as WebP
            out_io = io.BytesIO()
            img.save(out_io, format="WEBP", quality=settings.MEDIA_QUALITY)
            return out_io.getvalue()

    @staticmethod
    def generate_thumbnail(image_bytes: bytes) -> bytes:
        """
        Generate a smaller thumbnail version of the image in WebP format.
        """
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.mode in ("RGBA", "LA", "P"):
                pass
            elif img.mode != "RGB":
                img = img.convert("RGB")

            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # Resize to thumbnail dimensions
            thumb_dim = settings.MEDIA_THUMB_DIMENSION
            img.thumbnail((thumb_dim, thumb_dim), Image.Resampling.LANCZOS)

            # Compress and export as WebP
            out_io = io.BytesIO()
            img.save(out_io, format="WEBP", quality=settings.MEDIA_QUALITY)
            return out_io.getvalue()

    @staticmethod
    def format_url(relative_path: str) -> str:
        """
        Prepend CDN base URL if configured.
        """
        if settings.CDN_BASE_URL:
            base = settings.CDN_BASE_URL.rstrip("/")
            path = relative_path.lstrip("/")
            return f"{base}/{path}"
        return relative_path

    @staticmethod
    def save_media(file_contents: bytes, filename: str, content_type: str) -> dict:
        """
        Validates, optimizes, hashes and stores an uploaded image.
        Returns a dict containing:
        - hash: SHA-256 hash of original file
        - url: URL of the optimized WebP image
        - thumbnail_url: URL of the thumbnail WebP image
        - reused: Boolean indicating if an existing duplicate file was used
        """
        # Validate input
        MediaStorageManager.validate_image(file_contents, filename, content_type)

        # Get content hash
        hash_str = MediaStorageManager.get_content_hash(file_contents)

        # Organize into nested directory: uploads/media/ab/cd/hash.webp
        h_prefix1 = hash_str[0:2]
        h_prefix2 = hash_str[2:4]

        media_dir = Path(settings.MEDIA_UPLOAD_DIR)
        dir_path = media_dir / h_prefix1 / h_prefix2

        filename_main = f"{hash_str}.webp"
        filename_thumb = f"{hash_str}-thumb.webp"

        path_main = dir_path / filename_main
        path_thumb = dir_path / filename_thumb

        # Build relative URLs dynamically based on settings.MEDIA_UPLOAD_DIR
        parts = media_dir.parts
        subpath = "/".join(parts[1:]) if len(parts) > 1 else ""
        url_prefix = f"/uploads/{subpath}".rstrip("/")

        relative_url_main = f"{url_prefix}/{h_prefix1}/{h_prefix2}/{filename_main}"
        relative_url_thumb = f"{url_prefix}/{h_prefix1}/{h_prefix2}/{filename_thumb}"

        # Duplicate detection: If file exists, skip writing
        if path_main.exists() and path_thumb.exists():
            return {
                "hash": hash_str,
                "url": MediaStorageManager.format_url(relative_url_main),
                "thumbnail_url": MediaStorageManager.format_url(relative_url_thumb),
                "reused": True,
            }

        # Perform optimization and thumbnail generation
        optimized_bytes = MediaStorageManager.optimize_image(file_contents)
        thumb_bytes = MediaStorageManager.generate_thumbnail(file_contents)

        # Write files
        dir_path.mkdir(parents=True, exist_ok=True)
        path_main.write_bytes(optimized_bytes)
        path_thumb.write_bytes(thumb_bytes)

        return {
            "hash": hash_str,
            "url": MediaStorageManager.format_url(relative_url_main),
            "thumbnail_url": MediaStorageManager.format_url(relative_url_thumb),
            "reused": False,
        }
