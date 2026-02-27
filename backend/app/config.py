"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./backoffice.db"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "backoffice"

    # API Keys
    openrouter_api_key: str = ""
    senso_api_key: str = ""
    reka_api_key: str = ""
    yutori_api_key: str = ""
    tavily_api_key: str = ""
    render_api_key: str = ""
    notion_token: str = ""
    airbyte_client_id: str = ""
    airbyte_client_secret: str = ""

    # Base URLs
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    senso_base_url: str = "https://apiv2.senso.ai/api/v1"
    reka_base_url: str = "https://vision-agent.api.reka.ai"
    yutori_base_url: str = "https://api.yutori.com/v1"
    tavily_base_url: str = "https://api.tavily.com"
    airbyte_base_url: str = "https://api.airbyte.ai"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
