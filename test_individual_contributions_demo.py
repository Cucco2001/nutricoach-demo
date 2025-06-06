"""
Demo per mostrare il nuovo campo individual_contributions.
"""

import sys
import os
import streamlit as st
import json

# Aggiungi il path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import optimize_meal_portions

def setup_demo_environment():
    """Configura l'ambiente demo."""
    
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

def demo_individual_contributions():
    """Demo del nuovo campo individual_contributions."""
    
    print(f"{'='*80}")
    print("🔬 DEMO CONTRIBUTI INDIVIDUALI ALIMENTI")
    print("="*80)
    
    setup_demo_environment()
    
    # Test con un pasto semplice
    food_list = ["pollo_petto", "pasta_integrale", "broccoli"]
    
    print(f"🍽️ Pasto: Cena")
    print(f"🥘 Alimenti: {', '.join(food_list)}")
    
    result = optimize_meal_portions("Cena", food_list)
    
    if result["success"]:
        print(f"\n✅ OTTIMIZZAZIONE RIUSCITA")
        
        print(f"\n🎯 TARGET NUTRIZIONALI:")
        target = result["target_nutrients"]
        print(f"   🔥 Calorie: {target['kcal']}")
        print(f"   🥩 Proteine: {target['proteine_g']}g")
        print(f"   🍞 Carboidrati: {target['carboidrati_g']}g")
        print(f"   🥑 Grassi: {target['grassi_g']}g")
        
        print(f"\n📋 CONTRIBUTI INDIVIDUALI DETTAGLIATI:")
        for food, contrib in result["individual_contributions"].items():
            print(f"\n   📦 {food.upper().replace('_', ' ')} ({contrib['portion_g']}g):")
            print(f"      🔥 {contrib['kcal']} kcal")
            print(f"      🥩 {contrib['proteine_g']}g proteine")
            print(f"      🍞 {contrib['carboidrati_g']}g carboidrati")
            print(f"      🥑 {contrib['grassi_g']}g grassi")
            print(f"      📂 Categoria: {contrib['categoria']}")
        
        print(f"\n🧮 TOTALE EFFETTIVO:")
        actual = result["actual_nutrients"]
        print(f"   🔥 Calorie: {actual['kcal']} kcal")
        print(f"   🥩 Proteine: {actual['proteine_g']}g")
        print(f"   🍞 Carboidrati: {actual['carboidrati_g']}g")
        print(f"   🥑 Grassi: {actual['grassi_g']}g")
        
        print(f"\n📊 ERRORI:")
        errors = result["errors"]
        print(f"   🔥 Calorie: {errors['kcal_error_pct']:.1f}%")
        print(f"   🥩 Proteine: {errors['proteine_g_error_pct']:.1f}%")
        print(f"   🍞 Carboidrati: {errors['carboidrati_g_error_pct']:.1f}%")
        print(f"   🥑 Grassi: {errors['grassi_g_error_pct']:.1f}%")
        
        if result.get("oil_added", False):
            print(f"\n🫒 Nota: Olio aggiunto automaticamente per migliorare l'ottimizzazione")
        
    else:
        print(f"❌ OTTIMIZZAZIONE FALLITA: {result['error_message']}")
    
    print(f"\n{'='*80}")

# Carica database
db = json.load(open('Dati_processed/banca_alimenti_crea_60alimenti.json', 'r', encoding='utf-8'))

print("🧮 TEST: Calcolo manuale per raggiungere 78g carboidrati")
print("=" * 60)

# Target
target_carbs = 78
target_kcal = 543
target_protein = 18
target_fat = 15

# Dati nutrizionali per 100g
patate = db['patate']
broccoli = db['broccoli'] 
olio = db['olio_oliva']

print(f"📊 DATI NUTRIZIONALI (per 100g):")
print(f"   Patate: {patate['energia_kcal']} kcal, {patate['proteine_g']}g prot, {patate['carboidrati_g']}g carb, {patate['grassi_g']}g grassi")
print(f"   Broccoli: {broccoli['energia_kcal']} kcal, {broccoli['proteine_g']}g prot, {broccoli['carboidrati_g']}g carb, {broccoli['grassi_g']}g grassi")
print(f"   Olio: {olio['energia_kcal']} kcal, {olio['proteine_g']}g prot, {olio['carboidrati_g']}g carb, {olio['grassi_g']}g grassi")

print()
print("🧮 CALCOLO MANUALE PER RAGGIUNGERE 78g CARBOIDRATI:")
print("-" * 50)

# Scenario 1: Risultato attuale dell'algoritmo
print("📋 SCENARIO 1: Risultato attuale algoritmo")
portions_1 = {'patate': 100, 'broccoli': 210, 'olio_oliva': 10}

total_carbs_1 = (patate['carboidrati_g'] * portions_1['patate'] / 100 + 
                 broccoli['carboidrati_g'] * portions_1['broccoli'] / 100 + 
                 olio['carboidrati_g'] * portions_1['olio_oliva'] / 100)

