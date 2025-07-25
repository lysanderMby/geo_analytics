from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Geo Analytics"
    
    # CORS Settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Supabase Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # LLM API Settings (these will be provided by users, not stored here)
    # Just placeholders for validation
    OPENAI_MODELS: List[str] = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    ANTHROPIC_MODELS: List[str] = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
    GEMINI_MODELS: List[str] = ["gemini-pro", "gemini-pro-vision"]
    
    class Config:
        env_file = ".env"

settings = Settings() 