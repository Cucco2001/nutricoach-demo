#!/usr/bin/env python3
"""
Script per aggiungere i dati delle vitamine agli alimenti nel database
"""

import json
import os

def update_foods_with_vitamins():
    """Aggiunge i dati delle vitamine agli alimenti nel database"""
    
    # Carica il file degli alimenti
    foods_file = "Dati_processed/banca_alimenti_crea_60alimenti.json"
    with open(foods_file, 'r', encoding='utf-8') as f:
        foods_data = json.load(f)
    
    # Dati delle vitamine per 100g di alimento (valori approssimativi basati su dati nutrizionali standard)
    vitamin_data = {
        # CEREALI E DERIVATI
        "pasta_secca": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.1, "riboflavina_mg": 0.05, "niacina_mg": 1.5,
            "acido_pantotenico_mg": 0.4, "vitamina_B6_mg": 0.1, "biotina_ug": 2.0, "folati_ug": 18.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.5, "vitamina_K_ug": 0.1
        },
        "riso": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.07, "riboflavina_mg": 0.03, "niacina_mg": 1.6,
            "acido_pantotenico_mg": 1.0, "vitamina_B6_mg": 0.16, "biotina_ug": 2.0, "folati_ug": 8.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.1, "vitamina_K_ug": 0.1
        },
        "riso_integrale": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.4, "riboflavina_mg": 0.05, "niacina_mg": 5.1,
            "acido_pantotenico_mg": 1.5, "vitamina_B6_mg": 0.5, "biotina_ug": 12.0, "folati_ug": 20.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 1.2, "vitamina_K_ug": 1.9
        },
        "riso_basmati": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.07, "riboflavina_mg": 0.03, "niacina_mg": 1.6,
            "acido_pantotenico_mg": 1.0, "vitamina_B6_mg": 0.16, "biotina_ug": 2.0, "folati_ug": 8.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.1, "vitamina_K_ug": 0.1
        },
        "pane_bianco": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.1, "riboflavina_mg": 0.06, "niacina_mg": 1.4,
            "acido_pantotenico_mg": 0.4, "vitamina_B6_mg": 0.1, "biotina_ug": 2.0, "folati_ug": 22.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.3, "vitamina_K_ug": 0.3
        },
        
        # CARNI
        "pollo": {
            "vitamina_C_mg": 1.6, "tiamina_mg": 0.07, "riboflavina_mg": 0.12, "niacina_mg": 8.5,
            "acido_pantotenico_mg": 1.0, "vitamina_B6_mg": 0.5, "biotina_ug": 10.0, "folati_ug": 6.0,
            "vitamina_B12_ug": 0.3, "vitamina_A_ug": 16.0, "vitamina_D_ug": 0.1, "vitamina_E_mg": 0.3, "vitamina_K_ug": 2.6
        },
        "pollo_petto": {
            "vitamina_C_mg": 1.6, "tiamina_mg": 0.07, "riboflavina_mg": 0.12, "niacina_mg": 10.9,
            "acido_pantotenico_mg": 1.1, "vitamina_B6_mg": 0.6, "biotina_ug": 10.0, "folati_ug": 4.0,
            "vitamina_B12_ug": 0.3, "vitamina_A_ug": 6.0, "vitamina_D_ug": 0.1, "vitamina_E_mg": 0.3, "vitamina_K_ug": 2.6
        },
        "pollo_coscia": {
            "vitamina_C_mg": 1.6, "tiamina_mg": 0.08, "riboflavina_mg": 0.15, "niacina_mg": 6.2,
            "acido_pantotenico_mg": 1.0, "vitamina_B6_mg": 0.4, "biotina_ug": 10.0, "folati_ug": 8.0,
            "vitamina_B12_ug": 0.3, "vitamina_A_ug": 18.0, "vitamina_D_ug": 0.1, "vitamina_E_mg": 0.3, "vitamina_K_ug": 2.6
        },
        "pollo_ali": {
            "vitamina_C_mg": 1.6, "tiamina_mg": 0.05, "riboflavina_mg": 0.1, "niacina_mg": 6.8,
            "acido_pantotenico_mg": 0.9, "vitamina_B6_mg": 0.4, "biotina_ug": 10.0, "folati_ug": 6.0,
            "vitamina_B12_ug": 0.3, "vitamina_A_ug": 16.0, "vitamina_D_ug": 0.1, "vitamina_E_mg": 0.3, "vitamina_K_ug": 2.6
        },
        
        # VERDURE
        "zucchine": {
            "vitamina_C_mg": 17.9, "tiamina_mg": 0.05, "riboflavina_mg": 0.04, "niacina_mg": 0.5,
            "acido_pantotenico_mg": 0.2, "vitamina_B6_mg": 0.16, "biotina_ug": 1.4, "folati_ug": 24.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 10.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.1, "vitamina_K_ug": 4.3
        },
        "verdure_miste": {
            "vitamina_C_mg": 30.0, "tiamina_mg": 0.08, "riboflavina_mg": 0.1, "niacina_mg": 1.0,
            "acido_pantotenico_mg": 0.3, "vitamina_B6_mg": 0.2, "biotina_ug": 2.0, "folati_ug": 50.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 200.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 1.0, "vitamina_K_ug": 50.0
        },
        
        # GRASSI
        "olio_oliva": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.0, "riboflavina_mg": 0.0, "niacina_mg": 0.0,
            "acido_pantotenico_mg": 0.0, "vitamina_B6_mg": 0.0, "biotina_ug": 0.0, "folati_ug": 0.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 14.4, "vitamina_K_ug": 60.2
        },
        
        # FRUTTA
        "mela": {
            "vitamina_C_mg": 4.6, "tiamina_mg": 0.02, "riboflavina_mg": 0.03, "niacina_mg": 0.1,
            "acido_pantotenico_mg": 0.06, "vitamina_B6_mg": 0.04, "biotina_ug": 0.3, "folati_ug": 3.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 3.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.2, "vitamina_K_ug": 2.2
        },
        "banana": {
            "vitamina_C_mg": 8.7, "tiamina_mg": 0.03, "riboflavina_mg": 0.07, "niacina_mg": 0.7,
            "acido_pantotenico_mg": 0.3, "vitamina_B6_mg": 0.4, "biotina_ug": 5.0, "folati_ug": 20.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 3.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.1, "vitamina_K_ug": 0.5
        },
        "frutti_di_bosco": {
            "vitamina_C_mg": 53.0, "tiamina_mg": 0.02, "riboflavina_mg": 0.04, "niacina_mg": 0.4,
            "acido_pantotenico_mg": 0.1, "vitamina_B6_mg": 0.05, "biotina_ug": 1.0, "folati_ug": 25.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 11.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.6, "vitamina_K_ug": 19.3
        },
        
        # UOVA E LATTICINI
        "uovo": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.04, "riboflavina_mg": 0.46, "niacina_mg": 0.1,
            "acido_pantotenico_mg": 1.4, "vitamina_B6_mg": 0.17, "biotina_ug": 20.0, "folati_ug": 47.0,
            "vitamina_B12_ug": 0.9, "vitamina_A_ug": 140.0, "vitamina_D_ug": 2.0, "vitamina_E_mg": 1.1, "vitamina_K_ug": 0.3
        },
        "uova": {
            "vitamina_C_mg": 0.0, "tiamina_mg": 0.04, "riboflavina_mg": 0.46, "niacina_mg": 0.1,
            "acido_pantotenico_mg": 1.4, "vitamina_B6_mg": 0.17, "biotina_ug": 20.0, "folati_ug": 47.0,
            "vitamina_B12_ug": 0.9, "vitamina_A_ug": 140.0, "vitamina_D_ug": 2.0, "vitamina_E_mg": 1.1, "vitamina_K_ug": 0.3
        },
        "latte_intero": {
            "vitamina_C_mg": 1.0, "tiamina_mg": 0.04, "riboflavina_mg": 0.18, "niacina_mg": 0.1,
            "acido_pantotenico_mg": 0.4, "vitamina_B6_mg": 0.04, "biotina_ug": 3.5, "folati_ug": 5.0,
            "vitamina_B12_ug": 0.4, "vitamina_A_ug": 28.0, "vitamina_D_ug": 0.03, "vitamina_E_mg": 0.09, "vitamina_K_ug": 0.4
        },
        "latte_scremato": {
            "vitamina_C_mg": 1.0, "tiamina_mg": 0.04, "riboflavina_mg": 0.17, "niacina_mg": 0.1,
            "acido_pantotenico_mg": 0.4, "vitamina_B6_mg": 0.04, "biotina_ug": 3.5, "folati_ug": 5.0,
            "vitamina_B12_ug": 0.4, "vitamina_A_ug": 1.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.01, "vitamina_K_ug": 0.1
        },
        
        # LEGUMI
        "fagioli_borlotti_cotti": {
            "vitamina_C_mg": 1.2, "tiamina_mg": 0.15, "riboflavina_mg": 0.06, "niacina_mg": 0.5,
            "acido_pantotenico_mg": 0.2, "vitamina_B6_mg": 0.11, "biotina_ug": 5.0, "folati_ug": 130.0,
            "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.2, "vitamina_K_ug": 8.4
        }
    }
    
    # Aggiungi i dati delle vitamine a tutti gli alimenti
    for food_name, food_data in foods_data.items():
        if food_name in vitamin_data:
            # Aggiungi i dati delle vitamine
            food_data.update(vitamin_data[food_name])
        else:
            # Se non abbiamo dati specifici, aggiungi valori di default (0 per la maggior parte)
            default_vitamins = {
                "vitamina_C_mg": 0.0, "tiamina_mg": 0.0, "riboflavina_mg": 0.0, "niacina_mg": 0.0,
                "acido_pantotenico_mg": 0.0, "vitamina_B6_mg": 0.0, "biotina_ug": 0.0, "folati_ug": 0.0,
                "vitamina_B12_ug": 0.0, "vitamina_A_ug": 0.0, "vitamina_D_ug": 0.0, "vitamina_E_mg": 0.0, "vitamina_K_ug": 0.0
            }
            food_data.update(default_vitamins)
    
    # Salva il file aggiornato
    with open(foods_file, 'w', encoding='utf-8') as f:
        json.dump(foods_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ File {foods_file} aggiornato con i dati delle vitamine!")
    print(f"📊 Aggiornati {len(foods_data)} alimenti")
    
    # Mostra un esempio
    example_food = list(foods_data.keys())[0]
    print(f"\n📋 Esempio - {example_food}:")
    for key, value in foods_data[example_food].items():
        if 'vitamina' in key or 'tiamina' in key or 'riboflavina' in key or 'niacina' in key or 'acido_pantotenico' in key or 'biotina' in key or 'folati' in key:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    update_foods_with_vitamins() 