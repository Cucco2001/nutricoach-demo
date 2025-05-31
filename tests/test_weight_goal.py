#!/usr/bin/env python3
"""
Test script per la funzione calculate_weight_goal_calories
"""

from agent_tools.nutridb_tool import calculate_weight_goal_calories

def test_weight_loss():
    """Test per perdita di peso"""
    print("=== TEST PERDITA DI PESO ===")
    result = calculate_weight_goal_calories(
        kg_change=5,
        time_months=6,
        goal_type="perdita_peso"
    )
    print(f"Risultato: {result}")
    print()

def test_weight_gain():
    """Test per aumento di peso"""
    print("=== TEST AUMENTO DI PESO ===")
    result = calculate_weight_goal_calories(
        kg_change=5,
        time_months=6,
        goal_type="aumento_massa"
    )
    print(f"Risultato: {result}")
    print()

def test_excessive_deficit():
    """Test per deficit eccessivo"""
    print("=== TEST DEFICIT ECCESSIVO ===")
    result = calculate_weight_goal_calories(
        kg_change=15,  # 15 kg da perdere
        time_months=3, # in 3 mesi = troppo veloce
        goal_type="perdita_peso",
        bmr=1800
    )
    print(f"Risultato: {result}")
    print()

def test_excessive_gain():
    """Test per aumento eccessivo"""
    print("=== TEST AUMENTO ECCESSIVO ===")
    result = calculate_weight_goal_calories(
        kg_change=10,  # 10 kg da aumentare
        time_months=6, # in 6 mesi = >1 kg/mese
        goal_type="aumento_massa"
    )
    print(f"Risultato: {result}")
    print()

if __name__ == "__main__":
    test_weight_loss()
    test_weight_gain()
    test_excessive_deficit()
    test_excessive_gain() 