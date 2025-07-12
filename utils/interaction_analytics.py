"""
Modulo di analisi delle interazioni utente.

Fornisce funzioni per analizzare le statistiche delle interazioni
di tutti gli utenti presenti nel sistema locale.
"""

import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def get_total_interactions_count(user_data_dir: str = "user_data") -> int:
    """
    Calcola il numero totale di interazioni di tutti gli utenti nel sistema.
    
    Args:
        user_data_dir: Directory contenente i file utente (default: "user_data")
        
    Returns:
        int: Numero totale di interazioni di tutti gli utenti
    """
    try:
        user_data_path = Path(user_data_dir)
        
        if not user_data_path.exists():
            logger.warning(f"Directory {user_data_dir} non trovata")
            return 0
        
        total_interactions = 0
        
        # Trova tutti i file JSON utente (esclude users.json)
        user_files = list(user_data_path.glob("*.json"))
        user_files = [f for f in user_files if f.name != "users.json"]
        
        for user_file in user_files:
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_interactions = data.get("interazioni", 0)
                    total_interactions += user_interactions
                    
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Errore nel leggere {user_file}: {str(e)}")
                continue
        
        return total_interactions
        
    except Exception as e:
        logger.error(f"Errore nel calcolo interazioni totali: {str(e)}")
        return 0


