#!/usr/bin/env python3
"""
Test interattivo per DeepSeek - Inserisci il tuo prompt e vedere il JSON estratto.

Questo script ti permette di testare rapidamente l'estrazione di dati nutrizionali
inserendo manualmente una conversazione e vedendo il risultato JSON.
"""

import json
import sys
from services.deep_seek_service.deepseek_client import DeepSeekClient

def test_deepseek_extraction():
    """
    Test interattivo per l'estrazione di dati nutrizionali con DeepSeek.
    """
    print("🧪 Test DeepSeek - Estrazione Dati Nutrizionali")
    print("=" * 60)
    
    # Inizializza il client DeepSeek
    client = DeepSeekClient()
    
    # Verifica disponibilità
    if not client.is_available():
        print("❌ DeepSeek non disponibile!")
        print("   Verifica che DEEPSEEK_API_KEY sia impostata nel file .env")
        return
    
    print("✅ DeepSeek disponibile")
    print()
    
    # Dati utente di esempio (puoi modificarli)
    user_info = {
        'età': 30,
        'sesso': 'Maschio',
        'peso': 70,
        'altezza': 175,
        'obiettivo': 'Mantenimento'
    }
    
    print("👤 Informazioni utente utilizzate:")
    for key, value in user_info.items():
        print(f"   {key}: {value}")
    print()
    
    # Input della conversazione
    print("💬 Inserisci la conversazione da testare:")
    print("   Format: UTENTE: domanda")
    print("           AGENTE: risposta")
    print("   (Premi CTRL+D o CTRL+Z per terminare l'input)")
    print()
    
    # Raccogli input multi-riga
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    if not lines:
        print("❌ Nessuna conversazione inserita.")
        return
    
    conversation_text = "\n".join(lines)
    print(f"\n📝 Conversazione inserita ({len(lines)} righe):")
    print("-" * 40)
    print(conversation_text)
    print("-" * 40)
    
    # Simula conversation_history nel formato richiesto
    # Per semplicità, creo una singola interazione con tutto il testo
    conversation_history = [
        {
            'question': 'Test conversazione',
            'answer': conversation_text
        }
    ]
    
    print("\n🚀 Avvio estrazione DeepSeek...")
    
    try:
        # Chiama DeepSeek per l'estrazione
        extracted_data = client.extract_nutritional_data(
            conversation_history=conversation_history,
            user_info=user_info,
            max_retries=3
        )
        
        print("\n✅ Estrazione completata!")
        print("=" * 60)
        
        if extracted_data:
            print("📊 DATI ESTRATTI (JSON):")
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
            
            print(f"\n📈 SUMMARY:")
            print(f"   Sezioni trovate: {list(extracted_data.keys())}")
            
            # Mostra dettagli per sezione
            for section, data in extracted_data.items():
                if isinstance(data, dict):
                    print(f"   {section}: {len(data)} campi")
                elif isinstance(data, list):
                    print(f"   {section}: {len(data)} elementi")
                else:
                    print(f"   {section}: {type(data).__name__}")
        else:
            print("⚠️  Nessun dato estratto (JSON vuoto)")
            
    except Exception as e:
        print(f"\n❌ Errore durante l'estrazione:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

def test_with_predefined_examples():
    """
    Testa con esempi predefiniti invece di input manuale.
    """
    print("🧪 Test DeepSeek - Esempi Predefiniti")
    print("=" * 60)
    
    client = DeepSeekClient()
    
    if not client.is_available():
        print("❌ DeepSeek non disponibile!")
        return
    
    user_info = {
        'età': 25,
        'sesso': 'Femmina',
        'peso': 60,
        'altezza': 165,
        'obiettivo': 'Perdita di peso'
    }
    
    # Esempio di conversazione con calcoli calorici
    example_conversation = """
UTENTE: Mi cambi cena g 3

AGENTE: 🌙 CENA (Giorno 3) – Pasta, asparagi e carote

• Pasta integrale: 120g (peso a crudo) → 🍝 1 porzione abbondante
P: 16g, C: 78g, G: 2.6g
Sostituti: 110g farro, 120g pasta di semola

• Asparagi: 190g → 🥗 1 piatto colmo di asparagi lessati o saltati
P: 8.7g, C: 7.6g, G: 0.2g
Sostituti: 250g cavolfiore, 220g spinaci

• Carote: 180g → 🥕 2 carote grandi
P: 2.0g, C: 13.7g, G: 0.4g
Sostituti: 320g pomodoro, 320g melanzane

• Olio extravergine di oliva: 20g → 🫒 2 cucchiai
P: 0g, C: 0g, G: 20g
Sostituti: 20g burro, 80g avocado

Totale pasto: P: circa 27g, C: circa 99g, G: circa 23g — circa 726 kcal

Idea ricetta: Cuoci la pasta integrale. Nel frattempo, salta in padella gli asparagi tagliati a rondelle e le carote a julienne con un cucchiaio di olio e un po' di acqua. Unisci la pasta scolata, aggiungi il resto dell’olio a crudo e mescola bene, aggiungendo erbe aromatiche a piacere.

📚 Fonti utilizzate:

Banca dati CREA (valori nutrizionali alimenti)
Ottimizzazione automatica porzioni e sostituti
➡️ Conclusione: Cena vegetariana gustosa, ricca di fibre, vitamine e gusto! Va bene così o vuoi modifiche/integrazioni? Posso procedere con la generazione della dieta dei giorni 5-7?
"""
    
    conversation_history = [
        {
            'question': 'Puoi calcolare il mio fabbisogno calorico?',
            'answer': example_conversation.split('AGENTE: ')[1]
        }
    ]
    
    print("💬 Testando con conversazione di esempio...")
    
    try:
        extracted_data = client.extract_nutritional_data(
            conversation_history=conversation_history,
            user_info=user_info
        )
        
        print("\n✅ Estrazione completata!")
        print("📊 DATI ESTRATTI:")
        print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Errore: {str(e)}")

if __name__ == "__main__":
    print("Scegli modalità di test:")
    print("1. Input manuale (inserisci la tua conversazione)")
    print("2. Esempio predefinito")
    
    choice = input("Scelta (1 o 2): ").strip()
    
    if choice == "1":
        test_deepseek_extraction()
    elif choice == "2":
        test_with_predefined_examples()
    else:
        print("Scelta non valida. Uso modalità input manuale.")
        test_deepseek_extraction() 