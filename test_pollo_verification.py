"""
Test per verificare i valori nutrizionali del pollo e il caso specifico di discrepanza.
"""

import sys
import os
import json
import streamlit as st

# Aggiungi il path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import get_food_nutrition_per_100g, calculate_actual_nutrients, optimize_meal_portions

def setup_test_environment():
    """Configura l'ambiente di test."""
    
    # Simula session_state di Streamlit
    if not hasattr(st, 'session_state'):
        class MockSessionState:
            def __init__(self):
                self.user_info = {
                    "id": "user_1747679093",
                }
        st.session_state = MockSessionState()
    else:
        st.session_state.user_info = {
            "id": "user_1747679093",
        }

def test_chicken_nutrition():
    """Testa i valori nutrizionali del pollo."""
    
    print(f"\n{'='*80}")
    print("🐔 TEST VALORI NUTRIZIONALI POLLO")
    print("="*80)
    
    try:
        # Ottieni i dati nutrizionali del pollo per 100g
        chicken_nutrition = get_food_nutrition_per_100g(["pollo_petto"])
        pollo_100g = chicken_nutrition["pollo_petto"]
        
        print(f"📊 POLLO PETTO - Valori per 100g:")
        print(f"   🔥 Calorie: {pollo_100g['energia_kcal']}")
        print(f"   🥩 Proteine: {pollo_100g['proteine_g']}g")
        print(f"   🍞 Carboidrati: {pollo_100g['carboidrati_g']}g")
        print(f"   🥑 Grassi: {pollo_100g['grassi_g']}g")
        print(f"   📂 Categoria: {pollo_100g['categoria']}")
        
        # Calcola per 70g
        print(f"\n📊 POLLO PETTO - Valori per 70g:")
        kcal_70g = pollo_100g['energia_kcal'] * 70 / 100
        proteine_70g = pollo_100g['proteine_g'] * 70 / 100
        carb_70g = pollo_100g['carboidrati_g'] * 70 / 100
        grassi_70g = pollo_100g['grassi_g'] * 70 / 100
        
        print(f"   🔥 Calorie: {kcal_70g:.1f}")
        print(f"   🥩 Proteine: {proteine_70g:.1f}g")
        print(f"   🍞 Carboidrati: {carb_70g:.1f}g")
        print(f"   🥑 Grassi: {grassi_70g:.1f}g")
        
        return pollo_100g
        
    except Exception as e:
        print(f"❌ Errore nel test pollo: {str(e)}")
        return None

