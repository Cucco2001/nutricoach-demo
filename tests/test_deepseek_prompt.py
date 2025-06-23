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
UTENTE: Puoi calcolare il mio fabbisogno calorico?

AGENTE: Certo! Basandomi sui tuoi dati:
- Età: 25 anni
- Sesso: Femmina
- Peso: 60 kg
- Altezza: 165 cm
- Obiettivo: Perdita di peso

Calcolo del metabolismo basale (BMR) con formula Harris-Benedict:
BMR = 655 + (9.6 × 60) + (1.8 × 165) - (4.7 × 25) = 1.425 kcal

Il tuo fabbisogno base considerando uno stile di vita sedentario (LAF 1.2) è:
Fabbisogno base = 1.425 × 1.2 = 1.710 kcal/giorno

Per la perdita di peso, applico un deficit calorico del 15%:
Aggiustamento obiettivo = -256 kcal

Fabbisogno finale = 1.710 - 256 = 1.454 kcal/giorno

I tuoi macronutrienti dovrebbero essere:
- Proteine: 87g (348 kcal, 24%)
- Carboidrati: 145g (580 kcal, 40%) 
- Grassi: 58g (522 kcal, 36%)
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