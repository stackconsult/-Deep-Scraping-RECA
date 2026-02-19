"""
Unit tests for GoogleClient (providers/google_client.py).
All Gemini API calls are mocked — no GOOGLE_API_KEY required.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from types import SimpleNamespace

from providers.google_client import GoogleClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """GoogleClient initialised with a fake key (API never called)."""
    with patch("providers.google_client.genai") as mock_genai:
        c = GoogleClient(api_key="fake-key-for-testing")
    return c


def _mock_response(text="Hello from Gemini", prompt_tokens=10, output_tokens=5):
    """Build a fake GenerateContentResponse-like object."""
    resp = MagicMock()
    resp.text = text
    resp.usage_metadata = SimpleNamespace(
        prompt_token_count=prompt_tokens,
        candidates_token_count=output_tokens,
        total_token_count=prompt_tokens + output_tokens,
    )
    return resp


# ---------------------------------------------------------------------------
# Invoke — single-turn
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_single_turn(client):
    """Single user message should call generate_content."""
    fake_resp = _mock_response("Extracted: john@test.com")

    with patch("providers.google_client.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.return_value = fake_resp
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.invoke(
            model_id="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": "You are an extraction assistant."},
                {"role": "user", "content": "Extract the email from: john@test.com"},
            ],
        )

    assert result["content"] == "Extracted: john@test.com"
    assert result["provider"] == "google"
    assert result["model"] == "gemini-2.0-flash"
    assert result["usage"]["input_tokens"] == 10
    assert result["usage"]["output_tokens"] == 5


# ---------------------------------------------------------------------------
# Invoke — multi-turn
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_multi_turn(client):
    """Multi-turn messages should use start_chat + send_message."""
    fake_resp = _mock_response("Follow-up answer")

    with patch("providers.google_client.genai") as mock_genai:
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_chat.send_message.return_value = fake_resp
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model

        result = await client.invoke(
            model_id="gemini-1.5-pro",
            messages=[
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "Follow up question"},
            ],
        )

    assert result["content"] == "Follow-up answer"
    mock_model.start_chat.assert_called_once()


# ---------------------------------------------------------------------------
# Invoke — error propagation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invoke_api_error(client):
    """API errors should propagate as exceptions."""
    with patch("providers.google_client.genai") as mock_genai:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("quota exceeded")
        mock_genai.GenerativeModel.return_value = mock_model

        with pytest.raises(Exception, match="quota exceeded"):
            await client.invoke(
                model_id="gemini-2.0-flash",
                messages=[{"role": "user", "content": "test"}],
            )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check_with_key():
    """health_check returns True when API key is set."""
    with patch("providers.google_client.genai"):
        c = GoogleClient(api_key="real-key")
    assert c.health_check() is True


def test_health_check_without_key():
    """health_check returns False when no API key."""
    with patch("providers.google_client.genai"), \
         patch.dict("os.environ", {}, clear=True):
        c = GoogleClient(api_key="")
    assert c.health_check() is False


# ---------------------------------------------------------------------------
# get_available_models
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_available_models_success(client):
    """Should return model names that support generateContent."""
    mock_models = [
        SimpleNamespace(name="gemini-2.0-flash", supported_generation_methods=["generateContent"]),
        SimpleNamespace(name="embedding-001", supported_generation_methods=["embedContent"]),
        SimpleNamespace(name="gemini-1.5-pro", supported_generation_methods=["generateContent"]),
    ]
    with patch("providers.google_client.genai") as mock_genai:
        mock_genai.list_models.return_value = mock_models

        models = await client.get_available_models()

    assert "gemini-2.0-flash" in models
    assert "gemini-1.5-pro" in models
    assert "embedding-001" not in models


@pytest.mark.asyncio
async def test_get_available_models_fallback(client):
    """On error, should return hardcoded fallback list."""
    with patch("providers.google_client.genai") as mock_genai:
        mock_genai.list_models.side_effect = Exception("network error")

        models = await client.get_available_models()

    assert len(models) == 3
    assert "gemini-2.0-flash" in models
