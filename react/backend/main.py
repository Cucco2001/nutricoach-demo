from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import jwt
from datetime import datetime, timedelta
import hashlib
from pathlib import Path

# Aggiungo il path del progetto principale per importare UserDataManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agent_tools.user_data_manager import UserDataManager, ChatMessage
from config import get_settings

app = FastAPI(title="NutrAICoach API", version="1.0.0")
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Inizializzo UserDataManager usando la directory user_data del progetto principale
user_data_manager = UserDataManager(data_dir=os.path.join(os.path.dirname(__file__), '..', '..', 'user_data'))

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str

class UserInfo(BaseModel):
    user_id: str
    username: str
    email: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: float

class ChatHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: float

# Token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    # Usa UserDataManager per autenticare
    success, result = user_data_manager.login_user(login_request.username.lower(), login_request.password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = result
    user = user_data_manager.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        username=user.username
    )

@app.post("/auth/logout")
async def logout(current_user: str = Depends(verify_token)):
    # Per ora non facciamo nulla, il token scade automaticamente
    return {"message": "Successfully logged out"}

@app.get("/auth/me", response_model=UserInfo)
async def get_current_user(current_user: str = Depends(verify_token)):
    user = user_data_manager.get_user_by_id(current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        user_id=user.user_id,
        username=user.username,
        email=user.email
    )

@app.post("/chat/send", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user: str = Depends(verify_token)
):
    # Salva il messaggio dell'utente
    user_data_manager.save_chat_message(current_user, "user", chat_request.message)
    
    # Simula una risposta dell'assistente (per ora)
    # TODO: Integrare con OpenAI e il sistema di agent
    assistant_response = f"Hai scritto: {chat_request.message}. Questa è una risposta di test del sistema React integrato con i dati Streamlit!"
    
    # Salva la risposta dell'assistente
    user_data_manager.save_chat_message(current_user, "assistant", assistant_response)
    
    return ChatResponse(
        response=assistant_response,
        timestamp=datetime.now().timestamp()
    )

@app.get("/chat/history", response_model=List[ChatHistoryItem])
async def get_chat_history(current_user: str = Depends(verify_token)):
    chat_history = user_data_manager.get_chat_history(current_user)
    return [
        ChatHistoryItem(
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp
        )
        for msg in chat_history
    ]

@app.delete("/chat/clear")
async def clear_chat_history(current_user: str = Depends(verify_token)):
    user_data_manager.clear_chat_history(current_user)
    return {"message": "Chat history cleared"}

@app.post("/chat/thread/create")
async def create_new_thread(current_user: str = Depends(verify_token)):
    # Per ora equivale a pulire la chat history
    user_data_manager.clear_chat_history(current_user)
    return {"message": "New thread created"}

@app.get("/chat/thread/current")
async def get_current_thread(current_user: str = Depends(verify_token)):
    # Per ora ritorniamo solo se c'è una history
    chat_history = user_data_manager.get_chat_history(current_user)
    return {
        "thread_id": f"thread_{current_user}",
        "message_count": len(chat_history)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 