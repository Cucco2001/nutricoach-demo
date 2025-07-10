"""
Manager per operazioni amministrative su Supabase.

Questo script permette di gestire utenti e dati su Supabase tramite parametri configurabili.
Eseguibile direttamente da linea di comando.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Determina la directory root del progetto
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Una directory sopra services/

# Aggiungi il path del progetto per importare i moduli
sys.path.append(PROJECT_ROOT)

from services.supabase_service import SupabaseUserService

# ==================== CONFIGURAZIONE PARAMETRI ====================
# Modifica questi parametri per configurare le operazioni da eseguire

# OPERAZIONE PRINCIPALE
OPERATION = "delete_user"  # Opzioni: "delete_user", "load_user", "list_users"

# PARAMETRI PER ELIMINAZIONE UTENTE
DELETE_USERNAME = "fake_test"  # Username da eliminare (solo se OPERATION = "delete_user")

# PARAMETRI PER CARICAMENTO UTENTE
LOAD_USERNAME = "fake_test"  # Username da caricare da locale a Supabase (solo se OPERATION = "load_user")

# PARAMETRI GENERALI
CONFIRM_OPERATIONS = True  # Se True, chiede conferma prima di operazioni distruttive
VERBOSE_LOGGING = True  # Se True, mostra log dettagliati

# ==================== CONFIGURAZIONE LOGGING ====================

def setup_logging():
    """Configura il sistema di logging."""
    level = logging.INFO if VERBOSE_LOGGING else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)

# ==================== GESTORE OPERAZIONI SUPABASE ====================

class SupabaseManager:
    """Manager per operazioni amministrative su Supabase."""
    
    def __init__(self):
        """Inizializza il manager."""
        self.logger = setup_logging()
        self.supabase_service = SupabaseUserService()
        
        if not self.supabase_service.is_available():
            self.logger.error("❌ Supabase non disponibile. Controlla le credenziali.")
            sys.exit(1)
    
    def list_users(self) -> None:
        """Lista tutti gli utenti presenti su Supabase."""
        self.logger.info("📋 Recupero lista utenti da Supabase...")
        
        try:
            users_data = self.supabase_service.download_users_from_supabase()
            
            if not users_data:
                self.logger.info("📝 Nessun utente trovato su Supabase")
                return
            
            print(f"\n{'='*60}")
            print(f"UTENTI PRESENTI SU SUPABASE ({len(users_data)} totali)")
            print(f"{'='*60}")
            
            for username, user_info in users_data.items():
                created_date = datetime.fromtimestamp(user_info['created_at']).strftime('%Y-%m-%d %H:%M')
                print(f"👤 {username}")
                print(f"   📧 Email: {user_info.get('email', 'N/A')}")
                print(f"   🆔 User ID: {user_info['user_id']}")
                print(f"   📅 Creato: {created_date}")
                print(f"   {'-'*40}")
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel recupero utenti: {str(e)}")
    
    def delete_user(self, username: str) -> bool:
        """
        Elimina un utente da Supabase (sia da users che da user_data).
        
        Args:
            username: Nome utente da eliminare
            
        Returns:
            bool: True se l'eliminazione è riuscita
        """
        self.logger.info(f"🗑️ Avvio eliminazione utente: {username}")
        
        # 1. Recupera informazioni utente
        users_data = self.supabase_service.download_users_from_supabase()
        if not users_data or username not in users_data:
            self.logger.error(f"❌ Utente '{username}' non trovato su Supabase")
            return False
        
        user_info = users_data[username]
        user_id = user_info['user_id']
        
        # 2. Chiedi conferma se richiesto
        if CONFIRM_OPERATIONS:
            print(f"\n⚠️  ATTENZIONE: Stai per eliminare l'utente '{username}' (ID: {user_id})")
            print("Questa operazione eliminerà:")
            print("- Il record utente dalla tabella 'users'")
            print("- Tutti i dati dell'utente dalla tabella 'user_data'")
            print("- L'operazione è IRREVERSIBILE")
            
            confirmation = input("\nDigita 'CONFERMA' per procedere: ")
            if confirmation != 'CONFERMA':
                self.logger.info("❌ Operazione annullata dall'utente")
                return False
        
        try:
            # 3. Elimina dai dati utente
            self.logger.info(f"🗑️ Eliminazione dati utente per {user_id}...")
            delete_user_data_response = self.supabase_service.supabase.table("user_data").delete().eq("user_id", user_id).execute()
            
            if delete_user_data_response.data:
                self.logger.info(f"✅ Dati utente eliminati per {user_id}")
            else:
                self.logger.warning(f"⚠️ Nessun dato utente trovato per {user_id}")
            
            # 4. Elimina dalla tabella users
            self.logger.info(f"🗑️ Eliminazione utente {username} dalla tabella users...")
            delete_user_response = self.supabase_service.supabase.table("users").delete().eq("user_id", user_id).execute()
            
            if delete_user_response.data:
                self.logger.info(f"✅ Utente {username} eliminato dalla tabella users")
            else:
                self.logger.error(f"❌ Errore nell'eliminazione utente {username}")
                return False
            
            self.logger.info(f"✅ Utente {username} eliminato completamente da Supabase")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore durante l'eliminazione di {username}: {str(e)}")
            return False
    
    def load_user_from_local(self, username: str) -> bool:
        """
        Carica un utente specifico da locale a Supabase.
        
        Args:
            username: Nome utente da caricare
            
        Returns:
            bool: True se il caricamento è riuscito
        """
        self.logger.info(f"⬆️ Avvio caricamento utente da locale: {username}")
        
        # 1. Verifica esistenza file users.json locale
        users_file = os.path.join(PROJECT_ROOT, "user_data", "users.json")
        if not os.path.exists(users_file):
            self.logger.error(f"❌ File {users_file} non trovato")
            return False
        
        # 2. Carica utenti locali
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                local_users = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Errore nella lettura di {users_file}: {str(e)}")
            return False
        
        # 3. Verifica che l'utente esista localmente
        if username not in local_users:
            self.logger.error(f"❌ Utente '{username}' non trovato in {users_file}")
            available_users = list(local_users.keys())
            self.logger.info(f"Utenti disponibili: {available_users}")
            return False
        
        user_info = local_users[username]
        user_id = user_info['user_id']
        
        # 4. Verifica esistenza file dati utente locale
        user_data_file = os.path.join(PROJECT_ROOT, "user_data", f"{user_id}.json")
        if not os.path.exists(user_data_file):
            self.logger.error(f"❌ File dati utente {user_data_file} non trovato")
            return False
        
        # 5. Carica dati utente locali
        try:
            with open(user_data_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Errore nella lettura di {user_data_file}: {str(e)}")
            return False
        
        # 6. Chiedi conferma se richiesto
        if CONFIRM_OPERATIONS:
            print(f"\n📤 Caricamento utente '{username}' da locale a Supabase")
            print(f"User ID: {user_id}")
            print(f"Email: {user_info.get('email', 'N/A')}")
            print(f"File dati: {user_data_file}")
            
            confirmation = input("\nProcedere con il caricamento? (y/N): ")
            if confirmation.lower() not in ['y', 'yes', 'si', 's']:
                self.logger.info("❌ Operazione annullata dall'utente")
                return False
        
        try:
            # 7. Sincronizza utente su Supabase
            self.logger.info(f"📤 Caricamento informazioni utente {username}...")
            user_dict = {username: user_info}
            
            if not self.supabase_service.sync_users_to_supabase(user_dict):
                self.logger.error(f"❌ Errore nel caricamento informazioni utente {username}")
                return False
            
            # 8. Sincronizza dati utente su Supabase
            self.logger.info(f"📤 Caricamento dati utente {user_id}...")
            
            if not self.supabase_service.sync_user_data_to_supabase(user_id, user_data):
                self.logger.error(f"❌ Errore nel caricamento dati utente {user_id}")
                return False
            
            self.logger.info(f"✅ Utente {username} caricato completamente su Supabase")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Errore durante il caricamento di {username}: {str(e)}")
            return False
    
    def run_operation(self) -> None:
        """Esegue l'operazione configurata nei parametri."""
        self.logger.info(f"🚀 Avvio operazione: {OPERATION}")
        
        if OPERATION == "list_users":
            self.list_users()
            
        elif OPERATION == "delete_user":
            if not DELETE_USERNAME:
                self.logger.error("❌ DELETE_USERNAME non specificato")
                return
            
            success = self.delete_user(DELETE_USERNAME)
            if success:
                print(f"\n✅ Utente '{DELETE_USERNAME}' eliminato con successo")
            else:
                print(f"\n❌ Errore nell'eliminazione di '{DELETE_USERNAME}'")
                
        elif OPERATION == "load_user":
            if not LOAD_USERNAME:
                self.logger.error("❌ LOAD_USERNAME non specificato")
                return
            
            success = self.load_user_from_local(LOAD_USERNAME)
            if success:
                print(f"\n✅ Utente '{LOAD_USERNAME}' caricato con successo")
            else:
                print(f"\n❌ Errore nel caricamento di '{LOAD_USERNAME}'")
                
        else:
            self.logger.error(f"❌ Operazione '{OPERATION}' non riconosciuta")
            self.logger.info("Operazioni disponibili: list_users, delete_user, load_user")


# ==================== ESECUZIONE PRINCIPALE ====================

def main():
    """Funzione principale del manager."""
    print("=" * 60)
    print("SUPABASE MANAGER - Gestione Utenti")
    print("=" * 60)
    print(f"Directory progetto: {PROJECT_ROOT}")
    print(f"Directory user_data: {os.path.join(PROJECT_ROOT, 'user_data')}")
    print(f"Operazione configurata: {OPERATION}")
    
    if OPERATION == "delete_user":
        print(f"Utente da eliminare: {DELETE_USERNAME}")
    elif OPERATION == "load_user":
        print(f"Utente da caricare: {LOAD_USERNAME}")
    
    print("=" * 60)
    
    try:
        manager = SupabaseManager()
        manager.run_operation()
        
    except KeyboardInterrupt:
        print("\n\n❌ Operazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 