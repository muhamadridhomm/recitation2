from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Arabic Document Intelligence API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = ""
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173", # SvelteKit Default Dev Port
        "http://localhost:8080",
        "http://127.0.0.1:5173",
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
