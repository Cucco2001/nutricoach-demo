"""
Test per verificare i limiti fisici dei carboidrati con patate, broccoli e olio
"""

import json
import os
import sys

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_tools.meal_optimization_tool import get_portion_constraints

def load_food_database():
    """Carica il database degli alimenti"""
    db_path = "Dati_processed/banca_alimenti_crea_60alimenti.json"
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_max_carbs_possible():
    """Calcola il massimo di carboidrati possibile con patate, broccoli e olio"""
    
    print("🧪 TEST: Massimo carboidrati raggiungibili con patate, broccoli, olio")
    print("=" * 70)
    
    # Carica il database
    food_db = load_food_database()
    
    # Alimenti da testare
    foods = ["patate", "broccoli", "olio_oliva"]
    
    print("📋 ANALISI SINGOLI ALIMENTI:")
    print("-" * 40)
    
    for food in foods:
        if food in food_db:
            food_data = food_db[food]
            carbs_per_100g = food_data["carboidrati_g"]
            
            # Ottieni i vincoli di porzione dalla categoria
            constraints = get_portion_constraints()
            categoria = food_data["categoria"]
            constraint = constraints.get(categoria, constraints["alimento_misto"])
            min_portion = constraint["min"]
            max_portion = constraint["max"]
            
            # Calcola carboidrati max possibili
            max_carbs = (carbs_per_100g * max_portion) / 100
            
            print(f"   🍽️ {food}:")
            print(f"      Carboidrati per 100g: {carbs_per_100g}g")
            print(f"      Porzione min-max: {min_portion}g - {max_portion}g")
            print(f"      Max carboidrati: {max_carbs:.1f}g (a {max_portion}g)")
            print()
    
    print("🎯 CALCOLO TOTALE MASSIMO:")
    print("-" * 30)
    
    total_max_carbs = 0
    total_max_kcal = 0
    total_max_protein = 0
    total_max_fat = 0
    
    portions_used = {}
    
    for food in foods:
        if food in food_db:
            food_data = food_db[food]
            constraints = get_portion_constraints()
            categoria = food_data["categoria"]
            constraint = constraints.get(categoria, constraints["alimento_misto"])
            min_portion = constraint["min"]
            max_portion = constraint["max"]
            
            # Usa la porzione massima
            portions_used[food] = max_portion
            
            # Calcola i nutrienti
            carbs = (food_data["carboidrati_g"] * max_portion) / 100
            kcal = (food_data.get("energia_kcal", food_data.get("kcal", 0)) * max_portion) / 100
            protein = (food_data["proteine_g"] * max_portion) / 100
            fat = (food_data["grassi_g"] * max_portion) / 100
            
            total_max_carbs += carbs
            total_max_kcal += kcal
            total_max_protein += protein
            total_max_fat += fat
            
            print(f"   • {food} ({max_portion}g): +{carbs:.1f}g carb")
    
    print()
    print("📊 TOTALI MASSIMI RAGGIUNGIBILI:")
    print("-" * 35)
    print(f"   • Carboidrati: {total_max_carbs:.1f}g")
    print(f"   • Calorie: {total_max_kcal:.1f} kcal")
    print(f"   • Proteine: {total_max_protein:.1f}g")
    print(f"   • Grassi: {total_max_fat:.1f}g")
    
    print()
    print("🎯 CONFRONTO CON TARGET CENA:")
    print("-" * 30)
    target_carbs = 78
    target_kcal = 543
    target_protein = 18
    target_fat = 15
    
    carb_shortfall = target_carbs - total_max_carbs
    kcal_shortfall = target_kcal - total_max_kcal
    
    print(f"   Target carboidrati: {target_carbs}g")
    print(f"   Max raggiungibili: {total_max_carbs:.1f}g")
    
    if carb_shortfall > 0:
        print(f"   ❌ DEFICIT: {carb_shortfall:.1f}g carboidrati IMPOSSIBILI da raggiungere!")
        print(f"   📈 Percentuale raggiungibile: {(total_max_carbs/target_carbs*100):.1f}%")
    else:
        print(f"   ✅ SURPLUS: {-carb_shortfall:.1f}g carboidrati extra disponibili")
    
    print()
    print(f"   Target calorie: {target_kcal} kcal")
    print(f"   Max raggiungibili: {total_max_kcal:.1f} kcal")
    
    if kcal_shortfall > 0:
        print(f"   ❌ DEFICIT: {kcal_shortfall:.1f} kcal IMPOSSIBILI da raggiungere!")
    else:
        print(f"   ✅ SURPLUS: {-kcal_shortfall:.1f} kcal extra disponibili")
    
    print()
    print("💡 CONCLUSIONE:")
    print("-" * 15)
    if carb_shortfall > 0:
        print("   🚨 È FISICAMENTE IMPOSSIBILE raggiungere i target di carboidrati")
        print("   🔄 Serve AGGIUNGERE altri alimenti ricchi di carboidrati!")
        print("   💡 Suggerimenti: pasta, riso, pane, cereali, legumi")
    else:
        print("   ✅ I target sono teoricamente raggiungibili")
        print("   🤔 Il problema è nell'ottimizzazione algorithm")

if __name__ == "__main__":
    test_max_carbs_possible() 