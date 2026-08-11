"""Tests for resenha.gemini.GeminiClient."""

from unittest.mock import MagicMock, patch

import pytest

from resenha.gemini import GeminiClient


@patch("resenha.gemini.genai.Client")
def test_generate_calls_gemini(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "Mocked response"
    mock_client.models.generate_content.return_value = mock_response

    client = GeminiClient(api_key="test")
    result = client.generate("hello")

    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-flash-lite-latest",
        contents="hello",
        config={"max_output_tokens": 2000},
    )
    assert result == "Mocked response"


@patch("resenha.gemini.genai.Client")
def test_generate_retries_on_429(mock_client_class):
    from google.genai.errors import ClientError

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "Retry success"
    mock_client.models.generate_content.side_effect = [
        ClientError(429, {"error": {"message": "Rate limited"}}),
        mock_response,
    ]

    client = GeminiClient(api_key="test")
    result = client.generate("hello")

    assert mock_client.models.generate_content.call_count == 2
    assert result == "Retry success"


@patch("resenha.gemini.genai.Client")
def test_generate_raises_on_non_429(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("Server error")

    client = GeminiClient(api_key="test")
    with pytest.raises(Exception, match="Server error"):
        client.generate("hello")

    assert mock_client.models.generate_content.call_count == 1
