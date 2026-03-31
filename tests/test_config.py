import pytest
from pydantic import ValidationError

from src.models.config import Settings


def test_settings_loads_with_tavily_key() -> None:
    s = Settings(tavily_api_key="test-key")
    assert s.tavily_api_key == "test-key"
    assert s.model_profile == "default"


def test_missing_tavily_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
