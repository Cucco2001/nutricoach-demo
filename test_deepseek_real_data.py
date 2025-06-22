#!/usr/bin/env python3
"""
Test rapido della coda DeepSeek usando dati utente reali esistenti.
"""

import time
import json
import os
from services.deep_seek_service.deepseek_manager import DeepSeekManager

def test_with_real_user():
    """Test usando un utente reale esistente nel sistema."""
    
    # Trova un utente con conversazioni esistenti
    user_data_dir = "user_data"
    real_user_id = None
    
    if os.path.exists(user_data_dir):
        for filename in os.listdir(user_data_dir):
            if filename.endswith('.json'):
                user_id = filename[:-5]
                with open(f"{user_data_dir}/{filename}", 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                conversations = user_data.get('nutritional_info', {}).get('agent_qa', [])
                if conversations:
                    real_user_id = user_id
                    print(f"✅ Trovato utente {user_id} con {len(conversations)} conversazioni")
                    break
    
    if not real_user_id:
        print("❌ Nessun utente con conversazioni trovato. Crea prima alcune conversazioni nell'app.")
        return
    
    print(f"\n🧪 Test coda DeepSeek con utente reale: {real_user_id}")
    print("="*60)
    
    # Inizializza manager
    manager = DeepSeekManager()
    
    if not manager.is_available():
        print("❌ DeepSeek non disponibile. Verifica la chiave API nel file .env")
        return
    
    print("✅ DeepSeek disponibile")
    
    # Test: Invii rapidi consecutivi
    print(f"\n📱 Simulando 3 messaggi rapidi consecutivi...")
    
    user_info = {
        'età': 30,
        'sesso': 'Maschio',
        'peso': 70,
        'altezza': 170
    }
    
    for i in range(3):
        print(f"\n📝 Invio messaggio {i+1}/3")
        
        # Simula invio messaggio come fa l'app
        manager.check_and_extract_if_needed(
            user_id=real_user_id,
            user_data_manager=None,
            user_info=user_info,
            extraction_interval=1
        )
        
        # Mostra stato
        status = manager.get_extraction_status(real_user_id)
        print(f"   📊 Interazioni pendenti: {status['interactions_since_last']}")
        print(f"   🔄 Estrazione attiva: {status['extraction_in_progress']}")
        print(f"   📦 Coda: {status['queue_size']}")
        
        # Pausa molto breve per simulare invii rapidi
        time.sleep(0.2)
    
    # Monitora fino a che la coda si svuota (max 2 minuti)
    print(f"\n🔍 Monitoraggio fino a coda vuota (timeout: 2 min)...")
    
    max_seconds = 120  # 2 minuti completi
    
    for i in range(max_seconds):
        status = manager.get_extraction_status(real_user_id)
        queue_size = status['queue_size']
        extraction_active = status['extraction_in_progress']
        
        # Mostra status se c'è attività
        if queue_size > 0 or extraction_active:
            print(f"   ⏱️  {i+1:3d}s - Coda: {queue_size}, Estrazione: {'🔄' if extraction_active else '⏸️'}")
        
        # Processa risultati
        manager.check_and_process_results()
        
        # Controlla se tutto è finito
        if queue_size == 0 and not extraction_active:
            print(f"   🎉 Coda svuotata dopo {i+1} secondi!")
            break
            
        time.sleep(1)
    else:
        # Se usciamo dal loop senza break, è timeout
        print(f"   ⏰ Timeout raggiunto dopo {max_seconds} secondi")
    
    # Report finale
    print(f"\n📊 RISULTATO FINALE:")
    final_status = manager.get_extraction_status(real_user_id)
    print(f"   📈 Interazioni totali: {final_status['interaction_count']}")
    print(f"   ✅ Interazioni processate: {final_status['last_extraction_count']}")
    print(f"   ⏳ Interazioni pendenti: {final_status['interactions_since_last']}")
    print(f"   📦 Coda finale: {final_status['queue_size']}")
    
    if final_status['queue_size'] == 0 and not final_status['extraction_in_progress']:
        print(f"\n🎉 SUCCESSO: Tutte le richieste sono state processate!")
    elif final_status['queue_size'] > 0:
        print(f"\n⚠️  {final_status['queue_size']} richieste ancora in coda")
    elif final_status['extraction_in_progress']:
        print(f"\n⏳ Estrazione ancora in corso...")

if __name__ == "__main__":
    test_with_real_user() 