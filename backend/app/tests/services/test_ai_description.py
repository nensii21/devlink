from unittest.mock import MagicMock, patch

from app.schemas.ai import ProjectDescriptionGenerateRequest
from app.services.ai_service import AIService


@patch("app.services.ai_service.settings")
@patch("app.services.ai_service.OpenAI")
def test_generate_project_description_success(mock_openai, mock_settings):
    # Mock settings
    mock_settings.OPENAI_API_KEY = "test_key"

    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a great project description."
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    req = ProjectDescriptionGenerateRequest(prompt="A cool project")
    resp = AIService.generate_project_description(req)

    assert resp.description == "This is a great project description."
    mock_client.chat.completions.create.assert_called_once()


@patch("app.services.ai_service.settings")
def test_generate_project_description_no_api_key(mock_settings):
    mock_settings.OPENAI_API_KEY = None

    req = ProjectDescriptionGenerateRequest(prompt="A cool project")
    resp = AIService.generate_project_description(req)

    assert "could not be generated at this time" in resp.description


@patch("app.services.ai_service.settings")
@patch("app.services.ai_service.OpenAI")
def test_generate_project_description_api_error(mock_openai, mock_settings):
    mock_settings.OPENAI_API_KEY = "test_key"

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_client

    req = ProjectDescriptionGenerateRequest(prompt="A cool project")
    resp = AIService.generate_project_description(req)

    assert "could not be generated at this time" in resp.description
