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
UTENTE: Mi rigeneri anche i giorni dal 5 al 7

AGENTE: 🗓️ GIORNO 5 - VENERDÌ

🌅 COLAZIONE
• Pane integrale: 80 g → 🍞 2 fette grandi (Sostituti: 40 g cracker, 70 g pan bauletto)
• Uova: 60 g → 🥚 1 uovo grande (Sostituti: 20 g grana padano, 40 g ali di pollo)
• Marmellata: 40 g → 🥄 2 cucchiai abbondanti (Sostituti: 30 g miele, 190 g marmellata Hero light)
• Mandorle: 20 g → 🥜 15-18 mandorle (Sostituti: 20 g burro d’arachidi, 20 g nocciole)
• Arancia: 190 g → 🍊 1 arancia grande (Sostituti: 90 g banana, 140 g mirtilli)

🍽️ PRANZO
• Riso basmati: 120 g → 🍚 1 tazza grande (Sostituti: 130 g riso integrale, 160 g pane bianco)
• Tonno al naturale: 70 g → 🐟 1 scatoletta media (Sostituti: 70 g petto di pollo, 50 g salmone affumicato)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Zucchine: 100 g → 🥒 mezza zucchina grande (Sostituti: 60 g cavolfiore, 40 g asparagi)
• Carote: 110 g → 🥕 1-2 carote medie (Sostituti: 200 g pomodoro, 210 g insalata)

🥨 SPUNTINO POMERIDIANO
• Yogurt magro: 200 g → 🥛 1 vasetto abbondante (Sostituti: 160 g yogurt greco 0%, 120 g yogurt greco 2%)
• Kiwi: 190 g → 🥝 2 kiwi grandi (Sostituti: 190 g lamponi, 250 g arancia)
• Nocciole: 10 g → 🥜 8-9 nocciole (Sostituti: 10 g noci sgusciate, 10 g mandorle)

🌙 CENA
• Pasta integrale: 120 g → 🍝 1 porzione abbondante (Sostituti: 180 g pane integrale, 110 g farro)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Melanzane: 250 g → 🍆 1 melanzana grande (Sostituti: 260 g insalata, 250 g pomodoro)
• Pomodori: 250 g → 🍅 2-3 pomodori grandi (Sostituti: 260 g insalata, 140 g carote)

🗓️ GIORNO 6 - SABATO

🌅 COLAZIONE
• Pane integrale: 80 g → 🍞 2 fette grandi (Sostituti: 40 g cracker, 70 g pan bauletto)
• Uova: 60 g → 🥚 1 uovo grande (Sostituti: 20 g grana padano, 40 g ali di pollo)
• Marmellata: 40 g → 🥄 2 cucchiai abbondanti (Sostituti: 30 g miele, 190 g marmellata Hero light)
• Mandorle: 20 g → 🥜 15-18 mandorle (Sostituti: 20 g burro d’arachidi, 20 g nocciole)
• Arancia: 190 g → 🍊 1 arancia grande (Sostituti: 90 g banana, 140 g mirtilli)

🍽️ PRANZO
• Riso basmati: 120 g → 🍚 1 tazza grande (Sostituti: 130 g riso integrale, 160 g pane bianco)
• Tonno al naturale: 70 g → 🐟 1 scatoletta media (Sostituti: 70 g petto di pollo, 50 g salmone affumicato)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Zucchine: 100 g → 🥒 mezza zucchina grande (Sostituti: 60 g cavolfiore, 40 g asparagi)
• Carote: 110 g → 🥕 1-2 carote medie (Sostituti: 200 g pomodoro, 210 g insalata)

🥨 SPUNTINO POMERIDIANO
• Yogurt magro: 200 g → 🥛 1 vasetto abbondante (Sostituti: 160 g yogurt greco 0%, 120 g yogurt greco 2%)
• Kiwi: 190 g → 🥝 2 kiwi grandi (Sostituti: 190 g lamponi, 250 g arancia)
• Nocciole: 10 g → 🥜 8-9 nocciole (Sostituti: 10 g noci sgusciate, 10 g mandorle)

🌙 CENA
• Pasta integrale: 120 g → 🍝 1 porzione abbondante (Sostituti: 180 g pane integrale, 110 g farro)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Melanzane: 250 g → 🍆 1 melanzana grande (Sostituti: 260 g insalata, 250 g pomodoro)
• Pomodori: 250 g → 🍅 2-3 pomodori grandi (Sostituti: 260 g insalata, 140 g carote)

🗓️ GIORNO 7 - DOMENICA

🌅 COLAZIONE
• Pane integrale: 80 g → 🍞 2 fette grandi (Sostituti: 40 g cracker, 70 g pan bauletto)
• Uova: 60 g → 🥚 1 uovo grande (Sostituti: 20 g grana padano, 40 g ali di pollo)
• Marmellata: 40 g → 🥄 2 cucchiai abbondanti (Sostituti: 30 g miele, 190 g marmellata Hero light)
• Mandorle: 20 g → 🥜 15-18 mandorle (Sostituti: 20 g burro d’arachidi, 20 g nocciole)
• Arancia: 190 g → 🍊 1 arancia grande (Sostituti: 90 g banana, 140 g mirtilli)

🍽️ PRANZO
• Riso basmati: 120 g → 🍚 1 tazza grande (Sostituti: 130 g riso integrale, 160 g pane bianco)
• Tonno al naturale: 70 g → 🐟 1 scatoletta media (Sostituti: 70 g petto di pollo, 50 g salmone affumicato)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Zucchine: 100 g → 🥒 mezza zucchina grande (Sostituti: 60 g cavolfiore, 40 g asparagi)
• Carote: 110 g → 🥕 1-2 carote medie (Sostituti: 200 g pomodoro, 210 g insalata)

🥨 SPUNTINO POMERIDIANO
• Yogurt magro: 200 g → 🥛 1 vasetto abbondante (Sostituti: 160 g yogurt greco 0%, 120 g yogurt greco 2%)
• Kiwi: 190 g → 🥝 2 kiwi grandi (Sostituti: 190 g lamponi, 250 g arancia)
• Nocciole: 10 g → 🥜 8-9 nocciole (Sostituti: 10 g noci sgusciate, 10 g mandorle)

🌙 CENA
• Pasta integrale: 120 g → 🍝 1 porzione abbondante (Sostituti: 180 g pane integrale, 110 g farro)
• Olio extravergine di oliva: 20 g → 🥄 2 cucchiai (Sostituti: 20 g burro, 80 g avocado)
• Melanzane: 250 g → 🍆 1 melanzana grande (Sostituti: 260 g insalata, 250 g pomodoro)
• Pomodori: 250 g → 🍅 2-3 pomodori grandi (Sostituti: 260 g insalata, 140 g carote)

📚 Fonti utilizzate:

Banca dati CREA per la composizione degli alimenti
Ottimizzazione porzioni, sostituti e target nutrizionali secondo le linee guida SINU e standard internazionali
➡️ Conclusione:
Tutti i pasti dei giorni 5-7 sono stati generati con porzioni, misure casalinghe e sostituti per ogni alimento. Vuoi aggiungere ricette dettagliate, preferenze o chiarimenti su qualche giorno/pasto?
Hai domande sui valori nutrizionali o vuoi suggerimenti pratici per la preparazione?
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