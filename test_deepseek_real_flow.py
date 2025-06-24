#!/usr/bin/env python3
"""
Test che simula il flusso REALE di DeepSeek nell'applicazione.

Questo test segue esattamente il percorso che i dati fanno nel flusso normale:
1. chat_interface.py chiama save_agent_qa 
2. chat_interface.py chiama check_and_extract_if_needed
3. DeepSeekManager mette in coda le conversazioni individualmente
4. extraction_service processa ogni conversazione
"""

import json
import time
from pathlib import Path
from services.deep_seek_service.deepseek_manager import DeepSeekManager
from services.deep_seek_service.deepseek_client import DeepSeekClient

def simulate_real_flow():
    """
    Simula il flusso reale dell'applicazione con due conversazioni consecutive per testare la race condition.
    """
    print("🧪 Test DeepSeek - Simulazione Flusso Reale (2 conversazioni)")
    print("=" * 60)
    
    # Crea un user_id di test
    user_id = f"test_user_{int(time.time())}"
    user_file_path = f"user_data/{user_id}.json"
    
    # Crea un file utente di test con DUE conversazioni
    test_user_data = {
        "nutritional_info": {
            "age": 25,
            "weight": 70,
            "height": 175,
            "activity_level": "sedentary",
            "gender": "male",
            "agent_qa": [
                {
                    "question": "procedi",
                    "answer": """✓ FASE 2 - CALCOLO DEL FABBISOGNO ENERGETICO

⚡ Sto elaborando: Calcolo del metabolismo basale e del fabbisogno energetico totale.

📊 Risultati intermedi:
- Metabolismo basale (BMR): 1672 kcal/giorno
- Livello di attività fisica considerato (LAF): 1.3 (sedentario)
- Fabbisogno energetico totale: 1672 * 1.3 = 2173 kcal/giorno
- Calorie extra da sport: 0 kcal

Kcal totali giornaliere consigliate per mantenimento: 2173 kcal

📚 Fonti utilizzate:
- Formula Harris-Benedict per calcolo metabolismo basale

➡️ Conclusione: Per mantenere il peso attuale, il tuo fabbisogno energetico è di circa 2170 kcal al giorno.""",
                    "timestamp": "2025-01-01T10:00:00"
                },
                {
                    "question": "continua con la dieta",
                    "answer": """🌅 COLAZIONE (550 kcal)

• **Pane integrale**: 80 g → 🥖 2 fette grandi (Sostituti: 40 g di cracker, 70 g di pan bauletto)  
  P: 6.8 g | C: 37.6 g | G: 2.4 g | Kcal: 201

• **Prosciutto cotto**: 40 g → 🥩 2 fette (Sostituti: 30 g di bresaola, 40 g di tacchino)  
  P: 7.6 g | C: 0.4 g | G: 1.2 g | Kcal: 42

• **Caffè**: 200 ml → ☕ 1 tazza  
  P: 0.2 g | C: 0 g | G: 0 g | Kcal: 2

**TOTALI COLAZIONE**: P: 14.6 g | C: 38.0 g | G: 3.6 g | **Kcal: 245**""",
                    "timestamp": "2025-01-01T10:05:00"
                }
            ]
        }
    }
    
    # Salva il file di test
    with open(user_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_user_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Creato file utente di test: {user_file_path}")
    
    # Inizializza DeepSeek Manager
    manager = DeepSeekManager()
    
    if not manager.is_available():
        print("❌ DeepSeek non disponibile!")
        return
    
    print("✅ DeepSeek disponibile")
    
    try:
        print(f"\n🔄 Simulazione chiamata da chat_interface.py...")
        print(f"   - user_id: {user_id}")
        print(f"   - conversazioni totali: 2")
        
        # Prima chiamata - simula conversazione 9 (indice 0)
        manager.check_and_extract_if_needed(
            user_id=user_id,
            user_data_manager=None,
            user_info=test_user_data["nutritional_info"],
            extraction_interval=1
        )
        
        # Aspetta un po' per far partire la prima estrazione
        time.sleep(0.5)
        
        # Aggiungi una terza conversazione al file (simula invio rapido del secondo messaggio)
        test_user_data["nutritional_info"]["agent_qa"].append({
            "question": "continua",
            "answer": """🗓️ **GIORNO 2 - MERCOLEDÌ**

🌅 **COLAZIONE** (550 kcal)
• **Latte parzialmente scremato**: 200 ml
• **Cereali integrali**: 40 g
• **Banana**: 150 g

🍽️ **PRANZO** (700 kcal)
• **Pasta integrale**: 80 g
• **Pomodori pelati**: 200 g
• **Olio extravergine**: 10 ml""",
            "timestamp": "2025-01-01T10:06:00"
        })
        
        # Risalva il file con la terza conversazione
        with open(user_file_path, 'w', encoding='utf-8') as f:
            json.dump(test_user_data, f, indent=2, ensure_ascii=False)
        
        # Seconda chiamata - simula conversazione 10 (indice 2) invio quasi contemporaneo
        manager.check_and_extract_if_needed(
            user_id=user_id,
            user_data_manager=None,
            user_info=test_user_data["nutritional_info"],
            extraction_interval=1
        )
        
        print(f"\n⏳ Attendo l'estrazione DeepSeek...")
        
        # Monitora lo stato per vedere se entrambe le conversazioni vengono processate
        max_wait = 30
        for i in range(max_wait):
            time.sleep(1)
            status = manager.get_extraction_status(user_id)
            print(f"   Status ({i+1}s): {status}")
            
            # Se l'estrazione è finita e non ci sono più conversazioni in coda
            if not status["extraction_in_progress"] and status["user_conversations_in_queue"] == 0:
                print(f"\n✅ Tutte le estrazioni completate!")
                break
        else:
            print(f"\n⚠️ Timeout dopo {max_wait} secondi")
        
        # Controlla se tutte le conversazioni sono state processate
        status = manager.get_extraction_status(user_id)
        print(f"\n📊 Status finale: {status}")
        
        # L'indice dell'ultima conversazione processata dovrebbe essere 2 (terza conversazione, indice 2)
        if status["last_processed_conversation_index"] == 2:
            print("✅ SUCCESSO: Tutte e tre le conversazioni sono state processate!")
        else:
            print(f"❌ PROBLEMA: Solo processate fino all'indice {status['last_processed_conversation_index']}, doveva essere 2")
        
        # Controlla i risultati
        print(f"\n📊 Controllo risultati...")
        if Path(user_file_path).exists():
            with open(user_file_path, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
            
            if "nutritional_info_extracted" in final_data:
                print("✅ Dati estratti trovati!")
                extracted = final_data["nutritional_info_extracted"]
                print(json.dumps(extracted, indent=2, ensure_ascii=False))
            else:
                print("❌ Nessun dato estratto trovato!")
        
    finally:
        # Pulizia
        if Path(user_file_path).exists():
            Path(user_file_path).unlink()
            print(f"\n🧹 File di test rimosso: {user_file_path}")

def test_direct_client():
    """
    Test diretto del DeepSeekClient per confronto.
    """
    print(f"\n\n🧪 Test Diretto DeepSeekClient")
    print("=" * 60)
    
    client = DeepSeekClient()
    
    if not client.is_available():
        print("❌ DeepSeek non disponibile!")
        return
    
    print("📤 Chiamata diretta a DeepSeek...")
    
    # Conversazione con dati calorici 
    conversation = [
        {
            "question": "procedi",
            "answer": """✓ FASE 2 - CALCOLO DEL FABBISOGNO ENERGETICO

⚡ Sto elaborando: Calcolo del metabolismo basale e del fabbisogno energetico totale.

📊 Risultati intermedi:
- Metabolismo basale (BMR): 1672 kcal/giorno
- Livello di attività fisica considerato (LAF): 1.3 (sedentario)
- Fabbisogno energetico totale: 1672 * 1.3 = 2173 kcal/giorno
- Calorie extra da sport: 0 kcal

Kcal totali giornaliere consigliate per mantenimento: 2173 kcal

📚 Fonti utilizzate:
- Formula Harris-Benedict per calcolo metabolismo basale

➡️ Conclusione: Per mantenere il peso attuale, il tuo fabbisogno energetico è di circa 2170 kcal al giorno."""
        }
    ]
    
    user_info = {
        "age": 25,
        "weight": 70,
        "height": 175,
        "activity_level": "sedentary",
        "gender": "male"
    }
    
    result = client.extract_nutritional_data(conversation, user_info)
    
    print(f"\n📊 Risultato diretto:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    simulate_real_flow()
    test_direct_client() 