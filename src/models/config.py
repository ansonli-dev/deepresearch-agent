from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM providers
    deepseek_api_key: str = ""

    # Search
    tavily_api_key: str

    # Observability
    langsmith_api_key: str = ""
    langsmith_project: str = "deepresearch-agent"
    langchain_tracing_v2: bool = False

    # Active model profile
    model_profile: str = "default"
