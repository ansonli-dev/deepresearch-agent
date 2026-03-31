"""LangSmith tracing configuration.

LangSmith auto-tracing works via environment variables. When
LANGCHAIN_TRACING_V2=true, every LLM call made through a LangChain
ChatModel is automatically recorded to the LangSmith dashboard.

Call configure_tracing() once at startup, before any LLM invocation.
"""

import os

from langsmith import Client

from src.models.config import Settings


def configure_tracing(settings: Settings | None = None) -> None:
    """Set environment variables that enable LangChain auto-tracing."""
    if settings is None:
        settings = Settings()  # type: ignore[call-arg]
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key


def get_client(settings: Settings | None = None) -> Client:
    """Return a LangSmith client for manual run logging if needed."""
    if settings is None:
        settings = Settings()  # type: ignore[call-arg]
    return Client(api_key=settings.langsmith_api_key)
