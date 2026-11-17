from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    default_model: str = "gemini-2.5-flash"
    classifier_model: str = "gemini-2.5-flash-lite"
    audit_log_path: str = "audit_logs.jsonl"
    enable_strict_blocking: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
