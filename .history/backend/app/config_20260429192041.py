from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    database_url: str = "sqlite:///./resumagic.db"
    jwt_secret: str = "local_dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()