def get_users_interactions_breakdown(user_data_dir: str = "user_data") -> Dict[str, Dict]:
    """
    Ottiene un breakdown dettagliato delle interazioni per ogni utente.
    
    Args:
        user_data_dir: Directory contenente i file utente (default: "user_data")
        
    Returns:
        Dict: Dizionario con {user_id: {interazioni, chat_messages, username, last_activity}}
    """
    try:
        user_data_path = Path(user_data_dir)
        users_file = user_data_path / "users.json"
        
        if not user_data_path.exists():
            logger.warning(f"Directory {user_data_dir} non trovata")
            return {}
        
        # Carica informazioni utenti per ottenere username
        users_info = {}
        if users_file.exists():
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    # Crea mapping user_id -> username
                    for username, user_data in users_data.items():
                        users_info[user_data['user_id']] = {
                            'username': username,
                            'email': user_data.get('email', 'N/A'),
                            'created_at': user_data.get('created_at', 0)
                        }
            except Exception as e:
                logger.warning(f"Errore nel leggere users.json: {str(e)}")
        
        breakdown = {}
        
        # Trova tutti i file JSON utente (esclude users.json)
        user_files = list(user_data_path.glob("*.json"))
        user_files = [f for f in user_files if f.name != "users.json"]
        
        for user_file in user_files:
            try:
                user_id = user_file.stem  # Nome file senza estensione
                
                with open(user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Estrai statistiche
                total_interactions = data.get("interazioni", 0)
                chat_history = data.get("chat_history", [])
                
                # Conta messaggi utente nella chat
                chat_user_messages = len([msg for msg in chat_history if msg.get('role') == 'user'])
                
                # Calcola coach interactions (solo se total_interactions > 0)
                if total_interactions > 0:
                    coach_interactions = max(0, total_interactions - chat_user_messages)
                else:
                    # Per utenti senza campo interazioni, usa solo i dati della chat
                    coach_interactions = 0
                    total_interactions = chat_user_messages
                
                # Trova ultima attività
                last_activity = 0
                if chat_history:
                    last_activity = max([msg.get('timestamp', 0) for msg in chat_history])
                
                # Informazioni utente
                user_info = users_info.get(user_id, {})
                
                breakdown[user_id] = {
                    'username': user_info.get('username', f'user_{user_id[:8]}'),
                    'email': user_info.get('email', 'N/A'),
                    'total_interactions': total_interactions,
                    'chat_interactions': chat_user_messages,
                    'coach_interactions': coach_interactions,
                    'last_activity': last_activity,
                    'last_activity_formatted': datetime.fromtimestamp(last_activity).strftime('%Y-%m-%d %H:%M') if last_activity > 0 else 'Mai',
                    'created_at': user_info.get('created_at', 0)
                }
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Errore nel leggere {user_file}: {str(e)}")
                continue
        
        return breakdown
        
    except Exception as e:
        logger.error(f"Errore nel breakdown interazioni: {str(e)}")
        return {}


def get_interactions_statistics(user_data_dir: str = "user_data") -> Dict[str, any]:
    """
    Ottiene statistiche complete sulle interazioni del sistema.
    
    Args:
        user_data_dir: Directory contenente i file utente (default: "user_data")
        
    Returns:
        Dict: Statistiche complete del sistema
    """
    try:
        breakdown = get_users_interactions_breakdown(user_data_dir)
        
        if not breakdown:
            return {
                'total_users': 0,
                'total_interactions': 0,
                'total_chat_interactions': 0,
                'total_coach_interactions': 0,
                'active_users': 0,
                'average_interactions_per_user': 0,
                'most_active_user': None,
                'users_breakdown': {}
            }
        
        # Calcola statistiche aggregate
        total_users = len(breakdown)
        total_interactions = sum(user['total_interactions'] for user in breakdown.values())
        total_chat = sum(user['chat_interactions'] for user in breakdown.values())
        total_coach = sum(user['coach_interactions'] for user in breakdown.values())
        
        # Utenti attivi (con almeno 1 interazione)
        active_users = len([user for user in breakdown.values() if user['total_interactions'] > 0])
        
        # Media interazioni per utente
        avg_interactions = total_interactions / total_users if total_users > 0 else 0
        
        # Utente più attivo
        most_active = None
        if breakdown:
            most_active_user_id = max(breakdown.keys(), key=lambda k: breakdown[k]['total_interactions'])
            most_active = {
                'user_id': most_active_user_id,
                'username': breakdown[most_active_user_id]['username'],
                'interactions': breakdown[most_active_user_id]['total_interactions']
            }
        
        return {
            'total_users': total_users,
            'total_interactions': total_interactions,
            'total_chat_interactions': total_chat,
            'total_coach_interactions': total_coach,
            'active_users': active_users,
            'average_interactions_per_user': round(avg_interactions, 2),
            'most_active_user': most_active,
            'users_breakdown': breakdown
        }
        
    except Exception as e:
        logger.error(f"Errore nel calcolo statistiche: {str(e)}")
        return {}


def print_interactions_report(user_data_dir: str = "user_data") -> None:
    """
    Stampa un report dettagliato delle interazioni del sistema.
    
    Args:
        user_data_dir: Directory contenente i file utente (default: "user_data")
    """
    try:
        print("📊 REPORT INTERAZIONI SISTEMA")
        print("=" * 50)
        
        stats = get_interactions_statistics(user_data_dir)
        
        if not stats or stats['total_users'] == 0:
            print("❌ Nessun dato utente trovato")
            return
        
        # Statistiche generali
        print(f"\n📈 STATISTICHE GENERALI:")
        print(f"   👥 Utenti totali: {stats['total_users']}")
        print(f"   💬 Interazioni totali: {stats['total_interactions']}")
        print(f"   🥗 Interazioni Chat: {stats['total_chat_interactions']}")
        print(f"   🤖 Interazioni Coach: {stats['total_coach_interactions']}")
        print(f"   ✅ Utenti attivi: {stats['active_users']}")
        print(f"   📊 Media per utente: {stats['average_interactions_per_user']}")
        
        # Utente più attivo
        if stats['most_active_user']:
            most_active = stats['most_active_user']
            print(f"\n🏆 UTENTE PIÙ ATTIVO:")
            print(f"   👤 {most_active['username']} ({most_active['user_id'][:8]}...)")
            print(f"   💬 {most_active['interactions']} interazioni")
        
        # Top 5 utenti
        breakdown = stats['users_breakdown']
        if breakdown:
            sorted_users = sorted(breakdown.items(), key=lambda x: x[1]['total_interactions'], reverse=True)
            
            print(f"\n🔝 TOP 5 UTENTI PIÙ ATTIVI:")
            for i, (user_id, user_data) in enumerate(sorted_users[:5], 1):
                print(f"   {i}. {user_data['username']} - {user_data['total_interactions']} interazioni")
                print(f"      (Chat: {user_data['chat_interactions']}, Coach: {user_data['coach_interactions']})")
                print(f"      Ultima attività: {user_data['last_activity_formatted']}")
                print()
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Errore nella generazione del report: {str(e)}")


def export_interactions_csv(user_data_dir: str = "user_data", output_file: str = "interactions_export.csv") -> bool:
    """
    Esporta le statistiche delle interazioni in un file CSV.
    
    Args:
        user_data_dir: Directory contenente i file utente (default: "user_data")
        output_file: Nome del file CSV di output (default: "interactions_export.csv")
        
    Returns:
        bool: True se l'esportazione è riuscita
    """
    try:
        import csv
        
        breakdown = get_users_interactions_breakdown(user_data_dir)
        
        if not breakdown:
            logger.warning("Nessun dato da esportare")
            return False
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'user_id', 'username', 'email', 'total_interactions', 
                'chat_interactions', 'coach_interactions', 'last_activity_formatted'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user_id, user_data in breakdown.items():
                writer.writerow({
                    'user_id': user_id,
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'total_interactions': user_data['total_interactions'],
                    'chat_interactions': user_data['chat_interactions'],
                    'coach_interactions': user_data['coach_interactions'],
                    'last_activity_formatted': user_data['last_activity_formatted']
                })
        
        print(f"✅ Dati esportati in: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Errore nell'esportazione CSV: {str(e)}")
        return False


# Funzione di convenienza per uso rapido
def quick_total() -> int:
    """
    Funzione rapida per ottenere il totale delle interazioni.
    
    Returns:
        int: Numero totale di interazioni di tutti gli utenti
    """
    return get_total_interactions_count()


if __name__ == "__main__":
    # Script eseguibile per report rapido
    print_interactions_report() 