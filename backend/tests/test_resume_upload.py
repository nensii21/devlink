import pytest

from app.utils.uploads import validate_resume_upload


def test_rejects_non_pdf_files():
    with pytest.raises(ValueError, match="PDF"):
        validate_resume_upload("resume.docx", "application/msword", 1024)


def test_rejects_oversized_files():
    with pytest.raises(ValueError, match="5MB"):
        validate_resume_upload("resume.pdf", "application/pdf", 6 * 1024 * 1024)


def test_accepts_valid_pdf():
    validate_resume_upload("resume.pdf", "application/pdf", 1024)
