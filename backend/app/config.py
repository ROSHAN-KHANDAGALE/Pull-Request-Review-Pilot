from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    model_name: str
    github_token: str
    allowed_origins: list[str]

    model_config = {
        "env_file": Path(__file__).parent / ".env"
    }

settings = Settings()