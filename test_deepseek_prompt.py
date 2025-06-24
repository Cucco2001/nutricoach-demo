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
UTENTE: Procedi

AGENTE: ✓ FASE 6 - CONTROLLO ALIMENTI ULTRAPROCESSATI\n\n⚡ Sto elaborando: Analisi della presenza di alimenti ultraprocessati (NOVA 4) nella tua giornata alimentare, per garantire che non superino la soglia raccomandata.\n\nSpiegazione semplice:\n- Gli alimenti ultraprocessati sono prodotti industriali con ingredienti e additivi difficili da trovare nelle cucine domestiche. Mangiarne troppi può essere poco salutare per il benessere a lungo termine.\n- Le più recenti linee guida scientifiche consigliano di limitare questi alimenti a meno del 10% delle calorie totali.\n\n📊 Risultati intermedi:\n- Unico alimento ultraprocessato rilevato: Biscotti secchi\n- Percentuale ultraprocessati: 1.8% del peso totale della dieta giornaliera (~30g su 1650g)\n- Limite massimo (10%) non superato: la dieta è ampiamente nei limiti e salutare sotto questo aspetto\n\n📚 Fonti utilizzate:\n- Studio NOVA sugli alimenti ultraprocessati\n- Banca dati CREA (per classificazione ingredienti)\n- Letteratura internazionale sulle linee guida prevenzione (Monteiro et al., 2019)\n\n➡️ Conclusione: I biscotti secchi sono l’unico ultraprocessato, ma la quantità è minima (molto al di sotto della soglia critica). La tua alimentazione è ottimale anche sotto questo punto di vista!\n\nVuoi vedere subito la dieta settimanale personalizzata (giorni 1-4) in FASE 7, oppure hai altre richieste o domande su questa giornata?",
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