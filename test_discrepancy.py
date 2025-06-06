"""
Test per investigare la discrepanza tra nutrienti calcolati e target utente.

Questo test usa i dati reali dell'utente e gli alimenti menzionati
per capire perché ci sono differenze tra i risultati.
"""

import sys
import os
import json
import streamlit as st
from typing import Dict, List

# Aggiungi il path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import optimize_meal_portions

def setup_real_user_environment():
    """Configura l'ambiente con i dati reali dell'utente."""
    
    # Simula session_state di Streamlit
    if not hasattr(st, 'session_state'):
        class MockSessionState:
            def __init__(self):
                self.user_info = {
                    "id": "user_1747679093",  # Usa l'ID dell'utente reale
                }
        st.session_state = MockSessionState()
    else:
        st.session_state.user_info = {
            "id": "user_1747679093",
        }
    
    print("✅ Ambiente configurato con utente reale: user_1747679093")
    
    # Verifica che il file utente esista
    user_file = "user_data/user_1747679093.json"
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # Mostra i target della cena dall'utente reale
        if "nutritional_info_extracted" in user_data and "daily_macros" in user_data["nutritional_info_extracted"]:
            distribuzione = user_data["nutritional_info_extracted"]["daily_macros"].get("distribuzione_pasti", {})
            if "Cena" in distribuzione:
                cena_target = distribuzione["Cena"]
                print(f"🎯 Target CENA dall'utente reale:")
                print(f"   Calorie: {cena_target.get('kcal', 'N/A')}")
                print(f"   Proteine: {cena_target.get('proteine_g', 'N/A')}g")
                print(f"   Carboidrati: {cena_target.get('carboidrati_g', 'N/A')}g")
                print(f"   Grassi: {cena_target.get('grassi_g', 'N/A')}g")
            else:
                print("⚠️ 'Cena' non trovata nella distribuzione pasti")
                print("📋 Pasti disponibili:", list(distribuzione.keys()))
        else:
            print("❌ Dati nutrizionali non trovati nel file utente")
    else:
        print(f"❌ File utente {user_file} non trovato")

def test_real_user_meal():
    """Testa con gli alimenti e l'utente reale menzionati."""
    
    print(f"\n{'='*80}")
    print("🧪 TEST DISCREPANZA - DATI UTENTE REALE")
    print("="*80)
    
    # Alimenti menzionati dall'utente (convertiti ai nomi del database)
    # "Pollo: 70g, Pasta integrale: 100g, Broccoli: 50g, Olio d'oliva: 10ml"
    food_list = ["pollo_petto", "pasta_integrale", "broccoli", "olio_oliva"]
    meal_name = "Cena"  # Usa esattamente "Cena" come nel file utente
    
    print(f"🍽️  Pasto: {meal_name}")
    print(f"🥘 Alimenti: {', '.join(food_list)}")
    
    try:
        result = optimize_meal_portions(meal_name, food_list)
        
        if result["success"]:
            print("\n✅ OTTIMIZZAZIONE RIUSCITA")
            
            print("\n📋 PORZIONI OTTIMIZZATE:")
            for food, grams in result["portions"].items():
                print(f"   • {food}: {grams}g")
            
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
            
            # Confronto con i valori menzionati dall'utente
            print(f"\n🔍 CONFRONTO CON VALORI DELL'UTENTE:")
            print(f"   Menzione utente: Proteine 30.4g vs Nostro calcolo: {actual['proteine_g']:.1f}g")
            print(f"   Menzione utente: Carboidrati 68g vs Nostro calcolo: {actual['carboidrati_g']:.1f}g")
            print(f"   Menzione utente: Grassi 15g vs Nostro calcolo: {actual['grassi_g']:.1f}g")
            
            # Verifica se le porzioni sono diverse
            print(f"\n📏 CONFRONTO PORZIONI:")
            mentioned_portions = {"pollo_petto": 70, "pasta_integrale": 100, "broccoli": 50, "olio_oliva": 10}
            for food, mentioned_grams in mentioned_portions.items():
                if food in result["portions"]:
                    optimized_grams = result["portions"][food]
                    print(f"   {food}: Menzionato {mentioned_grams}g vs Ottimizzato {optimized_grams}g")
                else:
                    print(f"   {food}: Menzionato {mentioned_grams}g vs NON PRESENTE nell'ottimizzazione")
            
            # Calcola errore medio
            avg_error = sum([
                result['errors']['kcal_error_pct'],
                result['errors']['proteine_g_error_pct'],
                result['errors']['carboidrati_g_error_pct'],
                result['errors']['grassi_g_error_pct']
            ]) / 4
            
            print(f"\n📊 ERRORE MEDIO: {avg_error:.1f}%")
            
            # Mostra se è stato aggiunto olio
            if result.get("oil_added", False):
                print("🫒 Nota: Olio aggiunto automaticamente")
            
            print(f"\n📝 SUMMARY: {result.get('optimization_summary', 'N/A')}")
            
        else:
            print("❌ OTTIMIZZAZIONE FALLITA")
            print(f"Errore: {result['error_message']}")
            if 'foods_not_found' in result:
                print(f"Alimenti non trovati: {result['foods_not_found']}")
    
    except Exception as e:
        print(f"💥 ERRORE DURANTE IL TEST: {str(e)}")

def test_meal_name_variants():
    """Testa diverse varianti del nome del pasto per vedere se questo causa il problema."""
    
    print(f"\n{'='*80}")
    print("🧪 TEST VARIANTI NOME PASTO")
    print("="*80)
    
    food_list = ["pollo_petto", "pasta_integrale", "broccoli"]
    meal_variants = ["Cena", "cena", "dinner", "Dinner"]
    
    for variant in meal_variants:
        print(f"\n🔍 Testando con nome pasto: '{variant}'")
        try:
            result = optimize_meal_portions(variant, food_list)
            if result["success"]:
                target = result["target_nutrients"]
                print(f"   Target trovati: kcal={target['kcal']}, prot={target['proteine_g']}g, carb={target['carboidrati_g']}g, grassi={target['grassi_g']}g")
            else:
                print(f"   ❌ Fallito: {result['error_message']}")
        except Exception as e:
            print(f"   💥 Errore: {str(e)}")

def run_discrepancy_test():
    """Esegue i test per investigare la discrepanza."""
    
    print("🔍 AVVIO TEST INVESTIGAZIONE DISCREPANZA")
    print("="*80)
    
    # Setup ambiente con utente reale
    setup_real_user_environment()
    
    # Test con dati reali
    test_real_user_meal()
    
    # Test varianti nome pasto
    test_meal_name_variants()
    
    print(f"\n{'='*80}")
    print("🏁 TEST DISCREPANZA COMPLETATI")
    print("="*80)

if __name__ == "__main__":
    run_discrepancy_test() 