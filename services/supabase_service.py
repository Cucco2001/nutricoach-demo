"""
Servizio per la gestione dei dati utente su Supabase.

Questo modulo gestisce la sincronizzazione dei dati utente tra locale e Supabase,
garantendo che i dati non vengano persi quando si usa Streamlit Cloud.
"""

import os
import json
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
import logging
from services.state_service import app_state

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class SupabaseUserService:
    """Servizio per la gestione dei dati utente su Supabase."""
    
    def __init__(self):
        """Inizializza il client Supabase."""
        self.supabase: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Inizializza il client Supabase usando le credenziali disponibili."""
        try:
            # Per Streamlit Cloud, usa st.secrets, altrimenti usa variabile d'ambiente
            try:
                url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
            except:
                # Fallback per sviluppo locale
                url = os.getenv("SUPABASE_URL")
                key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                logger.error("SUPABASE_URL o SUPABASE_KEY non trovati")
                return
                
            self.supabase = create_client(url, key)
            logger.info("✅ Client Supabase inizializzato correttamente")
            
        except Exception as e:
            logger.error(f"❌ Errore nell'inizializzazione Supabase: {str(e)}")
            self.supabase = None
    
    def is_available(self) -> bool:
        """Verifica se il servizio Supabase è disponibile."""
        return self.supabase is not None
    
    # ==================== GESTIONE UTENTI ====================
    
    def sync_users_to_supabase(self, local_users_data: Dict[str, Any]) -> bool:
        """
        Sincronizza gli utenti locali su Supabase.
        
        Args:
            local_users_data: Dati degli utenti dal file users.json locale
            
        Returns:
            bool: True se la sincronizzazione è riuscita
        """
        if not self.is_available():
            logger.warning("⚠️ Supabase non disponibile per sincronizzazione utenti")
            return False
        
        try:
            # Converte users.json nel formato per Supabase
            users_for_supabase = []
            for username, user_data in local_users_data.items():
                users_for_supabase.append({
                    "username": username,
                    "email": user_data.get("email", ""),
                    "password_hash": user_data["password_hash"],
                    "user_id": user_data["user_id"],
                    "created_at": datetime.fromtimestamp(user_data["created_at"]).isoformat()
                })
            
            # Upsert su Supabase (insert o update se esiste già)
            for user in users_for_supabase:
                try:
                    self.supabase.table("users").upsert(user, on_conflict="user_id").execute()
                    logger.info(f"✅ Utente {user['username']} sincronizzato su Supabase")
                except Exception as e:
                    logger.error(f"❌ Errore sincronizzazione utente {user['username']}: {str(e)}")
                    return False
            
            logger.info(f"✅ {len(users_for_supabase)} utenti sincronizzati su Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore nella sincronizzazione utenti: {str(e)}")
            return False
    
    def download_users_from_supabase(self) -> Optional[Dict[str, Any]]:
        """
        Scarica tutti gli utenti da Supabase.
        
        Returns:
            Dict nel formato users.json o None se errore
        """
        if not self.is_available():
            logger.warning("⚠️ Supabase non disponibile per download utenti")
            return None
        
        try:
            response = self.supabase.table("users").select("*").execute()
            
            if not response.data:
                logger.info("📝 Nessun utente trovato su Supabase")
                return {}
            
            # Converte nel formato users.json
            users_data = {}
            for user in response.data:
                # Gestisce diversi formati di timestamp da Supabase
                try:
                    created_at_str = user["created_at"]
                    # Rimuove eventuali caratteri in eccesso e gestisce microsecondi
                    if created_at_str.endswith('+00:00'):
                        created_at_str = created_at_str.replace('+00:00', '+00:00')
                    elif created_at_str.endswith('Z'):
                        created_at_str = created_at_str.replace('Z', '+00:00')
                    
                    # Se ci sono troppi microsecondi, taglia a 6 cifre
                    if '.' in created_at_str:
                        parts = created_at_str.split('.')
                        if len(parts) == 2:
                            microseconds_part = parts[1].split('+')[0]
                            if len(microseconds_part) > 6:
                                microseconds_part = microseconds_part[:6]
                            created_at_str = f"{parts[0]}.{microseconds_part}+00:00"
                    
                    created_timestamp = datetime.fromisoformat(created_at_str).timestamp()
                except Exception as e:
                    logger.warning(f"⚠️ Errore parsing timestamp per {user.get('username', 'unknown')}: {str(e)}")
                    # Fallback: usa timestamp corrente
                    created_timestamp = datetime.now().timestamp()
                
                users_data[user["username"]] = {
                    "username": user["username"],
                    "email": user.get("email", ""),
                    "password_hash": user["password_hash"],
                    "user_id": user["user_id"],
                    "created_at": created_timestamp
                }
            
            logger.info(f"✅ {len(users_data)} utenti scaricati da Supabase")
            return users_data
            
        except Exception as e:
            logger.error(f"❌ Errore nel download utenti da Supabase: {str(e)}")
            return None
    
    # ==================== GESTIONE DATI UTENTE ====================
    
    def sync_user_data_to_supabase(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Sincronizza i dati di un utente specifico su Supabase.
        
        Args:
            user_id: ID dell'utente
            user_data: Dati dell'utente dal file JSON locale
            
        Returns:
            bool: True se la sincronizzazione è riuscita
        """
        if not self.is_available():
            logger.warning(f"⚠️ Supabase non disponibile per sincronizzazione dati utente {user_id}")
            return False
        
        try:
            # Prepara i dati per Supabase
            supabase_data = {
                "user_id": user_id,
                "data": json.dumps(user_data, ensure_ascii=False),
                "updated_at": datetime.now().isoformat()
            }
            
            # Upsert su Supabase
            self.supabase.table("user_data").upsert(supabase_data, on_conflict="user_id").execute()
            logger.info(f"✅ Dati utente {user_id} sincronizzati su Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore sincronizzazione dati utente {user_id}: {str(e)}")
            return False
    
    def download_user_data_from_supabase(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Scarica i dati di un utente specifico da Supabase.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dict con i dati dell'utente o None se non trovato/errore
        """
        if not self.is_available():
            logger.warning(f"⚠️ Supabase non disponibile per download dati utente {user_id}")
            return None
        
        try:
            response = self.supabase.table("user_data").select("*").eq("user_id", user_id).execute()
            
            if not response.data:
                logger.info(f"📝 Nessun dato trovato per utente {user_id} su Supabase")
                return None
            
            # Prende il primo record (dovrebbe essere unico per user_id)
            user_record = response.data[0]
            
            # Gestisce sia string JSON che dict diretto da Supabase
            if isinstance(user_record["data"], str):
                user_data = json.loads(user_record["data"])
            else:
                user_data = user_record["data"]
            
            logger.info(f"✅ Dati utente {user_id} scaricati da Supabase")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ Errore nel download dati utente {user_id} da Supabase: {str(e)}")
            return None
    
    def download_all_user_data_from_supabase(self) -> Dict[str, Any]:
        """
        Scarica tutti i dati utente da Supabase.
        
        Returns:
            Dict con {user_id: user_data} per tutti gli utenti
        """
        if not self.is_available():
            logger.warning("⚠️ Supabase non disponibile per download di tutti i dati utente")
            return {}
        
        try:
            response = self.supabase.table("user_data").select("*").execute()
            
            if not response.data:
                logger.info("📝 Nessun dato utente trovato su Supabase")
                return {}
            
            # Converte in formato {user_id: data}
            all_user_data = {}
            for record in response.data:
                user_id = record["user_id"]
                
                # Gestisce sia string JSON che dict diretto da Supabase
                if isinstance(record["data"], str):
                    user_data = json.loads(record["data"])
                else:
                    user_data = record["data"]
                    
                all_user_data[user_id] = user_data
            
            logger.info(f"✅ Dati di {len(all_user_data)} utenti scaricati da Supabase")
            return all_user_data
            
        except Exception as e:
            logger.error(f"❌ Errore nel download di tutti i dati utente da Supabase: {str(e)}")
            return {}
    
    # ==================== OPERAZIONI DI SINCRONIZZAZIONE ====================
    
    def ensure_tables_exist(self) -> bool:
        """
        Verifica che le tabelle necessarie esistano su Supabase.
        
        Nota: Questa funzione presuppone che le tabelle siano già create
        tramite l'interfaccia web di Supabase o script SQL.
        
        Returns:
            bool: True se le tabelle sono accessibili
        """
        if not self.is_available():
            return False
        
        try:
            # Test di connessione alle tabelle
            self.supabase.table("users").select("user_id").limit(1).execute()
            self.supabase.table("user_data").select("user_id").limit(1).execute()
            logger.info("✅ Tabelle Supabase verificate e accessibili")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore nell'accesso alle tabelle Supabase: {str(e)}")
            logger.info("""
            💡 Assicurati che le seguenti tabelle esistano su Supabase:
            
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                user_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE TABLE user_data (
                id SERIAL PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
            return False
    
    def sync_all_local_data_to_supabase(self) -> bool:
        """
        Sincronizza tutti i dati locali su Supabase.
        
        Returns:
            bool: True se la sincronizzazione completa è riuscita
        """
        logger.info("🔄 Avvio sincronizzazione completa locale → Supabase")
        
        if not self.ensure_tables_exist():
            logger.error("❌ Sincronizzazione interrotta: tabelle non accessibili")
            return False
        
        success = True
        
        # 1. Sincronizza utenti
        try:
            users_file = "user_data/users.json"
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                if not self.sync_users_to_supabase(users_data):
                    success = False
            else:
                logger.warning("⚠️ File users.json non trovato")
        except Exception as e:
            logger.error(f"❌ Errore sincronizzazione utenti: {str(e)}")
            success = False
        
        # 2. Sincronizza dati utente individuali
        user_data_dir = "user_data"
        if os.path.exists(user_data_dir):
            for filename in os.listdir(user_data_dir):
                if filename.endswith(".json") and filename != "users.json":
                    user_id = filename.replace(".json", "")
                    
                    try:
                        with open(os.path.join(user_data_dir, filename), 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                        
                        if not self.sync_user_data_to_supabase(user_id, user_data):
                            success = False
                    except Exception as e:
                        logger.error(f"❌ Errore sincronizzazione dati {user_id}: {str(e)}")
                        success = False
        
        if success:
            logger.info("✅ Sincronizzazione completa locale → Supabase completata")
        else:
            logger.warning("⚠️ Sincronizzazione completata con alcuni errori")
        
        return success
    
    def download_all_data_from_supabase(self) -> bool:
        """
        Scarica tutti i dati da Supabase e li salva localmente.
        
        Returns:
            bool: True se il download è riuscito
        """
        logger.info("⬇️ Avvio download completo Supabase → locale")
        
        if not self.is_available():
            logger.error("❌ Download interrotto: Supabase non disponibile")
            return False
        
        success = True
        
        # Crea directory user_data se non esiste
        os.makedirs("user_data", exist_ok=True)
        
        # 1. Scarica utenti
        try:
            users_data = self.download_users_from_supabase()
            if users_data is not None:
                with open("user_data/users.json", 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, ensure_ascii=False, indent=2)
                logger.info("✅ File users.json aggiornato da Supabase")
            else:
                success = False
        except Exception as e:
            logger.error(f"❌ Errore download utenti: {str(e)}")
            success = False
        
        # 2. Scarica dati utente individuali
        try:
            all_user_data = self.download_all_user_data_from_supabase()
            
            for user_id, user_data in all_user_data.items():
                filename = f"user_data/{user_id}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ File {filename} aggiornato da Supabase")
                
        except Exception as e:
            logger.error(f"❌ Errore download dati utente: {str(e)}")
            success = False
        
        if success:
            logger.info("✅ Download completo Supabase → locale completato")
        else:
            logger.warning("⚠️ Download completato con alcuni errori")
        
        return success


# ==================== UTILITY FUNCTIONS ====================

def get_supabase_service() -> SupabaseUserService:
    """
    Ottiene un'istanza del servizio Supabase, utilizzando il caching dello stato dell'app.
    Gestisce anche i casi in cui lo stato non è disponibile.
    
    Returns:
        SupabaseUserService: Istanza del servizio
    """
    try:
        # Usa il nuovo sistema di stato dell'app
        service = app_state.get_supabase_service()
        if service is None:
            service = SupabaseUserService()
            app_state.set_supabase_service(service)
        return service
        
    except Exception as e:
        # Fallback di sicurezza: crea sempre una nuova istanza
        logger.warning(f"⚠️ Errore nell'accesso al sistema di stato: {str(e)}, creando istanza temporanea")
        return SupabaseUserService()


def auto_sync_user_data(user_id: str, user_data: Dict[str, Any]) -> None:
    """
    Sincronizza automaticamente i dati di un utente su Supabase quando vengono modificati.
    Funzione robusta che gestisce tutti i possibili errori senza interrompere l'applicazione.
    
    Args:
        user_id: ID dell'utente
        user_data: Dati dell'utente da sincronizzare
    """
    try:
        supabase_service = get_supabase_service()
        if supabase_service and supabase_service.is_available():
            success = supabase_service.sync_user_data_to_supabase(user_id, user_data)
            if success:
                logger.debug(f"✅ Auto-sync completato per {user_id}")
            else:
                logger.warning(f"⚠️ Auto-sync fallito per {user_id}, ma dati salvati localmente")
        else:
            logger.debug(f"📴 Auto-sync saltato per {user_id}: Supabase non disponibile")
    except Exception as e:
        # Log dell'errore ma non interrompere l'applicazione
        logger.error(f"❌ Errore durante auto-sync per {user_id}: {str(e)}")
        logger.debug(f"💾 Dati dell'utente {user_id} comunque salvati localmente") 