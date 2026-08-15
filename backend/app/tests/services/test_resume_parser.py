from unittest.mock import MagicMock, patch

from app.schemas.user import ResumeParseResponse
from app.services.resume_parser_service import ResumeParserService


@patch("app.services.resume_parser_service.settings")
@patch("app.services.resume_parser_service.ResumeParserService._extract_text_from_pdf")
def test_parse_resume_pdf(mock_extract, mock_settings):
    # Setup mocks
    mock_settings.OPENAI_API_KEY = "fake-key"
    mock_extract.return_value = "Sample PDF Text with skills like Python and React"

    # Mock OpenAI client
    mock_openai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"skills": ["Python", "React"], "technologies": ["Django"], "experience": [], "education": [], "certifications": []}'
            )
        )
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_openai_client):
        # Call the method
        result = ResumeParserService.parse_resume(b"dummy_bytes", "resume.pdf")

        # Assertions
        assert isinstance(result, ResumeParseResponse)
        assert "Python" in result.skills
        assert "React" in result.skills
        assert "Django" in result.technologies
        assert len(result.experience) == 0


@patch("app.services.resume_parser_service.settings")
@patch("app.services.resume_parser_service.ResumeParserService._extract_text_from_docx")
def test_parse_resume_docx(mock_extract, mock_settings):
    # Setup mocks
    mock_settings.OPENAI_API_KEY = "fake-key"
    mock_extract.return_value = "Sample DOCX Text"

    # Mock OpenAI client
    mock_openai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"skills": ["Java"], "technologies": ["Spring"], "experience": [], "education": [], "certifications": []}'
            )
        )
    ]
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_openai_client):
        # Call the method
        result = ResumeParserService.parse_resume(b"dummy_bytes", "resume.docx")

        # Assertions
        assert isinstance(result, ResumeParseResponse)
        assert "Java" in result.skills
        assert "Spring" in result.technologies


def test_parse_resume_invalid_extension():
    result = ResumeParserService.parse_resume(b"dummy_bytes", "resume.txt")
    assert isinstance(result, ResumeParseResponse)
    assert len(result.skills) == 0