def test_specific_case_calculation():
    """Testa il calcolo specifico del caso che ha dato problemi."""
    
    print(f"\n{'='*80}")
    print("🧮 TEST CALCOLO CASO SPECIFICO")
    print("="*80)
    
    # Porzioni dal caso precedente
    portions = {
        "pollo_petto": 70.0,
        "pasta_integrale": 100.0,
        "broccoli": 50.0,
        "olio_oliva": 10.0
    }
    
    print(f"🍽️ Porzioni da testare:")
    for food, grams in portions.items():
        print(f"   • {food}: {grams}g")
    
    try:
        # Ottieni i dati nutrizionali per 100g di tutti gli alimenti
        food_list = list(portions.keys())
        foods_nutrition = get_food_nutrition_per_100g(food_list)
        
        print(f"\n📊 DATI NUTRIZIONALI per 100g:")
        for food, nutrition in foods_nutrition.items():
            print(f"   {food}:")
            print(f"      🔥 {nutrition['energia_kcal']} kcal")
            print(f"      🥩 {nutrition['proteine_g']}g proteine")
            print(f"      🍞 {nutrition['carboidrati_g']}g carboidrati")
            print(f"      🥑 {nutrition['grassi_g']}g grassi")
        
        # Calcola i nutrienti totali
        actual_nutrients = calculate_actual_nutrients(portions, foods_nutrition)
        
        print(f"\n🎯 NUTRIENTI TOTALI CALCOLATI:")
        print(f"   🔥 Calorie: {actual_nutrients['kcal']} kcal")
        print(f"   🥩 Proteine: {actual_nutrients['proteine_g']}g")
        print(f"   🍞 Carboidrati: {actual_nutrients['carboidrati_g']}g")
        print(f"   🥑 Grassi: {actual_nutrients['grassi_g']}g")
        
        # Confronto con i valori menzionati dal modello
        print(f"\n🔍 CONFRONTO CON VALORI MODELLO:")
        print(f"   🥩 Proteine: Nostro {actual_nutrients['proteine_g']}g vs Modello 30.4g")
        print(f"   🍞 Carboidrati: Nostro {actual_nutrients['carboidrati_g']}g vs Modello 68g")
        print(f"   🥑 Grassi: Nostro {actual_nutrients['grassi_g']}g vs Modello 15g")
        
        # Verifica dettagliata per ogni alimento
        print(f"\n🔬 CALCOLO DETTAGLIATO PER ALIMENTO:")
        total_check = {"kcal": 0, "proteine_g": 0, "carboidrati_g": 0, "grassi_g": 0}
        
        for food, grams in portions.items():
            nutrition = foods_nutrition[food]
            
            kcal_contrib = nutrition['energia_kcal'] * grams / 100
            prot_contrib = nutrition['proteine_g'] * grams / 100
            carb_contrib = nutrition['carboidrati_g'] * grams / 100
            fat_contrib = nutrition['grassi_g'] * grams / 100
            
            total_check["kcal"] += kcal_contrib
            total_check["proteine_g"] += prot_contrib
            total_check["carboidrati_g"] += carb_contrib
            total_check["grassi_g"] += fat_contrib
            
            print(f"   {food} ({grams}g):")
            print(f"      🔥 {kcal_contrib:.1f} kcal")
            print(f"      🥩 {prot_contrib:.1f}g proteine")
            print(f"      🍞 {carb_contrib:.1f}g carboidrati")
            print(f"      🥑 {fat_contrib:.1f}g grassi")
        
        print(f"\n✅ TOTALE RICONTROLLATO:")
        print(f"   🔥 {total_check['kcal']:.1f} kcal")
        print(f"   🥩 {total_check['proteine_g']:.1f}g proteine")
        print(f"   🍞 {total_check['carboidrati_g']:.1f}g carboidrati")
        print(f"   🥑 {total_check['grassi_g']:.1f}g grassi")
        
        # Verifica se i totali combaciano
        tolerance = 0.1
        kcal_match = abs(total_check['kcal'] - actual_nutrients['kcal']) < tolerance
        prot_match = abs(total_check['proteine_g'] - actual_nutrients['proteine_g']) < tolerance
        carb_match = abs(total_check['carboidrati_g'] - actual_nutrients['carboidrati_g']) < tolerance
        fat_match = abs(total_check['grassi_g'] - actual_nutrients['grassi_g']) < tolerance
        
        print(f"\n🔍 VERIFICA COERENZA CALCOLI:")
        print(f"   🔥 Calorie: {'✅' if kcal_match else '❌'}")
        print(f"   🥩 Proteine: {'✅' if prot_match else '❌'}")
        print(f"   🍞 Carboidrati: {'✅' if carb_match else '❌'}")
        print(f"   🥑 Grassi: {'✅' if fat_match else '❌'}")
        
        return actual_nutrients
        
    except Exception as e:
        print(f"❌ Errore nel test calcolo: {str(e)}")
        return None

