#!/usr/bin/env python3
"""
Test script per la nuova funzionalità di meal optimization
Testa 10 casi diversi per verificare il corretto funzionamento
"""

import json
import sys
import os

# Aggiungi il path per importare i moduli
sys.path.append('.')

from agent_tools.meal_optimization_tool import optimize_meal_portions

def test_case(case_num, description, meal_name, food_list, expected_behavior=""):
    """
    Esegue un singolo test case
    """
    print(f"\n{'='*60}")
    print(f"TEST CASE {case_num}: {description}")
    print(f"{'='*60}")
    print(f"Pasto: {meal_name}")
    print(f"Alimenti: {food_list}")
    if expected_behavior:
        print(f"Expected: {expected_behavior}")
    print("-" * 60)
    
    try:
        # Esegui l'ottimizzazione
        result = optimize_meal_portions(meal_name, food_list)
        
        # Stampa i risultati
        print("RISULTATO:")
        if not result.get("success", False):
            print(f"❌ ERRORE: {result.get('error_message', 'Errore sconosciuto')}")
        else:
            print(f"✅ SUCCESSO")
            
            # Mostra gli alimenti finali (potrebbe essere diverso dalla lista originale)
            final_foods = result.get("foods_included", food_list)
            print(f"   Alimenti finali: {final_foods}")
            
            # Stampa le porzioni
            portions = result.get("portions", {})
            print(f"   Porzioni:")
            for food, grams in portions.items():
                print(f"     {food}: {grams}g")
            
            # Stampa i macros ottenuti
            actual = result.get("actual_nutrients", {})
            target = result.get("target_nutrients", {})
            
            print(f"   Macros ottenuti vs target:")
            print(f"     Calorie: {actual.get('kcal', 0):.1f} / {target.get('kcal', 0):.1f}")
            print(f"     Proteine: {actual.get('proteine_g', 0):.1f}g / {target.get('proteine_g', 0):.1f}g")
            print(f"     Carboidrati: {actual.get('carboidrati_g', 0):.1f}g / {target.get('carboidrati_g', 0):.1f}g")
            print(f"     Grassi: {actual.get('grassi_g', 0):.1f}g / {target.get('grassi_g', 0):.1f}g")
            
            # Mostra le ottimizzazioni automatiche applicate
            optimizations = []
            if result.get("oil_added"):
                optimizations.append("Olio aggiunto automaticamente")
            if result.get("protein_added"):
                optimizations.append(f"Proteina aggiunta: {result.get('protein_adjustment_food')}")
            if result.get("protein_removed"):
                optimizations.append(f"Proteina rimossa: {result.get('protein_adjustment_food')}")
            if result.get("carb_added"):
                optimizations.append(f"Carboidrato aggiunto: {result.get('carb_adjustment_food')}")
            if result.get("carb_substituted"):
                optimizations.append(f"Sostituzione: {result.get('carb_substitution_type')}")
            
            if optimizations:
                print(f"   🎯 Ottimizzazioni automatiche:")
                for opt in optimizations:
                    print(f"     • {opt}")
            
            # Mostra il summary
            summary = result.get("optimization_summary", "")
            if summary:
                print(f"   📋 Summary: {summary}")
            
    except Exception as e:
        print(f"❌ ECCEZIONE: {str(e)}")
        import traceback
        traceback.print_exc()

def run_all_tests():
    """
    Esegue tutti i test cases
    """
    print("🚀 Avvio test della nuova funzionalità di meal optimization")
    print("=" * 80)
    
    # Test Case 1: Colazione semplice
    test_case(
        1,
        "Colazione semplice con cereali e frutta",
        "colazione",
        ["avena", "latte", "banana"],
        "Dovrebbe ottimizzare porzioni per una colazione equilibrata"
    )
    
    # Test Case 2: Pranzo classico 
    test_case(
        2,
        "Pranzo classico con proteine e carboidrati",
        "pranzo",
        ["pollo", "riso", "broccoli"],
        "Dovrebbe aggiungere olio automaticamente se migliora l'ottimizzazione"
    )
    
    # Test Case 3: Cena con pesce
    test_case(
        3,
        "Cena con pesce e verdure",
        "cena",
        ["salmone", "patate", "spinaci"],
        "Dovrebbe testare aggiunta olio e ottimizzazioni intelligenti"
    )
    
    # Test Case 4: Spuntino semplice
    test_case(
        4,
        "Spuntino con yogurt e frutta secca",
        "spuntino",
        ["yogurt", "mandorle"],
        "Non dovrebbe aggiungere olio (non è pranzo/cena)"
    )
    
    # Test Case 5: Pranzo con pasta
    test_case(
        5,
        "Pranzo con pasta e verdure",
        "pranzo",
        ["pasta", "pomodoro", "zucchine"],
        "Potrebbe sostituire pasta con riso se migliora carboidrati"
    )
    
    # Test Case 6: Colazione proteica
    test_case(
        6,
        "Colazione proteica",
        "colazione",
        ["uova", "pane", "pomodoro"],
        "Dovrebbe bilanciare senza ottimizzazioni automatiche eccessive"
    )
    
    # Test Case 7: Cena low-carb 
    test_case(
        7,
        "Cena low-carb con carne",
        "cena",
        ["manzo", "insalata"],
        "Potrebbe aggiungere pane se servono più carboidrati"
    )
    
    # Test Case 8: Pranzo vegetariano
    test_case(
        8,
        "Pranzo vegetariano con legumi",
        "pranzo",
        ["lenticchie", "riso", "carote"],
        "Dovrebbe ottimizzare senza fonti animali"
    )
    
    # Test Case 9: Spuntino energetico
    test_case(
        9,
        "Spuntino pre-workout",
        "spuntino",
        ["banana", "miele"],
        "Dovrebbe privilegiare carboidrati veloci"
    )
    
    # Test Case 10: Test con alimento non esistente
    test_case(
        10,
        "Test con alimento inventato",
        "pranzo",
        ["pollo", "riso", "alimento_che_non_esiste"],
        "Dovrebbe restituire errore per alimento non trovato"
    )
    
    print("\n" + "=" * 80)
    print("🏁 Test completati!")
    print("Verifica i risultati sopra per valutare le nuove funzionalità.")

if __name__ == "__main__":
    run_all_tests() 