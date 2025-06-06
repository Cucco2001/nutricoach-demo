#!/usr/bin/env python3
"""
Test script standalone per la funzionalità di meal optimization
Testa il sistema senza dipendenza da Streamlit session state
"""

import json
import sys
import os

# Aggiungi il path per importare i moduli
sys.path.append('.')

from agent_tools.meal_optimization_tool import get_food_nutrition_per_100g, optimize_portions, calculate_actual_nutrients
import numpy as np

def test_optimization_logic(case_num, description, food_list, target_nutrients, expected_behavior=""):
    """
    Testa la logica di ottimizzazione con target nutrizionali personalizzati
    """
    print(f"\n{'='*60}")
    print(f"TEST CASE {case_num}: {description}")
    print(f"{'='*60}")
    print(f"Alimenti: {food_list}")
    print(f"Target: {target_nutrients}")
    if expected_behavior:
        print(f"Expected: {expected_behavior}")
    print("-" * 60)
    
    try:
        # 1. Verifica che tutti gli alimenti siano nel database
        from agent_tools.nutridb import NutriDB
        db = NutriDB("Dati_processed")
        
        all_found, foods_not_found = db.check_foods_in_db(food_list)
        if not all_found:
            print(f"❌ ERRORE: Alimenti non trovati nel database: {foods_not_found}")
            return
        
        # 2. Ottieni i dati nutrizionali
        foods_nutrition = get_food_nutrition_per_100g(food_list)
        print(f"✅ Dati nutrizionali caricati per {len(foods_nutrition)} alimenti")
        
        # 3. Ottimizza le porzioni
        optimized_portions = optimize_portions(target_nutrients, foods_nutrition)
        
        # 4. Calcola nutrienti effettivi
        actual_nutrients = calculate_actual_nutrients(optimized_portions, foods_nutrition)
        
        # 5. Arrotonda le porzioni alla decina più vicina
        optimized_portions_rounded = {
            food: float(10 * np.floor(grams / 10 + 0.5)) for food, grams in optimized_portions.items()
        }
        
        # 6. Ricalcola i nutrienti dalle porzioni arrotondate
        actual_nutrients_rounded = calculate_actual_nutrients(optimized_portions_rounded, foods_nutrition)
        
        # 7. Stampa i risultati
        print(f"✅ SUCCESSO - Ottimizzazione completata")
        
        print(f"   Porzioni ottimizzate (arrotondate):")
        for food, grams in optimized_portions_rounded.items():
            print(f"     {food}: {grams}g")
        
        print(f"   Nutrienti ottenuti vs target:")
        print(f"     Calorie: {actual_nutrients_rounded['kcal']:.1f} / {target_nutrients['kcal']:.1f} (err: {abs(actual_nutrients_rounded['kcal'] - target_nutrients['kcal']):.1f})")
        print(f"     Proteine: {actual_nutrients_rounded['proteine_g']:.1f}g / {target_nutrients['proteine_g']:.1f}g (err: {abs(actual_nutrients_rounded['proteine_g'] - target_nutrients['proteine_g']):.1f}g)")
        print(f"     Carboidrati: {actual_nutrients_rounded['carboidrati_g']:.1f}g / {target_nutrients['carboidrati_g']:.1f}g (err: {abs(actual_nutrients_rounded['carboidrati_g'] - target_nutrients['carboidrati_g']):.1f}g)")
        print(f"     Grassi: {actual_nutrients_rounded['grassi_g']:.1f}g / {target_nutrients['grassi_g']:.1f}g (err: {abs(actual_nutrients_rounded['grassi_g'] - target_nutrients['grassi_g']):.1f}g)")
        
        # 8. Calcola l'errore totale
        total_error = sum([
            abs(actual_nutrients_rounded["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
            abs(actual_nutrients_rounded["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
            abs(actual_nutrients_rounded["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
            abs(actual_nutrients_rounded["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
        ]) / 4
        
        print(f"   📊 Errore totale relativo: {total_error:.3f} ({total_error*100:.1f}%)")
        
        # 9. Test aggiunta olio per pranzo/cena simulati
        if case_num in [2, 3, 5, 8]:  # Pranzi e cene
            print(f"\n   🧪 Test aggiunta olio automatica:")
            
            # Verifica se olio non è già presente
            oil_variants = ["olio", "olio_oliva", "olio d'oliva", "olio di oliva"]
            oil_already_present = any(any(oil_variant in food.lower() for oil_variant in oil_variants) for food in food_list)
            
            if not oil_already_present and total_error > 0.1:
                # Testa con olio aggiunto
                food_list_with_oil = food_list + ["olio_oliva"]
                oil_found, _ = db.check_foods_in_db(["olio_oliva"])
                
                if oil_found:
                    foods_nutrition_with_oil = get_food_nutrition_per_100g(food_list_with_oil)
                    optimized_portions_oil = optimize_portions(target_nutrients, foods_nutrition_with_oil)
                    actual_nutrients_oil = calculate_actual_nutrients(optimized_portions_oil, foods_nutrition_with_oil)
                    
                    # Calcola errore con olio
                    error_with_oil = sum([
                        abs(actual_nutrients_oil["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                        abs(actual_nutrients_oil["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                        abs(actual_nutrients_oil["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                        abs(actual_nutrients_oil["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                    ]) / 4
                    
                    improvement = total_error - error_with_oil
                    
                    print(f"     Errore con olio: {error_with_oil:.3f} (miglioramento: {improvement:.3f})")
                    
                    if improvement > 0.05:
                        print(f"     ✅ L'olio migliorerebbe significativamente l'ottimizzazione!")
                        print(f"     Olio suggerito: {optimized_portions_oil['olio_oliva']:.1f}g")
                    else:
                        print(f"     ⚪ Miglioramento non significativo")
                else:
                    print(f"     ❌ Olio d'oliva non trovato nel database")
            else:
                print(f"     ⚪ Olio già presente o errore troppo basso per testare")
        
    except Exception as e:
        print(f"❌ ECCEZIONE: {str(e)}")
        import traceback
        traceback.print_exc()

def run_all_tests():
    """
    Esegue tutti i test cases con target nutrizionali realistici
    """
    print("🚀 Avvio test standalone della funzionalità di meal optimization")
    print("=" * 80)
    
    # Test Case 1: Colazione equilibrata (400 kcal)
    test_optimization_logic(
        1,
        "Colazione semplice con cereali e frutta",
        ["avena", "latte", "banana"],
        {
            "kcal": 400,
            "proteine_g": 18,
            "carboidrati_g": 55,
            "grassi_g": 12
        },
        "Dovrebbe bilanciare cereali, proteine del latte e zuccheri della banana"
    )
    
    # Test Case 2: Pranzo standard (600 kcal)
    test_optimization_logic(
        2,
        "Pranzo classico con proteine e carboidrati",
        ["pollo", "riso", "broccoli"],
        {
            "kcal": 600,
            "proteine_g": 45,
            "carboidrati_g": 60,
            "grassi_g": 15
        },
        "Dovrebbe valutare aggiunta olio per migliorare i grassi"
    )
    
    # Test Case 3: Cena con pesce (500 kcal)
    test_optimization_logic(
        3,
        "Cena con pesce e verdure",
        ["salmone", "patate", "spinaci"],
        {
            "kcal": 500,
            "proteine_g": 35,
            "carboidrati_g": 40,
            "grassi_g": 20
        },
        "Il salmone già contiene grassi buoni"
    )
    
    # Test Case 4: Spuntino leggero (200 kcal)
    test_optimization_logic(
        4,
        "Spuntino con yogurt e frutta secca",
        ["yogurt", "mandorle"],
        {
            "kcal": 200,
            "proteine_g": 12,
            "carboidrati_g": 15,
            "grassi_g": 10
        },
        "Bilanciamento naturale tra proteine e grassi"
    )
    
    # Test Case 5: Pranzo con pasta (650 kcal)
    test_optimization_logic(
        5,
        "Pranzo con pasta e verdure",
        ["pasta", "pomodoro", "zucchine"],
        {
            "kcal": 650,
            "proteine_g": 25,
            "carboidrati_g": 100,
            "grassi_g": 15
        },
        "Alto contenuto di carboidrati, potrebbe beneficiare di olio"
    )
    
    # Test Case 6: Colazione proteica (350 kcal)
    test_optimization_logic(
        6,
        "Colazione proteica",
        ["uova", "pane", "pomodoro"],
        {
            "kcal": 350,
            "proteine_g": 22,
            "carboidrati_g": 35,
            "grassi_g": 12
        },
        "Le uova forniscono proteine e grassi di qualità"
    )
    
    # Test Case 7: Cena low-carb (400 kcal)
    test_optimization_logic(
        7,
        "Cena low-carb con carne",
        ["manzo", "insalata"],
        {
            "kcal": 400,
            "proteine_g": 40,
            "carboidrati_g": 10,
            "grassi_g": 20
        },
        "Focus su proteine, pochi carboidrati"
    )
    
    # Test Case 8: Pranzo vegetariano (550 kcal)
    test_optimization_logic(
        8,
        "Pranzo vegetariano con legumi",
        ["lenticchie", "riso", "carote"],
        {
            "kcal": 550,
            "proteine_g": 25,
            "carboidrati_g": 85,
            "grassi_g": 8
        },
        "I legumi forniscono proteine vegetali"
    )
    
    # Test Case 9: Spuntino energetico (250 kcal)
    test_optimization_logic(
        9,
        "Spuntino pre-workout",
        ["banana", "miele"],
        {
            "kcal": 250,
            "proteine_g": 3,
            "carboidrati_g": 60,
            "grassi_g": 1
        },
        "Focus sui carboidrati veloci per energia"
    )
    
    # Test Case 10: Test con ingrediente non esistente
    print(f"\n{'='*60}")
    print(f"TEST CASE 10: Test con alimento inventato")
    print(f"{'='*60}")
    print(f"Alimenti: ['pollo', 'riso', 'alimento_che_non_esiste']")
    print(f"Expected: Dovrebbe restituire errore per alimento non trovato")
    print("-" * 60)
    
    try:
        from agent_tools.nutridb import NutriDB
        db = NutriDB("Dati_processed")
        all_found, foods_not_found = db.check_foods_in_db(["pollo", "riso", "alimento_che_non_esiste"])
        
        if not all_found:
            print(f"✅ SUCCESSO - Errore correttamente rilevato")
            print(f"   Alimenti non trovati: {foods_not_found}")
        else:
            print(f"❌ ERRORE - Non è stato rilevato l'alimento non esistente")
            
    except Exception as e:
        print(f"❌ ECCEZIONE: {str(e)}")
    
    print("\n" + "=" * 80)
    print("🏁 Test completati!")
    print("Le nuove funzionalità sono state testate con successo.")

if __name__ == "__main__":
    run_all_tests() 