"""
Test file per la feature di aggiunta automatica dell'olio.

Questo file testa specificamente la funzione che aggiunge automaticamente
olio d'oliva ai pasti di pranzo e cena quando può migliorare l'ottimizzazione.
"""

import sys
import os
import json
import streamlit as st
from typing import Dict, List

# Aggiungi il path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import optimize_meal_portions

def setup_test_environment():
    """Configura l'ambiente di test simulando Streamlit session_state e dati utente."""
    
    # Simula session_state di Streamlit
    if not hasattr(st, 'session_state'):
        class MockSessionState:
            def __init__(self):
                self.user_info = {
                    "id": "test_user_001",
                }
        st.session_state = MockSessionState()
    else:
        st.session_state.user_info = {
            "id": "test_user_001",
        }
    
    # Crea directory user_data se non esiste
    os.makedirs("user_data", exist_ok=True)
    
    # Crea un file utente di test con dati nutrizionali completi
    test_user_data = {
        "personal_info": {
            "nome": "Mario",
            "età": 30,
            "sesso": "maschio",
            "peso": 75,
            "altezza": 175,
            "obiettivo": "Mantenimento"
        },
        "nutritional_info_extracted": {
            "daily_macros": {
                "kcal_totali": 2400,
                "proteine_g_totali": 120,
                "carboidrati_g_totali": 300,
                "grassi_g_totali": 80,
                "distribuzione_pasti": {
                    "colazione": {
                        "kcal": 480,
                        "proteine_g": 24,
                        "carboidrati_g": 60,
                        "grassi_g": 16
                    },
                    "spuntino_mattutino": {
                        "kcal": 240,
                        "proteine_g": 12,
                        "carboidrati_g": 30,
                        "grassi_g": 8
                    },
                    "pranzo": {
                        "kcal": 720,
                        "proteine_g": 36,
                        "carboidrati_g": 90,
                        "grassi_g": 24
                    },
                    "spuntino_pomeridiano": {
                        "kcal": 240,
                        "proteine_g": 12,
                        "carboidrati_g": 30,
                        "grassi_g": 8
                    },
                    "cena": {
                        "kcal": 720,
                        "proteine_g": 36,
                        "carboidrati_g": 90,
                        "grassi_g": 24
                    }
                }
            }
        }
    }
    
    # Salva il file utente
    with open("user_data/test_user_001.json", 'w', encoding='utf-8') as f:
        json.dump(test_user_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Ambiente di test configurato per test olio automatico")

def test_oil_addition_case(case_number: int, meal_name: str, food_list: List[str], description: str):
    """Esegue un test case specifico per l'aggiunta automatica di olio."""
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST OLIO {case_number}: {description}")
    print(f"🍽️  Pasto: {meal_name}")
    print(f"🥘 Alimenti originali: {', '.join(food_list)}")
    print("="*80)
    
    try:
        result = optimize_meal_portions(meal_name, food_list)
        
        if result["success"]:
            oil_added = result.get("oil_added", False)
            
            if oil_added:
                print("🫒 OLIO AGGIUNTO AUTOMATICAMENTE! ✨")
                print(f"📋 Lista finale: {', '.join(result['foods_included'])}")
                
                # Estrai il miglioramento dal summary
                summary = result.get("optimization_summary", "")
                if "miglioramento:" in summary:
                    improvement_text = summary.split("miglioramento:")[1].strip(")")
                    print(f"📈 Miglioramento: {improvement_text}")
            else:
                print("🚫 Olio NON aggiunto")
                print("📋 Lista finale: identica a quella originale")
            
            print("\n📋 PORZIONI OTTIMIZZATE:")
            for food, grams in result["portions"].items():
                oil_indicator = " 🫒" if food == "olio_oliva" and oil_added else ""
                print(f"   • {food}: {grams}g{oil_indicator}")
            
            print("\n🎯 TARGET vs EFFETTIVI:")
            target = result["target_nutrients"]
            actual = result["actual_nutrients"]
            
            print(f"   🔥 Calorie:     {target['kcal']:.0f} → {actual['kcal']:.1f} kcal "
                  f"(errore: {result['errors']['kcal_error_pct']:.1f}%)")
            print(f"   🥩 Proteine:    {target['proteine_g']:.0f} → {actual['proteine_g']:.1f}g "
                  f"(errore: {result['errors']['proteine_g_error_pct']:.1f}%)")
            print(f"   🍞 Carboidrati: {target['carboidrati_g']:.0f} → {actual['carboidrati_g']:.1f}g "
                  f"(errore: {result['errors']['carboidrati_g_error_pct']:.1f}%)")
            print(f"   🥑 Grassi:      {target['grassi_g']:.0f} → {actual['grassi_g']:.1f}g "
                  f"(errore: {result['errors']['grassi_g_error_pct']:.1f}%)")
            
            # Calcola errore medio
            avg_error = sum([
                result['errors']['kcal_error_pct'],
                result['errors']['proteine_g_error_pct'],
                result['errors']['carboidrati_g_error_pct'],
                result['errors']['grassi_g_error_pct']
            ]) / 4
            
            print(f"\n📊 ERRORE MEDIO: {avg_error:.1f}%")
            
            # Valutazione qualitativa
            if avg_error < 5:
                print("🌟 OTTIMO - Molto vicino ai target!")
            elif avg_error < 10:
                print("👍 BUONO - Accettabile per la pratica")
            elif avg_error < 20:
                print("⚠️  DISCRETO - Potrebbe essere migliorato")
            else:
                print("❌ SCADENTE - Target molto lontani")
                
        else:
            print("❌ OTTIMIZZAZIONE FALLITA")
            print(f"Errore: {result['error_message']}")
    
    except Exception as e:
        print(f"💥 ERRORE DURANTE IL TEST: {str(e)}")

def run_oil_tests():
    """Esegue tutti i test per la feature di aggiunta automatica dell'olio."""
    
    print("🫒 AVVIO TEST SUITE AGGIUNTA AUTOMATICA OLIO")
    print("="*80)
    
    # Setup ambiente
    setup_test_environment()
    
    # Test cases specifici per l'olio
    test_cases = [
        {
            "meal_name": "pranzo",
            "food_list": ["pollo_petto", "riso"],  # Manca fonte di grassi
            "description": "Pranzo senza grassi - DOVREBBE aggiungere olio"
        },
        {
            "meal_name": "cena",
            "food_list": ["salmone_affumicato", "patate"],  # Pochi grassi
            "description": "Cena con pochi grassi - POTREBBE aggiungere olio"
        },
        {
            "meal_name": "pranzo",
            "food_list": ["pollo_petto", "riso", "olio_oliva"],  # Già con olio
            "description": "Pranzo già con olio - NON DOVREBBE aggiungere"
        },
        {
            "meal_name": "colazione",
            "food_list": ["yogurt_greco_0percento", "avena"],  # Colazione
            "description": "Colazione senza grassi - NON DOVREBBE aggiungere (non è pranzo/cena)"
        },
        {
            "meal_name": "cena",
            "food_list": ["uova", "verdure_miste", "patate"],  # Cena sbilanciata
            "description": "Cena vegetariana - POTREBBE aggiungere olio"
        },
        {
            "meal_name": "pranzo",
            "food_list": ["pasta_secca", "tonno_naturale"],  # Pasta senza grassi
            "description": "Pasta al tonno senza condimento - DOVREBBE aggiungere olio"
        },
        {
            "meal_name": "pranzo",
            "food_list": ["pollo_petto", "riso", "verdure_miste", "olio_oliva"],  # Già bilanciato
            "description": "Pranzo già bilanciato - NON DOVREBBE aggiungere"
        },
        {
            "meal_name": "cena",
            "food_list": ["pesce_spada", "quinoa"],  # Pesce magro + quinoa
            "description": "Cena con pesce magro - POTREBBE aggiungere olio"
        }
    ]
    
    # Esegui tutti i test
    for i, case in enumerate(test_cases, 1):
        test_oil_addition_case(
            case_number=i,
            meal_name=case["meal_name"],
            food_list=case["food_list"], 
            description=case["description"]
        )
    
    print(f"\n{'='*80}")
    print("🏁 TUTTI I TEST OLIO COMPLETATI")
    print("="*80)

if __name__ == "__main__":
    run_oil_tests() 