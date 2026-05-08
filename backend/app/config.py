from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    database_url: str = "sqlite:///./resumagic.db"
    jwt_secret: str = "local_dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    frontend_url: str = "http://127.0.0.1:5173"
    email_provider: str = "console"
    resend_api_key: str = ""
    email_from: str = "noreply@resumagic.com"
    class Config:
        env_file = ".env"
        extra = "ignore"
    use_mock_ai: bool = False
        
settings = Settings()
