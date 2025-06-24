#!/usr/bin/env python3
"""
Test specifico per verificare l'estrazione dei pasti (registered_meals).
"""

import json
from services.deep_seek_service.deepseek_client import DeepSeekClient

def test_meal_extraction():
    """
    Testa l'estrazione di un pasto specifico.
    """
    print("🧪 Test DeepSeek - Estrazione Pasti")
    print("=" * 60)
    
    client = DeepSeekClient()
    
    if not client.is_available():
        print("❌ DeepSeek non disponibile!")
        return
    
    # Conversazione con un pasto del GIORNO 1 (dovrebbe andare in registered_meals)
    conversation_with_meal = [
        {
            "question": "procedi",
            "answer": """🌅 COLAZIONE (550 kcal)

• **Pane integrale**: 80 g → 🥖 2 fette grandi (Sostituti: 40 g di cracker, 70 g di pan bauletto)  
  P: 6.8 g, C: 35.3 g, G: 1.0 g

• **Yogurt magro**: 150 g → 🥣 1 vasetto grande (Sostituti: 120 g di yogurt greco 0%, 90 g di yogurt greco 2%)  
  P: 6.5 g, C: 8.4 g, G: 0.1 g

• **Miele**: 40 g → 🍯 poco più di 2 cucchiai (Sostituti: 50 g di marmellata)  
  P: 0.2 g, C: 32.1 g, G: 0.0 g

• **Mandorle**: 30 g → 🥜 1 manciata abbondante (Sostituti: 30 g di burro di arachidi, 30 g di nocciole)  
  P: 6.6 g, C: 1.4 g, G: 16.6 g

Totale pasto: P: 20 g, C: 77 g, G: 18 g

💡 Idea ricetta:  
Tosta le fette di pane integrale e spalma sopra il miele, accompagnando il tutto con uno yogurt magro ben freddo."""
        }
    ]
    
    # Conversazione con un GIORNO 2 (dovrebbe andare in weekly_diet)
    conversation_with_day2 = [
        {
            "question": "procedi", 
            "answer": """🗓️ **GIORNO 2 - MARTEDÌ**

🌅 **COLAZIONE**
• Pane integrale: 130 g → 🥖 3 fette grandi  
• Burro di arachidi: 30 g → 🥄 2 cucchiaini colmi  
• Marmellata: 40 g → 🍯 2 cucchiai abbondanti  

🍽️ **PRANZO**
• Riso basmati: 140 g → 🍚 1 porzione abbondante cotta  
• Zucchine: 160 g → 🥒 1 ciotola media cotta  
• Olio di oliva: 20 g → 🥄 2 cucchiai"""
        }
    ]
    
    user_info = {
        "età": 30,
        "sesso": "Maschio",
        "peso": 70,
        "altezza": 170,
        "obiettivo": "Mantenimento"
    }
    
    # Test 1: Estrazione pasto giorno 1
    print("\n📤 Test 1: Estrazione COLAZIONE (dovrebbe andare in registered_meals)...")
    result1 = client.extract_nutritional_data(conversation_with_meal, user_info)
    
    print("\n📊 Risultato Test 1:")
    if result1 and "extracted_data" in result1:
        extracted = result1["extracted_data"]
        print(json.dumps(extracted, indent=2, ensure_ascii=False))
        
        # Verifica presenza registered_meals
        if "registered_meals" in extracted:
            print("\n✅ registered_meals trovato!")
            print(f"   Numero pasti: {len(extracted['registered_meals'])}")
        else:
            print("\n❌ registered_meals NON trovato!")
    
    # Test 2: Estrazione giorno 2
    print("\n\n📤 Test 2: Estrazione GIORNO 2 (dovrebbe andare in weekly_diet)...")
    result2 = client.extract_nutritional_data(conversation_with_day2, user_info)
    
    print("\n📊 Risultato Test 2:")
    if result2 and "extracted_data" in result2:
        extracted = result2["extracted_data"]
        print(json.dumps(extracted, indent=2, ensure_ascii=False))
        
        # Verifica presenza weekly_diet
        if "weekly_diet" in extracted:
            print("\n✅ weekly_diet trovato!")
            print(f"   Giorni presenti: {list(extracted['weekly_diet'].keys())}")
        else:
            print("\n❌ weekly_diet NON trovato!")

if __name__ == "__main__":
    test_meal_extraction() 