#!/usr/bin/env python3
"""
Crea un database di sostituti alimentari logici basato su categorie alimentari sensate
"""

import json
import math
from typing import Dict, List, Tuple

def load_foods_data():
    """Carica i dati degli alimenti"""
    with open('Dati_processed/banca_alimenti_crea_60alimenti.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def define_food_categories():
    """Definisce categorie alimentari logiche"""
    return {
        # CEREALI E DERIVATI
        "cereali_pasta": [
            "pasta_secca", "pasta_integrale", "riso", "riso_integrale", "riso_basmati",
            "avena", "cornflakes"
        ],
        
        # PANE E PRODOTTI DA FORNO
        "pane_prodotti_forno": [
            "pane_bianco", "crostata_di_marmellata"
        ],
        
        # PROTEINE ANIMALI - CARNI
        "carni_bianche": [
            "pollo", "pollo_petto", "pollo_coscia", "pollo_ali"
        ],
        
        # PROTEINE ANIMALI - PESCI
        "pesci": [
            "tonno_naturale", "tonno_sottolio_sgocciolato", "salmone_al_naturale", 
            "salmone_affumicato", "pesce_spada"
        ],
        
        # PROTEINE ANIMALI - SALUMI
        "salumi": [
            "bresaola", "prosciutto_crudo"
        ],
        
        # PROTEINE - INTEGRATORI
        "proteine_integratori": [
            "iso_fuji_yamamoto", "pro_milk_20g_proteine"
        ],
        
        # LATTICINI
        "latticini_latte": [
            "latte_intero", "latte_scremato"
        ],
        
        "latticini_yogurt": [
            "yogurt_greco_0percento", "yogurt_greco_2percento", "yogurt_magro"
        ],
        
        "latticini_gelati": [
            "gelato_cioccolato", "gelato_fiordilatte"
        ],
        
        # UOVA
        "uova": [
            "uovo", "uova", "albume_uova"
        ],
        
        # GRASSI E OLI
        "grassi_oli": [
            "olio_oliva", "burro", "margarina"
        ],
        
        "frutta_secca": [
            "noci_sgusciate", "mandorle", "burro_arachidi"
        ],
        
        # VERDURE
        "verdure_foglia": [
            "verdure_miste", "spinaci_cotti"
        ],
        
        "verdure_varie": [
            "zucchine", "melanzane", "carote_crude"
        ],
        
        # FRUTTA
        "frutta_dolce": [
            "mela", "pera", "banana", "uva"
        ],
        
        "frutta_agrumi": [
            "arancia"
        ],
        
        "frutta_estiva": [
            "albicocche", "frutti_di_bosco"
        ]
    }

def get_food_category(food_name: str, categories: Dict[str, List[str]]) -> str:
    """Trova la categoria di un alimento"""
    for category, foods in categories.items():
        if food_name in foods:
            return category
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

def calculate_logical_substitutes():
    """Calcola sostituti logici basati su categorie e macronutrienti"""
    
    foods_data = load_foods_data()
    categories = define_food_categories()
    
    substitutes = {}
    
    for food_name, food_data in foods_data.items():
        food_category = get_food_category(food_name, categories)
        food_kcal = food_data.get('energia_kcal', 0)
        
        if food_kcal == 0:
            continue
        
        candidates = []
        
        # Trova candidati nella stessa categoria
        same_category_foods = categories.get(food_category, [])
        
        for candidate_name, candidate_data in foods_data.items():
            if candidate_name == food_name:
                continue
            
            candidate_category = get_food_category(candidate_name, categories)
            candidate_kcal = candidate_data.get('energia_kcal', 0)
            
            if candidate_kcal == 0:
                continue
            
            # Calcola equivalenza calorica (grammi necessari per uguagliare 100g del cibo di riferimento)
            equivalent_grams = (food_kcal / candidate_kcal) * 100
            
            # Calcola similarità macronutrienti
            macro_similarity = calculate_macronutrient_similarity(food_data, candidate_data)
            
            # Bonus per stessa categoria
            category_bonus = 0
            if candidate_category == food_category:
                category_bonus = 30  # Bonus significativo per stessa categoria
            elif self._are_related_categories(food_category, candidate_category):
                category_bonus = 15  # Bonus minore per categorie correlate
            
            # Penalità per grammature irrealistiche
            gram_penalty = 0
            if equivalent_grams > 500:  # Se servono più di 500g
                gram_penalty = min(30, (equivalent_grams - 500) / 20)  # Penalità crescente
            elif equivalent_grams < 20:  # Se servono meno di 20g
                gram_penalty = min(20, (20 - equivalent_grams) / 2)
            
            # Score finale
            final_score = macro_similarity + category_bonus - gram_penalty
            
            # Filtri di esclusione logica
            if self._should_exclude_combination(food_name, candidate_name, food_category, candidate_category):
                continue
            
            # Solo candidati con score ragionevole
            if final_score >= 60:  # Soglia più alta per qualità
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

def _are_related_categories(cat1: str, cat2: str) -> bool:
    """Verifica se due categorie sono correlate"""
    related_groups = [
        ["cereali_pasta", "pane_prodotti_forno"],  # Carboidrati complessi
        ["carni_bianche", "pesci", "salumi"],      # Proteine animali
        ["latticini_latte", "latticini_yogurt"],   # Latticini liquidi/cremosi
        ["grassi_oli", "frutta_secca"],            # Grassi
        ["verdure_foglia", "verdure_varie"],       # Verdure
        ["frutta_dolce", "frutta_agrumi", "frutta_estiva"],  # Frutta
        ["proteine_integratori", "carni_bianche", "pesci"]   # Proteine ad alto valore
    ]
    
    for group in related_groups:
        if cat1 in group and cat2 in group:
            return True
    return False

def _should_exclude_combination(food1: str, food2: str, cat1: str, cat2: str) -> bool:
    """Esclude combinazioni illogiche"""
    
    # Esclusioni specifiche illogiche
    illogical_combinations = [
        # Verdure non possono sostituire cereali/pasta
        (["verdure_foglia", "verdure_varie"], ["cereali_pasta", "pane_prodotti_forno"]),
        # Frutta non può sostituire cereali/pasta (tranne in casi molto specifici)
        (["frutta_dolce", "frutta_agrumi", "frutta_estiva"], ["cereali_pasta", "pane_prodotti_forno"]),
        # Cereali non possono sostituire verdure
        (["cereali_pasta", "pane_prodotti_forno"], ["verdure_foglia", "verdure_varie"]),
        # Proteine non possono sostituire verdure
        (["carni_bianche", "pesci", "salumi"], ["verdure_foglia", "verdure_varie"]),
    ]
    
    for group1, group2 in illogical_combinations:
        if (cat1 in group1 and cat2 in group2) or (cat1 in group2 and cat2 in group1):
            return True
    
    return False

def create_logical_substitutes_database():
    """Crea il database finale dei sostituti logici"""
    
    print("🔄 Generazione database sostituti alimentari logici...")
    
    substitutes = calculate_logical_substitutes()
    
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
    # Aggiungi i metodi mancanti alla classe globale
    def are_related_categories(cat1: str, cat2: str) -> bool:
        return _are_related_categories(cat1, cat2)
    
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
                
                # Calcola equivalenza calorica
                equivalent_grams = (food_kcal / candidate_kcal) * 100
                
                # Calcola similarità macronutrienti
                macro_similarity = calculate_macronutrient_similarity(food_data, candidate_data)
                
                # Bonus per stessa categoria
                category_bonus = 0
                if candidate_category == food_category:
                    category_bonus = 30
                elif are_related_categories(food_category, candidate_category):
                    category_bonus = 15
                
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