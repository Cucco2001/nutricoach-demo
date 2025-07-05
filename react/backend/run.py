#!/usr/bin/env python3
"""
Script per avviare il backend FastAPI
"""

import uvicorn
from config import settings

if __name__ == "__main__":
    print("🚀 Avvio del backend NutrAICoach FastAPI...")
    print(f"📡 Server disponibile su: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 Documentazione API: http://{settings.api_host}:{settings.api_port}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        reload_dirs=["./"] if settings.api_debug else None
    ) 