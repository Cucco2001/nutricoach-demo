"""
Configurazione del backend FastAPI
"""

import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configurazione dell'applicazione
    """
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # JWT Configuration - Nomi compatibili con main.py
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 giorni
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Istanza globale delle impostazioni
_settings = Settings()

def get_settings() -> Settings:
    """
    Restituisce l'istanza delle impostazioni
    """
    return _settings

# Esporta l'oggetto settings per importazione diretta
settings = _settings 