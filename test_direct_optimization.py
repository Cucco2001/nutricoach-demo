"""
Test diretto con patate, broccoli e olio per verificare se l'ottimizzazione raggiunge i target
"""

import json
import os
import sys

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import optimize_meal_portions

class MockSessionState:
    def __init__(self):
        self.user_info = {"id": "user_1747679093"}  # Uso l'ID dell'utente reale
    
    def __contains__(self, key):
        return hasattr(self, key)

# Mock di streamlit session_state
import streamlit as st
st.session_state = MockSessionState()

def test_direct_optimization():
    """Test diretto con i 3 alimenti finali della cena"""
    
    print("🧪 TEST: Ottimizzazione DIRETTA con patate, broccoli, olio")
    print("=" * 70)
    
    # Target della cena (dal DB utente)
    expected_targets = {
        "kcal": 543,
        "proteine_g": 18,
        "carboidrati_g": 78,
        "grassi_g": 15
    }
    
    print("🎯 TARGET DA RAGGIUNGERE:")
    for nutrient, target in expected_targets.items():
        print(f"   {nutrient}: {target}")
    print()
    
    # Test DIRETTO con solo i 3 alimenti finali
    food_list_direct = ["patate", "broccoli", "olio_oliva"]
    print(f"🍽️ ALIMENTI: {food_list_direct}")
    print()
    
    result = optimize_meal_portions(
        meal_name="cena",
        food_list=food_list_direct
    )
    
    if result["success"]:
        print("✅ OTTIMIZZAZIONE DIRETTA RIUSCITA!")
        print()
        
        print("📊 CONFRONTO TARGET vs RISULTATI:")
        print("-" * 50)
        
        for nutrient in ["kcal", "proteine_g", "carboidrati_g", "grassi_g"]:
            target = result["target_nutrients"][nutrient]
            actual = result["actual_nutrients"][nutrient]
            error = actual - target
            error_pct = (error / target * 100) if target > 0 else 0
            
            status = "✅" if abs(error_pct) < 15 else "❌" if abs(error_pct) > 25 else "⚠️"
            
            print(f"   {status} {nutrient}:")
            print(f"      Target: {target}")
            print(f"      Effettivo: {actual}")
            print(f"      Errore: {error:+.1f} ({error_pct:+.1f}%)")
            print()
        
        print("🍽️ PORZIONI RISULTANTI:")
        print("-" * 30)
        for food, portion in result["portions"].items():
            print(f"   • {food}: {portion}g")
        
        print()
        print(f"📝 Summary: {result.get('optimization_summary', 'N/A')}")
        
        # Verifica specifica sui carboidrati
        carb_actual = result["actual_nutrients"]["carboidrati_g"]
        carb_target = result["target_nutrients"]["carboidrati_g"]
        carb_error_pct = abs(carb_actual - carb_target) / carb_target * 100
        
        print()
        print("🔍 ANALISI CARBOIDRATI:")
        print("-" * 25)
        print(f"   Target: {carb_target}g")
        print(f"   Effettivo: {carb_actual}g")
        print(f"   Errore: {carb_error_pct:.1f}%")
        
        if carb_error_pct < 10:
            print("   🎉 ECCELLENTE! Carboidrati perfettamente raggiunti!")
        elif carb_error_pct < 20:
            print("   ✅ BUONO! Carboidrati ragionevolmente raggiunti")
        else:
            print("   ❌ PROBLEMA! Carboidrati ancora lontani dal target")
        
    else:
        print(f"❌ OTTIMIZZAZIONE FALLITA: {result.get('error_message', 'Errore sconosciuto')}")

if __name__ == "__main__":
    test_direct_optimization() 