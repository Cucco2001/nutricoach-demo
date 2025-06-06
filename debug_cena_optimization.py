"""
Debug del problema di ottimizzazione della cena
"""

import json
import os
import sys

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import optimize_meal_portions, get_food_nutrition_per_100g

class MockSessionState:
    def __init__(self):
        self.user_info = {"id": "user_1747679093"}  # Uso l'ID dell'utente reale
    
    def __contains__(self, key):
        return hasattr(self, key)

# Mock di streamlit session_state
import streamlit as st
st.session_state = MockSessionState()

def debug_cena_optimization():
    """Debugga l'ottimizzazione della cena"""
    
    print("🔍 DEBUG: Problema ottimizzazione cena")
    print("=" * 60)
    
    # Target attesi dalla cena dell'utente
    expected_targets = {
        "kcal": 543,
        "proteine_g": 18,
        "carboidrati_g": 78,
        "grassi_g": 15
    }
    
    print("🎯 TARGET ATTESI:")
    for nutrient, target in expected_targets.items():
        print(f"   {nutrient}: {target}")
    print()
    
    # Test con gli alimenti della cena problematica
    food_list_original = ["patate", "broccoli", "salmone_affumicato"]
    print(f"🍽️ ALIMENTI ORIGINALI: {food_list_original}")
    
    # Test 1: Ottimizzazione con tutti gli alimenti
    print("\n📊 TEST 1: Ottimizzazione con tutti gli alimenti")
    result1 = optimize_meal_portions(
        meal_name="cena",
        food_list=food_list_original
    )
    
    if result1["success"]:
        print("   ✅ Ottimizzazione riuscita")
        print(f"   📊 Target effettivi dal DB utente:")
        for nutrient, target in result1["target_nutrients"].items():
            print(f"      {nutrient}: {target}")
        
        print(f"   📊 Risultati ottimizzazione:")
        for nutrient, actual in result1["actual_nutrients"].items():
            target = result1["target_nutrients"][nutrient]
            error = actual - target
            error_pct = (error / target * 100) if target > 0 else 0
            print(f"      {nutrient}: {actual} (target: {target}, errore: {error:+.1f}, {error_pct:+.1f}%)")
        
        print(f"   🍽️ Porzioni:")
        for food, portion in result1["portions"].items():
            print(f"      {food}: {portion}g")
        
        print(f"   📝 Summary: {result1.get('optimization_summary', 'N/A')}")
        
    else:
        print(f"   ❌ Ottimizzazione fallita: {result1.get('error_message', 'Errore sconosciuto')}")
    
    # Test 2: Verifica dati nutrizionali singoli alimenti
    print("\n🧪 TEST 2: Analisi dati nutrizionali singoli alimenti")
    try:
        nutrition_data = get_food_nutrition_per_100g(food_list_original)
        
        for food, data in nutrition_data.items():
            print(f"   🥘 {food}:")
            print(f"      Categoria: {data['categoria']}")
            print(f"      Per 100g: {data['energia_kcal']} kcal, {data['proteine_g']}g prot, {data['carboidrati_g']}g carb, {data['grassi_g']}g grassi")
            
    except Exception as e:
        print(f"   ❌ Errore nel caricamento dati: {str(e)}")
    
    # Test 3: Calcolo manuale per raggiungere 78g carboidrati
    print("\n🧮 TEST 3: Calcolo manuale per raggiungere 78g carboidrati")
    try:
        # Assumendo che patate abbiano ~20g carb/100g e broccoli ~7g carb/100g
        # Per raggiungere 78g di carboidrati:
        
        if "patate" in nutrition_data:
            patate_carb_per_100g = nutrition_data["patate"]["carboidrati_g"]
            print(f"   Patate: {patate_carb_per_100g}g carb per 100g")
            
            # Quanto ne servirebbe solo di patate per 78g carb?
            patate_needed = (78 / patate_carb_per_100g) * 100
            print(f"   Per 78g carb servirebbe: {patate_needed:.0f}g di patate da sole")
        
        if "broccoli" in nutrition_data:
            broccoli_carb_per_100g = nutrition_data["broccoli"]["carboidrati_g"]
            print(f"   Broccoli: {broccoli_carb_per_100g}g carb per 100g")
        
        # Combinazione realistica
        print(f"   💡 Combinazione più realistica:")
        print(f"      300g patate ({patate_carb_per_100g * 3:.1f}g carb) + 200g broccoli ({broccoli_carb_per_100g * 2:.1f}g carb) = {(patate_carb_per_100g * 3) + (broccoli_carb_per_100g * 2):.1f}g carb totali")
        
    except Exception as e:
        print(f"   ❌ Errore nel calcolo manuale: {str(e)}")

if __name__ == "__main__":
    debug_cena_optimization() 