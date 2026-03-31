from unittest.mock import MagicMock, patch

from src.hello_llm import call_deepseek


def test_call_deepseek_returns_text() -> None:
    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = "LangGraph is a library for building stateful agents."
    with patch("src.hello_llm.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = mock_response
        result = call_deepseek("What is LangGraph?", api_key="fake-key")
    assert result == "LangGraph is a library for building stateful agents."