total_kcal_1 = (patate['energia_kcal'] * portions_1['patate'] / 100 + 
                broccoli['energia_kcal'] * portions_1['broccoli'] / 100 + 
                olio['energia_kcal'] * portions_1['olio_oliva'] / 100)

total_protein_1 = (patate['proteine_g'] * portions_1['patate'] / 100 + 
                   broccoli['proteine_g'] * portions_1['broccoli'] / 100 + 
                   olio['proteine_g'] * portions_1['olio_oliva'] / 100)

total_fat_1 = (patate['grassi_g'] * portions_1['patate'] / 100 + 
               broccoli['grassi_g'] * portions_1['broccoli'] / 100 + 
               olio['grassi_g'] * portions_1['olio_oliva'] / 100)

print(f"   Porzioni: {portions_1['patate']}g patate + {portions_1['broccoli']}g broccoli + {portions_1['olio_oliva']}g olio")
print(f"   Risultato: {total_kcal_1:.1f} kcal, {total_protein_1:.1f}g prot, {total_carbs_1:.1f}g carb, {total_fat_1:.1f}g grassi")
print(f"   Errori: kcal {total_kcal_1-target_kcal:+.1f}, prot {total_protein_1-target_protein:+.1f}, carb {total_carbs_1-target_carbs:+.1f}, grassi {total_fat_1-target_fat:+.1f}")

print()

# Scenario 2: Porzioni per raggiungere carboidrati target
print("📋 SCENARIO 2: Ottimizzazione manuale per 78g carboidrati")

# Calcolo inverso: quante patate servono per i carboidrati mancanti?
carbs_needed = target_carbs - total_carbs_1
patate_needed_for_carbs = carbs_needed / (patate['carboidrati_g'] / 100)

print(f"   Carboidrati mancanti: {carbs_needed:.1f}g")
print(f"   Patate extra necessarie: {patate_needed_for_carbs:.1f}g")

# Scenario ottimizzato manualmente
portions_2 = {
    'patate': 260,  # Circa quello che serve per 78g carb
    'broccoli': 150,  # Riduciamo un po' i broccoli
    'olio_oliva': 15   # Aumentiamo l'olio per i grassi
}

total_carbs_2 = (patate['carboidrati_g'] * portions_2['patate'] / 100 + 
                 broccoli['carboidrati_g'] * portions_2['broccoli'] / 100 + 
                 olio['carboidrati_g'] * portions_2['olio_oliva'] / 100)

total_kcal_2 = (patate['energia_kcal'] * portions_2['patate'] / 100 + 
                broccoli['energia_kcal'] * portions_2['broccoli'] / 100 + 
                olio['energia_kcal'] * portions_2['olio_oliva'] / 100)

total_protein_2 = (patate['proteine_g'] * portions_2['patate'] / 100 + 
                   broccoli['proteine_g'] * portions_2['broccoli'] / 100 + 
                   olio['proteine_g'] * portions_2['olio_oliva'] / 100)

total_fat_2 = (patate['grassi_g'] * portions_2['patate'] / 100 + 
               broccoli['grassi_g'] * portions_2['broccoli'] / 100 + 
               olio['grassi_g'] * portions_2['olio_oliva'] / 100)

print(f"   Porzioni: {portions_2['patate']}g patate + {portions_2['broccoli']}g broccoli + {portions_2['olio_oliva']}g olio")
print(f"   Risultato: {total_kcal_2:.1f} kcal, {total_protein_2:.1f}g prot, {total_carbs_2:.1f}g carb, {total_fat_2:.1f}g grassi")
print(f"   Errori: kcal {total_kcal_2-target_kcal:+.1f}, prot {total_protein_2-target_protein:+.1f}, carb {total_carbs_2-target_carbs:+.1f}, grassi {total_fat_2-target_fat:+.1f}")

print()

# Calcolo errori relativi per confronto
def calc_relative_error(actual, target):
    return abs(actual - target) / max(target, 1) * 100

print("📊 CONFRONTO ERRORI RELATIVI:")
print("-" * 30)

error_1 = (calc_relative_error(total_kcal_1, target_kcal) + 
           calc_relative_error(total_protein_1, target_protein) + 
           calc_relative_error(total_carbs_1, target_carbs) + 
           calc_relative_error(total_fat_1, target_fat)) / 4

error_2 = (calc_relative_error(total_kcal_2, target_kcal) + 
           calc_relative_error(total_protein_2, target_protein) + 
           calc_relative_error(total_carbs_2, target_carbs) + 
           calc_relative_error(total_fat_2, target_fat)) / 4

print(f"Scenario 1 (algoritmo): {error_1:.1f}% errore medio")
print(f"Scenario 2 (manuale): {error_2:.1f}% errore medio")

if error_2 < error_1:
    print(f"✅ SCENARIO 2 È MIGLIORE! Miglioramento: {error_1-error_2:.1f}%")
    print("🚨 L'algoritmo NON trova la soluzione ottimale!")
else:
    print(f"❌ Scenario 1 rimane migliore")
    print("🤔 Il problema potrebbe essere nei vincoli o nella funzione obiettivo")

if __name__ == "__main__":
    demo_individual_contributions() 