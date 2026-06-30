# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""

    db_url: str = "postgresql://jira_rag:jira_rag@localhost:5432/jira_rag"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    condensation_model: str = "claude-haiku-4-5-20251001"

    relevance_threshold: float = 0.35
    search_limit: int = 8


settings = Settings()
