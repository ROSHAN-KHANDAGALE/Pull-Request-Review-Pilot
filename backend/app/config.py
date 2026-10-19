from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    model_name: str = Field(
        validation_alias=AliasChoices("MODEL_NAME", "DEFAULT_MODEL")
    )
    github_token: str
    allowed_origins: list[str]

    secret_key: str
    access_token_expire_minutes: int

    redis_url: str | None = None
    use_celery: bool = Field(
        default=True,
        validation_alias=AliasChoices("USE_CELERY", "ENABLE_CELERY"),
    )
    enable_rate_limiting: bool = True

    @model_validator(mode="after")
    def validate_celery_configuration(self):
        if self.use_celery and not self.redis_url:
            raise ValueError("REDIS_URL is required when USE_CELERY is enabled")
        return self

    model_config = {
        "env_file": ".env",
        "protected_namespaces": ("settings_",),
    }


settings = Settings()