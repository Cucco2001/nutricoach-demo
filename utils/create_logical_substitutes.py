#!/usr/bin/env python3
"""
Crea un database di sostituti alimentari logici basato su categorie alimentari sensate
"""

import json
import math
from typing import Dict, List, Tuple

# CONFIGURAZIONE: Categorie che possono avere sostituti da altre categorie
# Tutte le altre categorie avranno sostituti SOLO dalla propria categoria
CATEGORIES_WITH_EXTERNAL_SUBSTITUTES = {
    "tuberi",
    "uova"
}

def load_foods_data():
    """Carica i dati degli alimenti"""
    with open('Dati_processed/banca_alimenti_crea_60alimenti.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_food_categories_from_database():
    """Estrae le categorie direttamente dalla banca alimenti"""
    foods_data = load_foods_data()
    categories = {}
    
    # Raggruppa gli alimenti per categoria
    for food_name, food_data in foods_data.items():
        categoria = food_data.get('categoria', 'uncategorized')
        if categoria not in categories:
            categories[categoria] = []
        categories[categoria].append(food_name)
    
    return categories

def define_food_categories():
    """Definisce categorie alimentari basate sulla banca alimenti"""
    # Ottieni le categorie direttamente dalla banca alimenti
    return get_food_categories_from_database()

def get_food_category(food_name: str, categories: Dict[str, List[str]] = None) -> str:
    """Trova la categoria di un alimento direttamente dalla banca alimenti"""
    foods_data = load_foods_data()
    if food_name in foods_data:
        return foods_data[food_name].get('categoria', 'uncategorized')
    return "uncategorized"

def calculate_macronutrient_similarity(food1_data: Dict, food2_data: Dict) -> float:
    """Calcola la similarità basata sui macronutrienti (0-100)"""
    
    def get_macro_percentages(food_data):
        kcal = food_data.get('energia_kcal', 0)
        if kcal == 0:
            return [0, 0, 0]
        
        prot_kcal = food_data.get('proteine_g', 0) * 4
        carb_kcal = food_data.get('carboidrati_g', 0) * 4
        fat_kcal = food_data.get('grassi_g', 0) * 9
        
        total_macro_kcal = prot_kcal + carb_kcal + fat_kcal
        if total_macro_kcal == 0:
            return [0, 0, 0]
        
        return [
            (prot_kcal / total_macro_kcal) * 100,
            (carb_kcal / total_macro_kcal) * 100,
            (fat_kcal / total_macro_kcal) * 100
        ]
    
    macro1 = get_macro_percentages(food1_data)
    macro2 = get_macro_percentages(food2_data)
    
    # Calcola distanza euclidea tra percentuali macronutrienti
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(macro1, macro2)))
    
    # Converte in similarità (0-100, dove 100 = identico)
    max_distance = math.sqrt(3 * (100 ** 2))  # Distanza massima possibile
    similarity = max(0, 100 - (distance / max_distance) * 100)
    
    return similarity



def _should_exclude_combination(food1: str, food2: str, cat1: str, cat2: str) -> bool:
    """Esclude combinazioni illogiche basandosi sulle categorie della banca alimenti"""
    
    # Esclusioni specifiche illogiche
    illogical_combinations = [
        # Verdure non possono sostituire cereali/carboidrati
        (["verdure"], ["cereali", "cereali_colazione", "tuberi"]),
        # Frutta non può sostituire cereali/carboidrati (tranne in casi molto specifici)
        (["frutta"], ["cereali", "cereali_colazione", "tuberi"]),
        # Cereali non possono sostituire verdure
        (["cereali", "cereali_colazione", "tuberi"], ["verdure"]),
        # Proteine animali non possono sostituire verdure
        (["proteine_animali"], ["verdure"]),
        # Grassi non possono sostituire verdure
        (["grassi_aggiunti"], ["verdure"]),
        # Verdure non possono sostituire grassi
        (["verdure"], ["grassi_aggiunti", "frutta_secca"]),
        # Dolci non possono sostituire proteine
        (["dolci"], ["proteine_animali", "legumi", "uova"]),
        # Proteine non possono sostituire dolci
        (["proteine_animali", "legumi", "uova"], ["dolci"]),
    ]
    
    for group1, group2 in illogical_combinations:
        if (cat1 in group1 and cat2 in group2) or (cat1 in group2 and cat2 in group1):
            return True
    
    return False

