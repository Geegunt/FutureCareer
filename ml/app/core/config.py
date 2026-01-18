from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки приложения"""
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VibeCode ML Service"
    
    GROQ_API_KEY: str = ""
    SCIBOX_API_BASE: str = "https://api.groq.com/openai/v1"
    
    MODEL_AWQ: str = "llama-3.3-70b-versatile"
    MODEL_CODER: str = "llama-3.3-70b-versatile"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
