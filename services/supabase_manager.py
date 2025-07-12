"""
Manager per operazioni amministrative su Supabase.

Questo script permette di gestire utenti e dati su Supabase tramite parametri configurabili.
Eseguibile direttamente da linea di comando.

OPERAZIONI DISPONIBILI:
- list_users: Lista tutti gli utenti presenti su Supabase
- delete_user: Elimina un utente specifico da Supabase (IRREVERSIBILE)
- load_user: Carica un utente specifico da locale a Supabase
- sync_all_from_supabase: Scarica tutti i dati da Supabase e li salva localmente

ESEMPI DI USO:

1. Sincronizzazione completa da Supabase:
   OPERATION = "sync_all_from_supabase"
   BACKUP_EXISTING_DATA = True
   OVERWRITE_LOCAL_DATA = False
   
2. Lista utenti:
   OPERATION = "list_users"
   
3. Caricamento utente specifico:
   OPERATION = "load_user"
   LOAD_USERNAME = "nome_utente"
   
4. Eliminazione utente (ATTENZIONE):
   OPERATION = "delete_user"
   DELETE_USERNAME = "nome_utente"
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
OPERATION = "sync_all_from_supabase"  # Opzioni: "delete_user", "load_user", "list_users", "sync_all_from_supabase", "load_all"

# PARAMETRI PER ELIMINAZIONE UTENTE
DELETE_USERNAME = ""  # Username da eliminare (solo se OPERATION = "delete_user")

# PARAMETRI PER CARICAMENTO UTENTE
LOAD_USERNAME = "Army69"  # Username da caricare da locale a Supabase (solo se OPERATION = "load_user")

# PARAMETRI GENERALI
CONFIRM_OPERATIONS = True  # Se True, chiede conferma prima di operazioni distruttive
VERBOSE_LOGGING = True  # Se True, mostra log dettagliati

# PARAMETRI PER SINCRONIZZAZIONE DA SUPABASE
BACKUP_EXISTING_DATA = False  # Se True, crea backup dei dati locali esistenti prima della sincronizzazione
OVERWRITE_LOCAL_DATA = False  # Se True, sovrascrive i dati locali esistenti senza chiedere conferma

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
    
    def sync_all_from_supabase(self) -> bool:
        """
        Sincronizza tutti i dati da Supabase al sistema locale.
        Scarica tutti gli utenti e i loro dati da Supabase e li salva localmente.
        
        Returns:
            bool: True se la sincronizzazione è riuscita
        """
        self.logger.info("🔄 Avvio sincronizzazione completa da Supabase...")
        
        # 1. Definisci le directory
        user_data_dir = os.path.join(PROJECT_ROOT, "user_data")
        backup_dir = os.path.join(PROJECT_ROOT, "user_data_backup")
        
        # 2. Crea directory se non esistono
        os.makedirs(user_data_dir, exist_ok=True)
        
        # 3. Backup dei dati esistenti se richiesto
        if BACKUP_EXISTING_DATA:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(PROJECT_ROOT, f"user_data_backup_{timestamp}")
            
            self.logger.info(f"💾 Creazione backup dati esistenti in: {backup_dir}")
            
            try:
                import shutil
                if os.path.exists(user_data_dir):
                    shutil.copytree(user_data_dir, backup_dir)
                    self.logger.info(f"✅ Backup creato in: {backup_dir}")
                else:
                    self.logger.info("📁 Directory user_data non esistente, nessun backup necessario")
            except Exception as e:
                self.logger.warning(f"⚠️ Errore nella creazione del backup: {str(e)}")
                if CONFIRM_OPERATIONS:
                    proceed = input("Continuare senza backup? (y/N): ")
                    if proceed.lower() not in ['y', 'yes', 'si', 's']:
                        self.logger.info("❌ Operazione annullata")
                        return False
        
        try:
            # 4. Scarica tutti gli utenti da Supabase
            self.logger.info("📥 Scaricamento utenti da Supabase...")
            users_data = self.supabase_service.download_users_from_supabase()
            
            if not users_data:
                self.logger.info("📝 Nessun utente trovato su Supabase")
                return True
            
            self.logger.info(f"👥 Trovati {len(users_data)} utenti su Supabase")
            
            # 5. Chiedi conferma se richiesto
            if CONFIRM_OPERATIONS and not OVERWRITE_LOCAL_DATA:
                print(f"\n🔄 SINCRONIZZAZIONE DA SUPABASE")
                print(f"Utenti da sincronizzare: {len(users_data)}")
                print(f"Directory locale: {user_data_dir}")
                if BACKUP_EXISTING_DATA:
                    print(f"Backup creato in: {backup_dir}")
                
                print("\nUtenti che verranno sincronizzati:")
                for username, user_info in users_data.items():
                    print(f"  👤 {username} (ID: {user_info['user_id']})")
                
                confirmation = input(f"\nProcedere con la sincronizzazione di {len(users_data)} utenti? (y/N): ")
                if confirmation.lower() not in ['y', 'yes', 'si', 's']:
                    self.logger.info("❌ Operazione annullata dall'utente")
                    return False
            
            # 6. Salva users.json locale
            users_file = os.path.join(user_data_dir, "users.json")
            self.logger.info(f"💾 Salvataggio users.json in: {users_file}")
            
            try:
                with open(users_file, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2, ensure_ascii=False)
                self.logger.info("✅ users.json salvato con successo")
            except Exception as e:
                self.logger.error(f"❌ Errore nel salvataggio di users.json: {str(e)}")
                return False
            
            # 7. Scarica e salva i dati di ogni utente
            success_count = 0
            error_count = 0
            
            for username, user_info in users_data.items():
                user_id = user_info['user_id']
                self.logger.info(f"📥 Scaricamento dati per utente: {username} (ID: {user_id})")
                
                try:
                    # Scarica dati utente da Supabase
                    user_data = self.supabase_service.download_user_data_from_supabase(user_id)
                    
                    if user_data:
                        # Salva file dati utente
                        user_data_file = os.path.join(user_data_dir, f"{user_id}.json")
                        
                        with open(user_data_file, 'w', encoding='utf-8') as f:
                            json.dump(user_data, f, indent=2, ensure_ascii=False)
                        
                        self.logger.info(f"✅ Dati salvati per {username}: {user_data_file}")
                        success_count += 1
                    else:
                        self.logger.warning(f"⚠️ Nessun dato trovato per {username} (ID: {user_id})")
                        success_count += 1  # Consideriamo successo anche se non ci sono dati
                        
                except Exception as e:
                    self.logger.error(f"❌ Errore nel download dati per {username}: {str(e)}")
                    error_count += 1
            
            # 8. Riepilogo operazione
            self.logger.info(f"📊 Sincronizzazione completata:")
            self.logger.info(f"   ✅ Utenti sincronizzati con successo: {success_count}")
            self.logger.info(f"   ❌ Errori durante la sincronizzazione: {error_count}")
            
            if error_count == 0:
                self.logger.info("🎉 Sincronizzazione completata con successo!")
                return True
            else:
                self.logger.warning(f"⚠️ Sincronizzazione completata con {error_count} errori")
                return success_count > 0
                
        except Exception as e:
            self.logger.error(f"❌ Errore durante la sincronizzazione: {str(e)}")
            return False
    
    def load_all_users_to_supabase(self) -> bool:
        """
        Carica tutti gli utenti da locale a Supabase.
        Legge tutti i file utente locali e li sincronizza con Supabase.
        
        Returns:
            bool: True se il caricamento è riuscito
        """
        self.logger.info("⬆️ Avvio caricamento completo da locale a Supabase...")
        
        # 1. Definisci le directory
        user_data_dir = os.path.join(PROJECT_ROOT, "user_data")
        users_file = os.path.join(user_data_dir, "users.json")
        
        # 2. Verifica esistenza directory e file users.json
        if not os.path.exists(user_data_dir):
            self.logger.error(f"❌ Directory {user_data_dir} non trovata")
            return False
        
        if not os.path.exists(users_file):
            self.logger.error(f"❌ File {users_file} non trovato")
            return False
        
        try:
            # 3. Carica utenti locali
            self.logger.info("📖 Caricamento utenti locali...")
            with open(users_file, 'r', encoding='utf-8') as f:
                local_users = json.load(f)
            
            if not local_users:
                self.logger.info("📝 Nessun utente trovato localmente")
                return True
            
            self.logger.info(f"👥 Trovati {len(local_users)} utenti locali")
            
            # 4. Chiedi conferma se richiesto
            if CONFIRM_OPERATIONS:
                print(f"\n⬆️ CARICAMENTO COMPLETO A SUPABASE")
                print(f"Utenti da caricare: {len(local_users)}")
                print(f"Directory locale: {user_data_dir}")
                
                print("\nUtenti che verranno caricati:")
                for username, user_info in local_users.items():
                    user_id = user_info['user_id']
                    user_data_file = os.path.join(user_data_dir, f"{user_id}.json")
                    has_data = "✅" if os.path.exists(user_data_file) else "❌"
                    print(f"  👤 {username} (ID: {user_id}) {has_data}")
                
                confirmation = input(f"\nProcedere con il caricamento di {len(local_users)} utenti? (y/N): ")
                if confirmation.lower() not in ['y', 'yes', 'si', 's']:
                    self.logger.info("❌ Operazione annullata dall'utente")
                    return False
            
            # 5. Carica users.json su Supabase
            self.logger.info("⬆️ Caricamento users.json su Supabase...")
            if not self.supabase_service.sync_users_to_supabase(local_users):
                self.logger.error("❌ Errore nel caricamento users.json")
                return False
            
            self.logger.info("✅ users.json caricato con successo")
            
            # 6. Carica i dati di ogni utente
            success_count = 0
            error_count = 0
            
            for username, user_info in local_users.items():
                user_id = user_info['user_id']
                user_data_file = os.path.join(user_data_dir, f"{user_id}.json")
                
                self.logger.info(f"⬆️ Caricamento dati per utente: {username} (ID: {user_id})")
                
                try:
                    # Verifica esistenza file dati utente
                    if not os.path.exists(user_data_file):
                        self.logger.warning(f"⚠️ File dati non trovato per {username}: {user_data_file}")
                        # Crea un file dati vuoto per mantenere la consistenza
                        empty_data = {
                            "user_preferences": None,
                            "chat_history": [],
                            "nutritional_info": None,
                            "interazioni": 0
                        }
                        
                        if not self.supabase_service.sync_user_data_to_supabase(user_id, empty_data):
                            self.logger.error(f"❌ Errore nel caricamento dati vuoti per {username}")
                            error_count += 1
                            continue
                        
                        self.logger.info(f"✅ Dati vuoti caricati per {username}")
                        success_count += 1
                        continue
                    
                    # Carica dati utente locali
                    with open(user_data_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    # Assicurati che il campo interazioni sia presente
                    if "interazioni" not in user_data:
                        # Calcola dalle chat history esistenti
                        chat_history = user_data.get("chat_history", [])
                        user_messages = [msg for msg in chat_history if msg.get("role") == "user"]
                        user_data["interazioni"] = len(user_messages)
                        
                        # Salva il file aggiornato localmente
                        with open(user_data_file, 'w', encoding='utf-8') as f:
                            json.dump(user_data, f, indent=2, ensure_ascii=False)
                        
                        self.logger.info(f"  📊 Campo 'interazioni' aggiunto: {user_data['interazioni']}")
                    
                    # Carica su Supabase
                    if not self.supabase_service.sync_user_data_to_supabase(user_id, user_data):
                        self.logger.error(f"❌ Errore nel caricamento dati per {username}")
                        error_count += 1
                        continue
                    
                    self.logger.info(f"✅ Dati caricati per {username}")
                    success_count += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Errore nel caricamento dati per {username}: {str(e)}")
                    error_count += 1
            
            # 7. Riepilogo operazione
            self.logger.info(f"📊 Caricamento completato:")
            self.logger.info(f"   ✅ Utenti caricati con successo: {success_count}")
            self.logger.info(f"   ❌ Errori durante il caricamento: {error_count}")
            
            if error_count == 0:
                self.logger.info("🎉 Caricamento completato con successo!")
                return True
            else:
                self.logger.warning(f"⚠️ Caricamento completato con {error_count} errori")
                return success_count > 0
                
        except Exception as e:
            self.logger.error(f"❌ Errore durante il caricamento: {str(e)}")
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
                
        elif OPERATION == "sync_all_from_supabase":
            success = self.sync_all_from_supabase()
            if success:
                print(f"\n✅ Sincronizzazione da Supabase completata con successo")
            else:
                print(f"\n❌ Errore durante la sincronizzazione da Supabase")
                
        elif OPERATION == "load_all":
            success = self.load_all_users_to_supabase()
            if success:
                print(f"\n✅ Caricamento completo su Supabase completato con successo")
            else:
                print(f"\n❌ Errore durante il caricamento completo su Supabase")
                
        else:
            self.logger.error(f"❌ Operazione '{OPERATION}' non riconosciuta")
            self.logger.info("Operazioni disponibili: list_users, delete_user, load_user, sync_all_from_supabase, load_all")


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
    elif OPERATION == "sync_all_from_supabase":
        print(f"Backup dati esistenti: {'Sì' if BACKUP_EXISTING_DATA else 'No'}")
        print(f"Sovrascrittura automatica: {'Sì' if OVERWRITE_LOCAL_DATA else 'No'}")
    
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