def create_logical_substitutes_database():
    """Crea il database finale dei sostituti logici"""
    
    print("🔄 Generazione database sostituti alimentari logici...")
    
    substitutes = patched_calculate_logical_substitutes()
    
    # Conta le categorie
    foods_data = load_foods_data()
    categories = define_food_categories()
    
    category_counts = {}
    for food_name in foods_data.keys():
        category = get_food_category(food_name, categories)
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Crea il database finale
    database = {
        "metadata": {
            "description": "Database di alimenti sostitutivi basato su categorie alimentari logiche e macronutrienti",
            "reference_amount": "100g",
            "calculation_method": "Equivalenza calorica con priorità per categorie alimentari logiche e similarità macronutrienti",
            "categories": category_counts,
            "algorithm_version": "2.0_logical",
            "filters_applied": [
                "Bonus +30 per stessa categoria alimentare",
                "Bonus +15 per categorie correlate", 
                "Penalità per grammature irrealistiche (>500g o <20g)",
                "Esclusione combinazioni illogiche (es: verdure↔cereali)",
                "Soglia minima score: 60"
            ]
        },
        "substitutes": substitutes
    }
    
    # Salva il database
    output_file = 'Dati_processed/alimenti_sostitutivi.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Database salvato in: {output_file}")
    print(f"📊 Alimenti processati: {len(substitutes)}")
    print(f"📂 Categorie identificate: {len(category_counts)}")
    
    # Mostra statistiche
    total_substitutes = sum(len(subs) for subs in substitutes.values())
    avg_substitutes = total_substitutes / len(substitutes) if substitutes else 0
    
    print(f"🔄 Sostituti totali generati: {total_substitutes}")
    print(f"📈 Media sostituti per alimento: {avg_substitutes:.1f}")
    
    return database

if __name__ == "__main__":
    
    def should_exclude_combination(food1: str, food2: str, cat1: str, cat2: str) -> bool:
        return _should_exclude_combination(food1, food2, cat1, cat2)
    
    # Sostituisci i riferimenti self con chiamate dirette
    import types
    
    def patched_calculate_logical_substitutes():
        """Versione corretta della funzione"""
        foods_data = load_foods_data()
        categories = define_food_categories()
        
        substitutes = {}
        
        for food_name, food_data in foods_data.items():
            food_category = get_food_category(food_name, categories)
            food_kcal = food_data.get('energia_kcal', 0)
            
            if food_kcal == 0:
                continue
            
            candidates = []
            
            for candidate_name, candidate_data in foods_data.items():
                if candidate_name == food_name:
                    continue
                
                candidate_category = get_food_category(candidate_name, categories)
                candidate_kcal = candidate_data.get('energia_kcal', 0)
                
                if candidate_kcal == 0:
                    continue
                
                # NUOVO FILTRO: Limita i sostituti alla stessa categoria, 
                # tranne per le categorie specificate in CATEGORIES_WITH_EXTERNAL_SUBSTITUTES
                if food_category not in CATEGORIES_WITH_EXTERNAL_SUBSTITUTES:
                    if candidate_category != food_category:
                        continue  # Salta candidati di categorie diverse
                
                # Calcola equivalenza calorica
                equivalent_grams = (food_kcal / candidate_kcal) * 100
                
                # Calcola similarità macronutrienti
                macro_similarity = calculate_macronutrient_similarity(food_data, candidate_data)
                
                # Bonus per stessa categoria
                category_bonus = 0
                if candidate_category == food_category:
                    category_bonus = 30
                
                # Penalità per grammature irrealistiche
                gram_penalty = 0
                if equivalent_grams > 500:
                    gram_penalty = min(30, (equivalent_grams - 500) / 20)
                elif equivalent_grams < 20:
                    gram_penalty = min(20, (20 - equivalent_grams) / 2)
                
                # Score finale
                final_score = macro_similarity + category_bonus - gram_penalty
                
                # Filtri di esclusione logica
                if should_exclude_combination(food_name, candidate_name, food_category, candidate_category):
                    continue
                
                # Solo candidati con score ragionevole
                if final_score >= 60:
                    candidates.append({
                        'name': candidate_name,
                        'grams': round(equivalent_grams, 1),
                        'similarity_score': round(final_score, 1),
                        'category': candidate_category,
                        'macro_similarity': round(macro_similarity, 1),
                        'category_bonus': category_bonus
                    })
            
            # Ordina per score e prendi i migliori 5
            candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
            top_candidates = candidates[:5]
            
            if top_candidates:
                substitutes[food_name] = {}
                for candidate in top_candidates:
                    substitutes[food_name][candidate['name']] = {
                        'grams': candidate['grams'],
                        'similarity_score': candidate['similarity_score']
                    }
        
        return substitutes
    
    # Sostituisci la funzione
    calculate_logical_substitutes = patched_calculate_logical_substitutes
    
    database = create_logical_substitutes_database() 