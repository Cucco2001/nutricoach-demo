"""
Servizio per l'autenticazione Google con Streamlit.

Gestisce il flusso OAuth2 per permettere agli utenti di accedere 
tramite il loro account Google.
"""

import streamlit as st
import json
import time
from typing import Optional, Dict, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import RefreshError
import hashlib
import os
from pathlib import Path


class GoogleAuthService:
    """Servizio per l'autenticazione Google"""
    
    def __init__(self):
        """Inizializza il servizio di autenticazione Google"""
        self.client_config = self._get_client_config()
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
    def _get_client_config(self) -> Dict:
        """
        Ottiene la configurazione del client OAuth2 da variabili d'ambiente o secrets.
        
        Returns:
            Dict: Configurazione del client OAuth2
        """
        try:
            # Carica le variabili d'ambiente dal file .env
            from dotenv import load_dotenv
            load_dotenv()
            
            # Usa direttamente le variabili d'ambiente
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
            
            if not client_id or not client_secret:
                print(f"❌ Credenziali Google mancanti - CLIENT_ID: {bool(client_id)}, CLIENT_SECRET: {bool(client_secret)}")
                print(f"CLIENT_ID: {client_id}")
                print(f"CLIENT_SECRET: {'***' if client_secret else 'None'}")
                return None
                
            config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }
            print(f"✅ Configurazione Google OAuth caricata - CLIENT_ID: {client_id[:10]}..., REDIRECT_URI: {redirect_uri}")
            return config
            
        except Exception as e:
            st.error(f"Errore nella configurazione OAuth Google: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        Verifica se il servizio Google Auth è disponibile.
        
        Returns:
            bool: True se disponibile, False altrimenti
        """
        return self.client_config is not None
    
    def get_authorization_url(self) -> Optional[str]:
        """
        Genera l'URL di autorizzazione Google.
        
        Returns:
            str: URL di autorizzazione o None se non disponibile
        """
        if not self.is_available():
            return None
            
        try:
            # Crea il flow OAuth2
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes
            )
            
            # Imposta l'URI di redirect
            flow.redirect_uri = self.client_config["web"]["redirect_uris"][0]
            
            # Genera l'URL di autorizzazione
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account'
            )
            
            # Salva lo state per la verifica
            st.session_state.google_auth_state = state
            
            return auth_url
            
        except Exception as e:
            st.error(f"Errore nella generazione URL autorizzazione: {e}")
            return None
    
    def handle_callback(self, authorization_response: str) -> Optional[Dict]:
        """
        Gestisce la risposta del callback OAuth2.
        
        Args:
            authorization_response: URL completo di risposta da Google
            
        Returns:
            Dict: Informazioni utente o None se errore
        """
        if not self.is_available():
            return None
            
        try:
            # Crea il flow OAuth2
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                state=st.session_state.get('google_auth_state')
            )
            
            flow.redirect_uri = self.client_config["web"]["redirect_uris"][0]
            
            # Ottieni il token
            flow.fetch_token(authorization_response=authorization_response)
            
            # Ottieni le informazioni dell'utente
            credentials = flow.credentials
            user_info = self._get_user_info(credentials)
            
            return user_info
            
        except Exception as e:
            st.error(f"Errore nel callback OAuth2: {e}")
            return None
    
    def _get_user_info(self, credentials: Credentials) -> Dict:
        """
        Ottiene le informazioni dell'utente dalle credenziali.
        
        Args:
            credentials: Credenziali OAuth2
            
        Returns:
            Dict: Informazioni utente
        """
        try:
            import requests
            
            # Richiesta alle API Google per ottenere info utente
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials.token}'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture'),
                    'google_id': user_data.get('id')
                }
            else:
                st.error(f"Errore nell'ottenere info utente: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Errore nell'ottenere informazioni utente: {e}")
            return None
    
    def create_google_user_id(self, google_id: str, email: str) -> str:
        """
        Crea un ID utente univoco basato sui dati Google.
        
        Args:
            google_id: ID Google dell'utente
            email: Email dell'utente
            
        Returns:
            str: ID utente univoco
        """
        # Crea un hash dell'ID Google per un ID utente univoco
        hash_input = f"google_{google_id}_{email}"
        hash_object = hashlib.sha256(hash_input.encode())
        return f"user_google_{hash_object.hexdigest()[:12]}"
    
    def register_or_login_google_user(self, user_info: Dict, user_data_manager) -> Tuple[bool, str]:
        """
        Registra o effettua login di un utente Google.
        
        Args:
            user_info: Informazioni utente da Google
            user_data_manager: Gestore dati utente
            
        Returns:
            Tuple[bool, str]: (successo, user_id o messaggio errore)
        """
        try:
            email = user_info.get('email')
            google_id = user_info.get('google_id')
            name = user_info.get('name', '')
            
            if not email or not google_id:
                return False, "Informazioni Google incomplete"
            
            # Crea un ID utente univoco
            user_id = self.create_google_user_id(google_id, email)
            
            # Verifica se l'utente esiste già
            existing_user = user_data_manager.get_user_by_id(user_id)
            
            if existing_user:
                # Login utente esistente
                user_data_manager._load_user_data(user_id)
                return True, user_id
            else:
                # Registra nuovo utente
                # Crea un username basato sul nome e email
                username = self._create_username_from_email(email, name)
                
                # Salva l'utente nel sistema
                success = self._save_google_user(
                    user_data_manager, 
                    username, 
                    email, 
                    user_id, 
                    google_id,
                    name
                )
                
                if success:
                    return True, user_id
                else:
                    return False, "Errore nella registrazione utente Google"
                    
        except Exception as e:
            return False, f"Errore nell'autenticazione Google: {str(e)}"
    
    def _create_username_from_email(self, email: str, name: str) -> str:
        """
        Crea un username dal nome e email.
        
        Args:
            email: Email dell'utente
            name: Nome dell'utente
            
        Returns:
            str: Username generato
        """
        # Prova prima con il nome
        if name:
            base_username = name.lower().replace(' ', '_')
            # Rimuovi caratteri speciali
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
        else:
            # Fallback con la parte locale dell'email
            base_username = email.split('@')[0].lower()
        
        # Aggiungi suffisso per evitare conflitti
        timestamp = str(int(time.time()))[-6:]  # Ultimi 6 cifre del timestamp
        return f"{base_username}_g{timestamp}"
    
    def _save_google_user(self, user_data_manager, username: str, email: str, 
                         user_id: str, google_id: str, name: str) -> bool:
        """
        Salva un utente Google nel sistema.
        
        Args:
            user_data_manager: Gestore dati utente
            username: Username generato
            email: Email dell'utente
            user_id: ID utente
            google_id: ID Google
            name: Nome dell'utente
            
        Returns:
            bool: True se salvato con successo
        """
        try:
            # Importa la classe User
            from agent_tools.user_data_manager import User
            
            # Crea l'oggetto User
            user = User(
                username=username,
                email=email,
                password_hash="GOOGLE_AUTH",  # Placeholder per utenti Google
                user_id=user_id,
                created_at=time.time()
            )
            
            # Salva l'utente
            user_data_manager._users[username] = user
            user_data_manager._save_users()
            
            # Salva informazioni aggiuntive Google in un file separato
            self._save_google_user_info(user_id, google_id, name)
            
            return True
            
        except Exception as e:
            st.error(f"Errore nel salvare utente Google: {e}")
            return False
    
    def _save_google_user_info(self, user_id: str, google_id: str, name: str) -> None:
        """
        Salva informazioni aggiuntive Google.
        
        Args:
            user_id: ID utente
            google_id: ID Google
            name: Nome dell'utente
        """
        try:
            google_info = {
                'google_id': google_id,
                'name': name,
                'auth_type': 'google',
                'created_at': time.time()
            }
            
            # Salva in un file separato per le info Google
            google_info_dir = Path("user_data/google_auth")
            google_info_dir.mkdir(exist_ok=True)
            
            google_info_file = google_info_dir / f"{user_id}_google.json"
            with open(google_info_file, 'w', encoding='utf-8') as f:
                json.dump(google_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            st.error(f"Errore nel salvare info Google: {e}")


# Istanza globale del servizio
_google_auth_service = None

def get_google_auth_service() -> GoogleAuthService:
    """
    Ottiene l'istanza del servizio Google Auth.
    
    Returns:
        GoogleAuthService: Istanza del servizio
    """
    global _google_auth_service
    if _google_auth_service is None:
        _google_auth_service = GoogleAuthService()
    return _google_auth_service 