def test_individual_contributions():
    """Testa il nuovo campo individual_contributions."""
    
    print(f"\n{'='*80}")
    print("🔬 TEST CONTRIBUTI INDIVIDUALI")
    print("="*80)
    
    try:
        # Test ottimizzazione completa
        food_list = ["pollo_petto", "pasta_integrale", "broccoli"]
        
        result = optimize_meal_portions("Cena", food_list)
        
        if result["success"]:
            print(f"✅ Ottimizzazione riuscita")
            
            print(f"\n📋 CONTRIBUTI INDIVIDUALI:")
            for food, contrib in result["individual_contributions"].items():
                print(f"   {food} ({contrib['portion_g']}g):")
                print(f"      🔥 {contrib['kcal']} kcal")
                print(f"      🥩 {contrib['proteine_g']}g proteine")
                print(f"      🍞 {contrib['carboidrati_g']}g carboidrati")
                print(f"      🥑 {contrib['grassi_g']}g grassi")
                print(f"      📂 {contrib['categoria']}")
            
            # Verifica che la somma dei contributi individuali corrisponda ai nutrienti totali
            total_from_individual = {
                "kcal": sum(contrib["kcal"] for contrib in result["individual_contributions"].values()),
                "proteine_g": sum(contrib["proteine_g"] for contrib in result["individual_contributions"].values()),
                "carboidrati_g": sum(contrib["carboidrati_g"] for contrib in result["individual_contributions"].values()),
                "grassi_g": sum(contrib["grassi_g"] for contrib in result["individual_contributions"].values())
            }
            
            print(f"\n🧮 VERIFICA SOMMA CONTRIBUTI:")
            print(f"   🔥 Calorie: Individuali {total_from_individual['kcal']} vs Totali {result['actual_nutrients']['kcal']}")
            print(f"   🥩 Proteine: Individuali {total_from_individual['proteine_g']} vs Totali {result['actual_nutrients']['proteine_g']}")
            print(f"   🍞 Carboidrati: Individuali {total_from_individual['carboidrati_g']} vs Totali {result['actual_nutrients']['carboidrati_g']}")
            print(f"   🥑 Grassi: Individuali {total_from_individual['grassi_g']} vs Totali {result['actual_nutrients']['grassi_g']}")
            
            # Controlla se le somme combaciano (con tolleranza di 0.1)
            tolerance = 0.1
            matches = {
                "kcal": abs(total_from_individual['kcal'] - result['actual_nutrients']['kcal']) < tolerance,
                "proteine_g": abs(total_from_individual['proteine_g'] - result['actual_nutrients']['proteine_g']) < tolerance,
                "carboidrati_g": abs(total_from_individual['carboidrati_g'] - result['actual_nutrients']['carboidrati_g']) < tolerance,
                "grassi_g": abs(total_from_individual['grassi_g'] - result['actual_nutrients']['grassi_g']) < tolerance
            }
            
            print(f"\n✅ COERENZA VERIFICATA:")
            for nutrient, match in matches.items():
                print(f"   {nutrient}: {'✅' if match else '❌'}")
            
            # Controlla se è stato aggiunto olio
            if result.get("oil_added", False):
                print(f"\n🫒 Olio aggiunto automaticamente - Contributo olio:")
                if "olio_oliva" in result["individual_contributions"]:
                    oil_contrib = result["individual_contributions"]["olio_oliva"]
                    print(f"   Porzione: {oil_contrib['portion_g']}g")
                    print(f"   Grassi: {oil_contrib['grassi_g']}g")
                    print(f"   Calorie: {oil_contrib['kcal']} kcal")
            
        else:
            print(f"❌ Ottimizzazione fallita: {result['error_message']}")
            
    except Exception as e:
        print(f"❌ Errore nel test contributi individuali: {str(e)}")

def run_verification_test():
    """Esegue tutti i test di verifica."""
    
    print("🔍 AVVIO TEST VERIFICA POLLO E CALCOLI")
    print("="*80)
    
    # Setup ambiente
    setup_test_environment()
    
    # Test valori pollo
    chicken_data = test_chicken_nutrition()
    
    # Test calcolo caso specifico
    calculated_nutrients = test_specific_case_calculation()
    
    # Test contributi individuali
    test_individual_contributions()
    
    print(f"\n{'='*80}")
    print("🏁 TEST VERIFICA COMPLETATI")
    print("="*80)

if __name__ == "__main__":
    run_verification_test() 