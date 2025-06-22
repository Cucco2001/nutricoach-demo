#!/usr/bin/env python3
"""
Test script per verificare la gestione della coda DeepSeek.
Simula più messaggi consecutivi per testare il sistema di accodamento.
"""

import time
import threading
from services.deep_seek_service.deepseek_manager import DeepSeekManager

def simulate_user_interactions(manager, user_id, num_interactions=5):
    """
    Simula una serie di interazioni utente consecutive.
    
    Args:
        manager: DeepSeekManager instance
        user_id: ID dell'utente
        num_interactions: Numero di interazioni da simulare
    """
    print(f"\n🚀 Avvio test per utente {user_id} con {num_interactions} interazioni consecutive")
    
    user_info = {
        'età': 30,
        'sesso': 'Maschio', 
        'peso': 70,
        'altezza': 170,
        'attività': 'Sedentario',
        'obiettivo': 'Mantenimento'
    }
    
    for i in range(num_interactions):
        print(f"\n📝 Interazione {i+1}/{num_interactions} per utente {user_id}")
        
        # Simula l'aggiunta di una conversazione al file utente
        # (normalmente fatto dal sistema di chat)
        
        # Chiama il manager come farebbe l'app
        manager.check_and_extract_if_needed(
            user_id=user_id,
            user_data_manager=None,  # Ora non serve più
            user_info=user_info,
            extraction_interval=1  # Estrazione ad ogni interazione per test
        )
        
        # Mostra stato attuale
        status = manager.get_extraction_status(user_id)
        print(f"   📊 Stato: {status['interactions_since_last']} interazioni in coda")
        print(f"   🔄 Estrazione in corso: {status['extraction_in_progress']}")
        print(f"   📦 Dimensione coda globale: {status['queue_size']}")
        
        # Breve pausa tra le interazioni
        time.sleep(0.5)
    
    print(f"\n✅ Completate tutte le {num_interactions} interazioni per utente {user_id}")

def monitor_queue(manager, duration=30):
    """
    Monitora lo stato della coda per un certo periodo.
    
    Args:
        manager: DeepSeekManager instance
        duration: Durata del monitoraggio in secondi
    """
    print(f"\n🔍 Avvio monitoraggio coda per {duration} secondi...")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            # Controlla se ci sono richieste in coda
            queue_size = manager.queue.qsize()
            active_extractions = len([t for t in threading.enumerate() 
                                    if t.name.startswith("DeepSeekExtraction-")])
            
            if queue_size > 0 or active_extractions > 0:
                print(f"   ⏱️  {time.strftime('%H:%M:%S')} - Coda: {queue_size}, Thread attivi: {active_extractions}")
            
            # Processa risultati se disponibili
            manager.check_and_process_results()
            
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoraggio interrotto")
            break
    
    print(f"\n📊 Monitoraggio completato")

def test_queue_system():
    """Test principale del sistema di coda."""
    print("=" * 60)
    print("🧪 TEST SISTEMA CODA DEEPSEEK")
    print("=" * 60)
    
    # Inizializza il manager
    manager = DeepSeekManager()
    
    if not manager.is_available():
        print("❌ DeepSeek non disponibile. Controlla la chiave API nel file .env")
        return
    
    print("✅ DeepSeek disponibile, avvio test...")
    
    # Test 1: Utente singolo con messaggi consecutivi
    print("\n" + "="*40)
    print("TEST 1: Messaggi consecutivi - Utente singolo")
    print("="*40)
    
    user_id = "test_user_queue_001"
    
    # Avvia monitoraggio in thread separato
    monitor_thread = threading.Thread(
        target=monitor_queue, 
        args=(manager, 20),
        daemon=True
    )
    monitor_thread.start()
    
    # Simula interazioni consecutive
    simulate_user_interactions(manager, user_id, 3)
    
    # Test 2: Utenti multipli simultanei
    print("\n" + "="*40)
    print("TEST 2: Utenti multipli simultanei")
    print("="*40)
    
    user_threads = []
    for i in range(2):
        user_id = f"test_user_multi_{i+1:03d}"
        thread = threading.Thread(
            target=simulate_user_interactions,
            args=(manager, user_id, 2),
            daemon=True
        )
        user_threads.append(thread)
        thread.start()
        time.sleep(1)  # Sfasa leggermente gli avvii
    
    # Attendi completion dei thread utente
    for thread in user_threads:
        thread.join()
    
    # Attendi che la coda si svuoti
    print("\n⏳ Attendo svuotamento coda...")
    timeout = 30
    start_wait = time.time()
    
    while manager.queue.qsize() > 0 and (time.time() - start_wait) < timeout:
        print(f"   📦 Richieste in coda: {manager.queue.qsize()}")
        time.sleep(2)
    
    # Report finale
    print("\n" + "="*40)
    print("📊 REPORT FINALE")
    print("="*40)
    
    for user_id in [f"test_user_queue_001"] + [f"test_user_multi_{i+1:03d}" for i in range(2)]:
        status = manager.get_extraction_status(user_id)
        print(f"👤 {user_id}:")
        print(f"   Interazioni totali: {status['interaction_count']}")
        print(f"   Interazioni processate: {status['last_extraction_count']}")
        print(f"   Interazioni pendenti: {status['interactions_since_last']}")
        print(f"   Estrazione in corso: {status['extraction_in_progress']}")
    
    print(f"\n📦 Coda finale: {manager.queue.qsize()} richieste")
    print(f"🔧 Thread attivi: {len([t for t in threading.enumerate() if t.name.startswith('DeepSeekExtraction-')])}")
    
    if manager.queue.qsize() == 0:
        print("\n✅ TEST COMPLETATO: Tutte le richieste sono state processate!")
    else:
        print(f"\n⚠️  TEST PARZIALE: {manager.queue.qsize()} richieste ancora in coda")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_queue_system() 