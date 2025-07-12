"""
Script per inizializzare il campo "interazioni" per tutti i file utente esistenti.

Questo script:
1. Analizza tutti i file utente esistenti
2. Calcola il numero corretto di interazioni dalla chat history (solo messaggi "user")
3. Aggiunge il campo "interazioni" con il valore corretto
4. Mantiene tutti gli altri dati intatti
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_interactions_from_chat_history(chat_history: list) -> int:
    """
    Calcola il numero di interazioni dalla chat history.
    Conta solo i messaggi con role="user".
    
    Args:
        chat_history: Lista dei messaggi della chat
        
    Returns:
        int: Numero di interazioni (messaggi dell'utente)
    """
    if not chat_history:
        return 0
    
    user_messages = [msg for msg in chat_history if msg.get("role") == "user"]
    return len(user_messages)

def initialize_interactions_field() -> Dict[str, Any]:
    """
    Inizializza il campo "interazioni" per tutti i file utente esistenti.
    
    Returns:
        Dict con statistiche dell'operazione
    """
    user_data_dir = Path("user_data")
    
    if not user_data_dir.exists():
        logger.error("Directory user_data non trovata")
        return {"success": False, "error": "Directory user_data non trovata"}
    
    # Statistiche
    stats = {
        "success": True,
        "total_files": 0,
        "updated_files": 0,
        "already_had_field": 0,
        "errors": 0,
        "error_details": [],
        "files_processed": []
    }
    
    # Processa tutti i file utente
    for file_path in user_data_dir.glob("user_*.json"):
        stats["total_files"] += 1
        
        try:
            logger.info(f"Processando file: {file_path.name}")
            
            # Leggi il file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Controlla se il campo esiste già
            if "interazioni" in data:
                stats["already_had_field"] += 1
                logger.info(f"  ⚪ Campo 'interazioni' già presente: {data['interazioni']}")
                stats["files_processed"].append({
                    "file": file_path.name,
                    "status": "already_present",
                    "interactions": data["interazioni"]
                })
                continue
            
            # Calcola le interazioni dalla chat history
            chat_history = data.get("chat_history", [])
            interactions_count = calculate_interactions_from_chat_history(chat_history)
            
            # Aggiungi il campo
            data["interazioni"] = interactions_count
            
            # Salva il file aggiornato
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            stats["updated_files"] += 1
            logger.info(f"  ✅ Campo 'interazioni' aggiunto: {interactions_count}")
            
            stats["files_processed"].append({
                "file": file_path.name,
                "status": "updated",
                "interactions": interactions_count,
                "chat_messages": len(chat_history)
            })
            
        except Exception as e:
            stats["errors"] += 1
            error_msg = f"Errore con {file_path.name}: {str(e)}"
            logger.error(f"  ❌ {error_msg}")
            stats["error_details"].append(error_msg)
            
            stats["files_processed"].append({
                "file": file_path.name,
                "status": "error",
                "error": str(e)
            })
    
    return stats

def print_report(stats: Dict[str, Any]) -> None:
    """
    Stampa un report dettagliato delle operazioni eseguite.
    
    Args:
        stats: Statistiche dell'operazione
    """
    print("\n" + "="*60)
    print("REPORT INIZIALIZZAZIONE CAMPO 'INTERAZIONI'")
    print("="*60)
    
    print(f"📊 STATISTICHE GENERALI:")
    print(f"   📁 File totali processati: {stats['total_files']}")
    print(f"   ✅ File aggiornati: {stats['updated_files']}")
    print(f"   ⚪ File che già avevano il campo: {stats['already_had_field']}")
    print(f"   ❌ Errori: {stats['errors']}")
    
    if stats['error_details']:
        print(f"\n❌ DETTAGLI ERRORI:")
        for error in stats['error_details']:
            print(f"   • {error}")
    
    print(f"\n📋 DETTAGLI FILE PROCESSATI:")
    for file_info in stats['files_processed']:
        if file_info['status'] == 'updated':
            print(f"   ✅ {file_info['file']}: {file_info['interactions']} interazioni (da {file_info['chat_messages']} messaggi)")
        elif file_info['status'] == 'already_present':
            print(f"   ⚪ {file_info['file']}: {file_info['interactions']} interazioni (già presente)")
        elif file_info['status'] == 'error':
            print(f"   ❌ {file_info['file']}: ERRORE - {file_info['error']}")
    
    print(f"\n🎉 OPERAZIONE COMPLETATA!")
    if stats['errors'] == 0:
        print("   Tutti i file sono stati processati con successo!")
    else:
        print(f"   Completata con {stats['errors']} errori.")

def main():
    """Funzione principale."""
    print("🚀 Avvio inizializzazione campo 'interazioni'...")
    
    # Esegui l'inizializzazione
    stats = initialize_interactions_field()
    
    # Stampa il report
    print_report(stats)
    
    return stats['success']

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 