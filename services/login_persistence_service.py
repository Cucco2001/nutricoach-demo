"""
Servizio per la persistenza del login tramite cookies.

Gestisce il salvataggio e il caricamento automatico delle credenziali utente
per mantenere l'utente loggato per un periodo determinato.
"""

import streamlit as st
import json
import time
import hashlib
import secrets
from typing import Optional, Dict, Tuple
from pathlib import Path


class LoginPersistenceService:
    """Servizio per la persistenza del login tramite cookies"""
    
    def __init__(self, cookie_name_prefix: str = "nutricoach_auth", default_expiry_days: int = 2):
        """
        Inizializza il servizio di persistenza login.
        
        Args:
            cookie_name_prefix: Prefisso per il nome del cookie
            default_expiry_days: Giorni di validità del cookie (default: 2)
        """
        self.cookie_name_prefix = cookie_name_prefix
        self.default_expiry_days = default_expiry_days
        self.controller = self._get_cookie_controller()
        self.token_store_path = Path("user_data/auth_tokens")
        self.token_store_path.mkdir(exist_ok=True)
        
    def _get_cookie_controller(self):
        """Ottiene l'istanza del controller cookies."""
        try:
            from streamlit_cookies_controller import CookieController
            
            # Nascondi il div del component per evitare flickering
            st.markdown("""
            <style>
            div[data-testid='element-container']:has(iframe[title='streamlit_cookies_controller.cookie_controller.cookie_controller']) {
                display: none;
            }
            </style>
            """, unsafe_allow_html=True)
            
            return CookieController()
        except ImportError:
            st.warning("⚠️ streamlit-cookies-controller non disponibile")
            return None
    
    def _generate_secure_token(self, user_id: str, device_fingerprint: str) -> str:
        """
        Genera un token sicuro per l'autenticazione.
        
        Args:
            user_id: ID dell'utente
            device_fingerprint: Fingerprint del dispositivo
            
        Returns:
            str: Token sicuro
        """
        # Genera un salt casuale
        salt = secrets.token_hex(16)
        
        # Crea timestamp
        timestamp = str(int(time.time()))
        
        # Combina informazioni per creare il token
        token_data = f"{user_id}:{device_fingerprint}:{timestamp}:{salt}"
        
        # Genera hash sicuro
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        
        return f"{token_hash}:{timestamp}:{salt}"
    
    def _get_device_fingerprint(self) -> str:
        """
        Genera un fingerprint del dispositivo basato su informazioni disponibili.
        
        Returns:
            str: Fingerprint del dispositivo
        """
        # Usa informazioni dalla sessione (più stabile senza time.time())
        session_info = str(st.session_state.get('_session_id', 'unknown'))
        
        # Tenta di ottenere user agent se disponibile
        try:
            # Prova a ottenere user agent dalla query params se disponibile
            user_agent = st.context.headers.get('user-agent', 'no-ua')
        except:
            user_agent = 'no-ua'
            
        # Estrai versione iOS e modello iPhone se è un iPhone per distinguere meglio
        ios_version = ""
        if 'iphone' in user_agent.lower():
            import re
            ios_match = re.search(r'os (\d+)_(\d+)', user_agent.lower())
            if ios_match:
                ios_version = f":ios_{ios_match.group(1)}_{ios_match.group(2)}"
            
            # Estrai anche il modello specifico dell'iPhone se disponibile
            model_match = re.search(r'iphone[,\s]?(\d+)', user_agent.lower())
            if model_match:
                ios_version += f":iphone{model_match.group(1)}"
            
            # Aggiungi un ID unico per questa sessione browser per distinguere tra dispositivi identici
            if '_session_browser_id' not in st.session_state:
                st.session_state._session_browser_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            ios_version += f":{st.session_state._session_browser_id}"
            
        # Crea un fingerprint più stabile e specifico
        fingerprint_data = f"streamlit:{session_info}:{user_agent}{ios_version}"
        
        # Se session_info è unknown, aggiungi un identificativo più specifico
        if session_info == 'unknown':
            # Usa un hash della combinazione di informazioni disponibili
            import platform
            system_info = f"{platform.system()}:{platform.release()}"
            fingerprint_data += f":{system_info}"
            
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:16]
        
    def _verify_device_fingerprint(self, saved_fingerprint: str) -> bool:
        """
        Verifica se il fingerprint del device corrente corrisponde a quello salvato.
        
        Args:
            saved_fingerprint: Fingerprint salvato nel token
            
        Returns:
            bool: True se il fingerprint corrisponde
        """
        current_fingerprint = self._get_device_fingerprint()
        return current_fingerprint == saved_fingerprint
    
    def _save_token_info(self, token: str, user_id: str, auth_type: str, expires_at: float) -> None:
        """
        Salva le informazioni del token su file.
        
        Args:
            token: Token di autenticazione
            user_id: ID dell'utente
            auth_type: Tipo di autenticazione (standard/google)
            expires_at: Timestamp di scadenza
        """
        try:
            token_hash = token.split(':')[0]
            token_file = self.token_store_path / f"{token_hash}.json"
            
            token_info = {
                'user_id': user_id,
                'auth_type': auth_type,
                'created_at': time.time(),
                'expires_at': expires_at,
                'device_fingerprint': self._get_device_fingerprint()
            }
            
            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            st.error(f"Errore nel salvare token: {e}")
    
    def _load_token_info(self, token: str) -> Optional[Dict]:
        """
        Carica le informazioni del token da file.
        
        Args:
            token: Token di autenticazione
            
        Returns:
            Dict: Informazioni del token o None se non valido
        """
        try:
            token_hash = token.split(':')[0]
            token_file = self.token_store_path / f"{token_hash}.json"
            
            if not token_file.exists():
                return None
            
            with open(token_file, 'r', encoding='utf-8') as f:
                token_info = json.load(f)
            
            # Verifica se il token è scaduto
            if time.time() > token_info.get('expires_at', 0):
                # Rimuovi token scaduto
                token_file.unlink(missing_ok=True)
                return None
            
            return token_info
            
        except Exception as e:
            st.error(f"Errore nel caricare token: {e}")
            return None
    
    def _cleanup_expired_tokens(self) -> None:
        """Pulisce i token scaduti dal sistema."""
        try:
            current_time = time.time()
            
            for token_file in self.token_store_path.glob("*.json"):
                try:
                    with open(token_file, 'r', encoding='utf-8') as f:
                        token_info = json.load(f)
                    
                    # Rimuovi token scaduti
                    if current_time > token_info.get('expires_at', 0):
                        token_file.unlink(missing_ok=True)
                        
                except Exception:
                    # In caso di errore, rimuovi il file corrotto
                    token_file.unlink(missing_ok=True)
                    
        except Exception as e:
            st.error(f"Errore nella pulizia token: {e}")
    
    def _get_unique_cookie_name(self, user_id: str, device_fingerprint: str) -> str:
        """
        Genera un nome di cookie unico per la combinazione user + device.
        
        Args:
            user_id: ID dell'utente
            device_fingerprint: Fingerprint del device
            
        Returns:
            str: Nome cookie unico
        """
        # Crea un hash della combinazione user_id + device_fingerprint
        combined = f"{user_id}:{device_fingerprint}"
        cookie_hash = hashlib.md5(combined.encode()).hexdigest()[:8]
        return f"{self.cookie_name_prefix}_{cookie_hash}"
        
    def _find_user_cookie(self) -> Optional[Tuple[str, Dict]]:
        """
        Cerca il cookie dell'utente corrente tra tutti i cookie salvati.
        
        Returns:
            Tuple[str, Dict]: (cookie_name, cookie_data) se trovato, None altrimenti
        """
        if not self.controller:
            return None
            
        try:
            current_device_fingerprint = self._get_device_fingerprint()
            
            # Cerca tra tutti i cookie che iniziano con il nostro prefisso
            all_cookies = self.controller.getAll()
            
            for cookie_name, cookie_value in all_cookies.items():
                if not cookie_name.startswith(self.cookie_name_prefix):
                    continue
                    
                try:
                    cookie_data = json.loads(cookie_value)
                    token = cookie_data.get('token')
                    
                    if not token:
                        continue
                        
                    # Verifica se questo token appartiene al device corrente
                    token_info = self._load_token_info(token)
                    if not token_info:
                        continue
                        
                    saved_fingerprint = token_info.get('device_fingerprint')
                    if saved_fingerprint == current_device_fingerprint:
                        return cookie_name, cookie_data
                        
                except (json.JSONDecodeError, Exception):
                    continue
                    
            return None
            
        except Exception as e:
            st.error(f"Errore nella ricerca cookie: {e}")
            return None

    def save_login_session(self, user_id: str, auth_type: str = "standard", 
                          expiry_days: Optional[int] = None) -> bool:
        """
        Salva la sessione di login nel cookie.
        
        Args:
            user_id: ID dell'utente
            auth_type: Tipo di autenticazione (standard/google)
            expiry_days: Giorni di validità (default: 2)
            
        Returns:
            bool: True se salvato con successo
        """
        if not self.controller:
            return False
        
        try:
            # Usa expiry_days fornito o default
            days = expiry_days or self.default_expiry_days
            
            # Genera device fingerprint
            device_fingerprint = self._get_device_fingerprint()
            
            # Genera nome cookie unico per questo user + device
            cookie_name = self._get_unique_cookie_name(user_id, device_fingerprint)
            
            # Genera token sicuro
            token = self._generate_secure_token(user_id, device_fingerprint)
            
            # Calcola scadenza
            expires_at = time.time() + (days * 24 * 60 * 60)
            
            # Salva informazioni token
            self._save_token_info(token, user_id, auth_type, expires_at)
            
            # Salva nel cookie specifico
            cookie_data = {
                'token': token,
                'user_id': user_id,
                'auth_type': auth_type
            }
            
            # Imposta cookie con scadenza
            max_age = days * 24 * 60 * 60  # In secondi
            self.controller.set(
                cookie_name, 
                json.dumps(cookie_data), 
                max_age=max_age
            )
            
            # Pulizia token scaduti
            self._cleanup_expired_tokens()
            
            return True
            
        except Exception as e:
            st.error(f"Errore nel salvare sessione: {e}")
            return False
    
    def load_login_session(self, user_data_manager) -> Optional[Tuple[str, str]]:
        """
        Carica la sessione di login dal cookie.
        
        Args:
            user_data_manager: Gestore dati utente per validare l'utente
            
        Returns:
            Tuple[str, str]: (user_id, auth_type) se valido, None altrimenti
        """
        if not self.controller:
            return None
        
        try:
            # Cerca il cookie dell'utente corrente
            cookie_result = self._find_user_cookie()
            
            if not cookie_result:
                return None
                
            cookie_name, cookie_data = cookie_result
            
            token = cookie_data.get('token')
            user_id = cookie_data.get('user_id')
            auth_type = cookie_data.get('auth_type', 'standard')
            
            if not token or not user_id:
                return None
            
            # Verifica token
            token_info = self._load_token_info(token)
            
            if not token_info:
                # Token non valido, rimuovi cookie
                self._clear_specific_cookie(cookie_name)
                return None
            
            # Verifica che user_id corrisponda
            if token_info.get('user_id') != user_id:
                self._clear_specific_cookie(cookie_name)
                return None
                
            # Verifica device fingerprint
            saved_fingerprint = token_info.get('device_fingerprint')
            if saved_fingerprint and not self._verify_device_fingerprint(saved_fingerprint):
                # Device fingerprint non corrisponde
                self._clear_specific_cookie(cookie_name)
                return None
            
            # Verifica che l'utente esista ancora nel sistema
            existing_user = user_data_manager.get_user_by_id(user_id)
            if not existing_user:
                self._clear_specific_cookie(cookie_name)
                return None
            
            return user_id, auth_type
            
        except Exception as e:
            st.error(f"Errore nel caricare sessione: {e}")
            return None
    
    def _clear_specific_cookie(self, cookie_name: str) -> bool:
        """
        Pulisce un cookie specifico e i dati associati.
        
        Args:
            cookie_name: Nome del cookie da rimuovere
            
        Returns:
            bool: True se pulito con successo
        """
        if not self.controller:
            return False
        
        try:
            # Ottieni cookie per rimuovere anche il token file
            cookie_value = self.controller.get(cookie_name)
            
            if cookie_value:
                try:
                    cookie_data = json.loads(cookie_value)
                    token = cookie_data.get('token')
                    
                    if token:
                        # Rimuovi file token
                        token_hash = token.split(':')[0]
                        token_file = self.token_store_path / f"{token_hash}.json"
                        token_file.unlink(missing_ok=True)
                        
                except Exception:
                    pass  # Ignora errori nella pulizia file
            
            # Rimuovi cookie
            self.controller.remove(cookie_name)
            
            return True
            
        except Exception as e:
            st.error(f"Errore nella pulizia cookie {cookie_name}: {e}")
            return False

    def clear_login_session(self) -> bool:
        """
        Pulisce la sessione di login corrente rimuovendo il cookie e i dati associati.
        
        Returns:
            bool: True se pulito con successo
        """
        try:
            # Cerca il cookie dell'utente corrente
            cookie_result = self._find_user_cookie()
            
            if not cookie_result:
                return True  # Nessun cookie da rimuovere
                
            cookie_name, _ = cookie_result
            return self._clear_specific_cookie(cookie_name)
            
        except Exception as e:
            st.error(f"Errore nella pulizia sessione: {e}")
            return False
    
    def extend_session(self, expiry_days: Optional[int] = None) -> bool:
        """
        Estende la sessione di login corrente.
        
        Args:
            expiry_days: Nuovi giorni di validità
            
        Returns:
            bool: True se esteso con successo
        """
        if not self.controller:
            return False
        
        try:
            # Cerca il cookie dell'utente corrente
            cookie_result = self._find_user_cookie()
            
            if not cookie_result:
                return False
                
            cookie_name, cookie_data = cookie_result
            user_id = cookie_data.get('user_id')
            auth_type = cookie_data.get('auth_type', 'standard')
            
            if not user_id:
                return False
            
            # Rimuovi sessione corrente
            self._clear_specific_cookie(cookie_name)
            
            # Crea nuova sessione con nuova scadenza
            return self.save_login_session(user_id, auth_type, expiry_days)
            
        except Exception as e:
            st.error(f"Errore nell'estendere sessione: {e}")
            return False


# Istanza globale del servizio
_login_persistence_service = None

def get_login_persistence_service() -> LoginPersistenceService:
    """
    Ottiene l'istanza del servizio di persistenza login.
    
    Returns:
        LoginPersistenceService: Istanza del servizio
    """
    global _login_persistence_service
    if _login_persistence_service is None:
        _login_persistence_service = LoginPersistenceService()
    return _login_persistence_service 