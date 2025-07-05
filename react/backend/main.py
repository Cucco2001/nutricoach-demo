"""
Backend FastAPI per NutrAICoach - Migrazione da Streamlit
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Carica le variabili d'ambiente
load_dotenv()

# Inizializza FastAPI
app = FastAPI(
    title="NutrAICoach API",
    description="API per l'assistente nutrizionale NutrAICoach",
    version="1.0.0"
)

# Configurazione CORS per permettere richieste dal frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Porte comuni per React dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security per autenticazione
security = HTTPBearer()

# === MODELLI PYDANTIC ===

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role del messaggio (user/assistant)")
    content: str = Field(..., description="Contenuto del messaggio")
    timestamp: Optional[datetime] = None

class SendMessageRequest(BaseModel):
    message: str = Field(..., description="Messaggio da inviare all'assistente")

class SendMessageResponse(BaseModel):
    response: str = Field(..., description="Risposta dell'assistente")
    message_id: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Lista dei messaggi della chat")
    total_messages: int = Field(..., description="Numero totale di messaggi")

class UserInfo(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    età: Optional[int] = None
    sesso: Optional[str] = None
    peso: Optional[float] = None
    altezza: Optional[float] = None
    attività: Optional[str] = None
    obiettivo: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

# === GESTIONE AUTENTICAZIONE ===

# Questo è un sistema di autenticazione semplificato per il demo
# In produzione, usare un sistema più sicuro con JWT, hash delle password, ecc.

DEMO_USERS = {
    "admin": {"password": "admin123", "id": "user_1", "email": "admin@nutricoach.com"},
    "demo": {"password": "demo123", "id": "user_2", "email": "demo@nutricoach.com"}
}

ACTIVE_SESSIONS = {}  # In produzione, usare Redis o database

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica il token di autenticazione e restituisce l'utente corrente
    """
    token = credentials.credentials
    
    if token not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o sessione scaduta"
        )
    
    return ACTIVE_SESSIONS[token]

# === MOCK DATA E SERVIZI ===

# Mock per i dati utente (in produzione, usare database)
MOCK_USER_DATA = {}
MOCK_CHAT_HISTORY = {}
MOCK_THREADS = {}

def get_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Recupera i dati utente dal mock storage"""
    return MOCK_USER_DATA.get(user_id)

def save_user_data(user_id: str, data: Dict[str, Any]):
    """Salva i dati utente nel mock storage"""
    MOCK_USER_DATA[user_id] = data

def get_chat_history(user_id: str) -> List[Dict[str, Any]]:
    """Recupera la cronologia chat dal mock storage"""
    return MOCK_CHAT_HISTORY.get(user_id, [])

def save_chat_message(user_id: str, role: str, content: str):
    """Salva un messaggio nella cronologia chat"""
    if user_id not in MOCK_CHAT_HISTORY:
        MOCK_CHAT_HISTORY[user_id] = []
    
    MOCK_CHAT_HISTORY[user_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

# === ENDPOINTS API ===

@app.get("/")
async def root():
    return {"message": "NutrAICoach API - Benvenuto!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# === AUTENTICAZIONE ===

@app.post("/auth/login")
async def login(user_login: UserLogin):
    """
    Endpoint per il login utente
    """
    username = user_login.username
    password = user_login.password
    
    # Verifica credenziali (sistema semplificato per demo)
    if username in DEMO_USERS and DEMO_USERS[username]["password"] == password:
        # Crea un token semplice (in produzione, usare JWT)
        token = f"token_{username}_{datetime.now().timestamp()}"
        user_info = {
            "id": DEMO_USERS[username]["id"],
            "username": username,
            "email": DEMO_USERS[username]["email"]
        }
        
        ACTIVE_SESSIONS[token] = user_info
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_info
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide"
    )

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Endpoint per il logout utente
    """
    # Rimuovi la sessione attiva
    tokens_to_remove = []
    for token, user_info in ACTIVE_SESSIONS.items():
        if user_info["id"] == current_user["id"]:
            tokens_to_remove.append(token)
    
    for token in tokens_to_remove:
        del ACTIVE_SESSIONS[token]
    
    return {"message": "Logout effettuato con successo"}

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Endpoint per ottenere le informazioni dell'utente corrente
    """
    user_id = current_user["id"]
    user_data = get_user_data(user_id)
    
    if user_data:
        return UserInfo(**user_data)
    
    return UserInfo(
        id=user_id,
        username=current_user["username"],
        email=current_user.get("email")
    )

# === CHAT API ===

@app.post("/chat/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint per inviare un messaggio all'assistente
    """
    user_id = current_user["id"]
    user_message = request.message
    
    # Salva il messaggio dell'utente
    save_chat_message(user_id, "user", user_message)
    
    # Simula risposta dell'assistente (da implementare con OpenAI)
    # Per ora, risposta mock
    assistant_response = f"Grazie per il messaggio: '{user_message}'. Sono il tuo assistente nutrizionale! Come posso aiutarti oggi?"
    
    # Salva la risposta dell'assistente
    save_chat_message(user_id, "assistant", assistant_response)
    
    return SendMessageResponse(
        response=assistant_response,
        message_id=f"msg_{datetime.now().timestamp()}"
    )

@app.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint per recuperare la cronologia della chat
    """
    user_id = current_user["id"]
    messages = get_chat_history(user_id)
    
    chat_messages = [
        ChatMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=datetime.fromisoformat(msg["timestamp"])
        ) for msg in messages
    ]
    
    return ChatHistoryResponse(
        messages=chat_messages,
        total_messages=len(chat_messages)
    )

@app.delete("/chat/clear")
async def clear_chat_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint per cancellare la cronologia della chat
    """
    user_id = current_user["id"]
    MOCK_CHAT_HISTORY[user_id] = []
    
    return {"message": "Cronologia chat cancellata"}

# === THREAD MANAGEMENT ===

@app.post("/chat/thread/create")
async def create_new_thread(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint per creare un nuovo thread di conversazione
    """
    user_id = current_user["id"]
    thread_id = f"thread_{user_id}_{datetime.now().timestamp()}"
    
    # Salva il thread (mock)
    MOCK_THREADS[user_id] = thread_id
    
    return {"thread_id": thread_id}

@app.get("/chat/thread/current")
async def get_current_thread(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint per ottenere il thread corrente
    """
    user_id = current_user["id"]
    thread_id = MOCK_THREADS.get(user_id)
    
    if not thread_id:
        # Crea un nuovo thread se non esiste
        thread_id = f"thread_{user_id}_{datetime.now().timestamp()}"
        MOCK_THREADS[user_id] = thread_id
    
    return {"thread_id": thread_id}

# === MAIN ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 