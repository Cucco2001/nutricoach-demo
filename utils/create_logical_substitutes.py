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

# CONFIGURAZIONE: Categorie correlate che ricevono bonus tra loro
RELATED_CATEGORIES = {
    "latte": ["formaggi", "latticini"],
    "formaggi": ["latte", "latticini"], 
    "latticini": ["latte", "formaggi"],
    "tuberi": ["cereali"],
    "cereali": ["tuberi"]
}

# CONFIGURAZIONE: Categorie incompatibili che ricevono malus tra loro
INCOMPATIBLE_CATEGORIES = {
    "verdure": ["latte", "formaggi", "latticini"],
    "latte": ["verdure", "frutta", "legumi", "cereali"],
    "formaggi": ["verdure"],
    "latticini": ["verdure"],
    "frutta": ["latte", "formaggi", "latticini"],
    "legumi": ["latte", "formaggi", "latticini"]
}

# CONFIGURAZIONE: Alimenti che non devono avere sostituti
FOODS_WITHOUT_SUBSTITUTES = {
    "caffe"
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

def are_categories_related(cat1: str, cat2: str) -> bool:
    """Verifica se due categorie sono correlate"""
    if cat1 == cat2:
        return False  # Stessa categoria, non correlata
    
    return cat2 in RELATED_CATEGORIES.get(cat1, [])

def are_categories_incompatible(cat1: str, cat2: str) -> bool:
    """Verifica se due categorie sono incompatibili"""
    if cat1 == cat2:
        return False  # Stessa categoria, non incompatibile
    
    return cat2 in INCOMPATIBLE_CATEGORIES.get(cat1, [])

def calculate_macronutrient_similarity(food1_data: Dict, food2_data: Dict) -> float:
    """
    Calcola la similarità basata sui macronutrienti (0-100)
    Priorità al macronutriente dominante, peso minore agli altri
    """
    
    def get_macro_percentages_and_dominant(food_data):
        kcal = food_data.get('energia_kcal', 0)
        if kcal == 0:
            return [0, 0, 0], 0
        
        prot_kcal = food_data.get('proteine_g', 0) * 4
        carb_kcal = food_data.get('carboidrati_g', 0) * 4
        fat_kcal = food_data.get('grassi_g', 0) * 9
        
        total_macro_kcal = prot_kcal + carb_kcal + fat_kcal
        if total_macro_kcal == 0:
            return [0, 0, 0], 0
        
        percentages = [
            (prot_kcal / total_macro_kcal) * 100,  # 0: proteine
            (carb_kcal / total_macro_kcal) * 100,  # 1: carboidrati
            (fat_kcal / total_macro_kcal) * 100    # 2: grassi
        ]
        
        # Trova il macronutriente dominante (indice del maggiore)
        dominant_macro = percentages.index(max(percentages))
        
        return percentages, dominant_macro
    
    macro1, dominant1 = get_macro_percentages_and_dominant(food1_data)
    macro2, dominant2 = get_macro_percentages_and_dominant(food2_data)
    
    # Se hanno macronutrienti dominanti diversi, penalità importante
    if dominant1 != dominant2:
        # Calcola distanza pesata: 70% peso al macro dominante, 30% agli altri
        dominant_diff = abs(macro1[dominant1] - macro2[dominant1])
        other_diff = abs(macro1[dominant2] - macro2[dominant2])
        
        # Distanza pesata per macro dominanti diversi
        weighted_distance = (dominant_diff * 0.7) + (other_diff * 0.3)
        similarity = max(0, 100 - (weighted_distance * 1.5))  # Moltiplicatore per penalizzare
        
    else:
        # Stesso macro dominante: calcola similarità più accurata
        # 60% peso al macro dominante, 20% ciascuno agli altri due
        dominant_diff = abs(macro1[dominant1] - macro2[dominant1])
        
        # Altri due macro
        other_indices = [i for i in range(3) if i != dominant1]
        other_diff_sum = sum(abs(macro1[i] - macro2[i]) for i in other_indices)
        
        # Distanza pesata per stesso macro dominante
        weighted_distance = (dominant_diff * 0.6) + (other_diff_sum * 0.2)
        similarity = max(0, 100 - weighted_distance)
    
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
            "calculation_method": "Equivalenza calorica con priorità per categorie alimentari logiche e similarità macronutrienti dominanti",
            "categories": category_counts,
            "algorithm_version": "2.3_gram_distance_penalty",
            "filters_applied": [
                "Similarità basata su macronutriente dominante (60-70% peso)",
                "Penalità importante per macro dominanti diversi (moltiplicatore 1.5)",
                "Penalità proporzionale distanza da 100g ideali: |grammi-100|/10 (max 20 punti)",
                "Malus categorie incompatibili: verdure/frutta/legumi ↔ latte/formaggi",
                "5 sostituti migliori dalla categoria principale (soglia: 60)",
                "5 sostituti aggiuntivi da tutte le categorie (soglia: 45)",
                "Bonus +30 stessa categoria, +35/+30 correlate, -20/-15 incompatibili",
                "Penalità per grammature irrealistiche (>500g o <20g)",
                "Penalità -20 per burro, pollo_ali e gelati come sostituti",
                "Penalità -25 per sostituti aggiuntivi (garantisce priorità ai primi 5)",
                "Esclusione combinazioni illogiche (es: verdure↔cereali)",
                "Massimo 10 sostituti totali per alimento"
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
            # Salta gli alimenti che non devono avere sostituti
            if food_name.lower() in FOODS_WITHOUT_SUBSTITUTES:
                continue
                
            food_category = get_food_category(food_name, categories)
            food_kcal = food_data.get('energia_kcal', 0)
            
            if food_kcal == 0:
                continue
            
            candidates = []
            
            for candidate_name, candidate_data in foods_data.items():
                if candidate_name == food_name:
                    continue
                
                # Salta gli alimenti che non possono essere usati come sostituti
                if candidate_name.lower() in FOODS_WITHOUT_SUBSTITUTES:
                    continue
                
                candidate_category = get_food_category(candidate_name, categories)
                candidate_kcal = candidate_data.get('energia_kcal', 0)
                
                if candidate_kcal == 0:
                    continue
                
                # NUOVO FILTRO: Limita i sostituti alla stessa categoria o categorie correlate, 
                # tranne per le categorie specificate in CATEGORIES_WITH_EXTERNAL_SUBSTITUTES
                if food_category not in CATEGORIES_WITH_EXTERNAL_SUBSTITUTES:
                    if candidate_category != food_category and not are_categories_related(food_category, candidate_category):
                        continue  # Salta candidati di categorie diverse e non correlate
                
                # Calcola equivalenza calorica
                equivalent_grams = (food_kcal / candidate_kcal) * 100
                
                # Calcola similarità macronutrienti
                macro_similarity = calculate_macronutrient_similarity(food_data, candidate_data)
                
                # Bonus/Malus per categorie
                category_bonus = 0
                if candidate_category == food_category:
                    category_bonus = 30
                elif are_categories_related(food_category, candidate_category):
                    category_bonus = 35  # Bonus aumentato per categorie correlate
                elif are_categories_incompatible(food_category, candidate_category):
                    category_bonus = -30  # Malus per categorie incompatibili
                
                # Penalità per grammature irrealistiche
                gram_penalty = 0
                if equivalent_grams > 500:
                    gram_penalty = min(30, (equivalent_grams - 500) / 20)
                elif equivalent_grams < 20:
                    gram_penalty = min(20, (20 - equivalent_grams) / 2)
                
                # NUOVA PENALITÀ: Distanza dalle grammature ideali (100g)
                # Penalità sempre proporzionale alla distanza dall'ideale
                gram_distance_penalty = 0
                distance_from_ideal = abs(equivalent_grams - 100)
                # Penalità proporzionale: più ci si allontana da 100g, più penalità
                # Formula: distanza / 10 con cap a 20 punti massimi
                gram_distance_penalty = min(20, distance_from_ideal / 10)
                
                # Penalità specifiche per scoraggiare certi alimenti come sostituti
                food_penalty = 0
                if "burro" in candidate_name.lower():
                    food_penalty = 20  # Penalità per il burro
                elif candidate_name.lower() == "pollo_ali":
                    food_penalty = 70  # Penalità per ali di pollo
                elif "gelato" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "gelato_fiordilatte" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "caffe" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "zucchero" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                
                # Score finale
                final_score = macro_similarity + category_bonus - gram_penalty - gram_distance_penalty - food_penalty
                
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
            
            # Ordina per score e prendi i migliori 5 della categoria principale
            candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
            top_candidates = candidates[:5]
            
            # NUOVA FUNZIONALITÀ: Aggiungi 5 sostituti migliori da TUTTE le categorie
            # (escludendo quelli già trovati nell'analisi principale)
            already_found_names = {candidate['name'] for candidate in top_candidates}
            
            # Cerca candidati da tutte le categorie (senza limitazioni di categoria)
            all_category_candidates = []
            
            for candidate_name, candidate_data in foods_data.items():
                if candidate_name == food_name or candidate_name in already_found_names:
                    continue
                
                # Salta gli alimenti che non possono essere usati come sostituti
                if candidate_name.lower() in FOODS_WITHOUT_SUBSTITUTES:
                    continue
                
                candidate_category = get_food_category(candidate_name, categories)
                candidate_kcal = candidate_data.get('energia_kcal', 0)
                
                if candidate_kcal == 0:
                    continue
                
                # Calcola equivalenza calorica
                equivalent_grams = (food_kcal / candidate_kcal) * 100
                
                # Calcola similarità macronutrienti
                macro_similarity = calculate_macronutrient_similarity(food_data, candidate_data)
                
                # Bonus/Malus per categorie (ridotto per varietà)
                category_bonus = 0
                if candidate_category == food_category:
                    category_bonus = 30  
                elif are_categories_related(food_category, candidate_category):
                    category_bonus = 30   # Bonus per categorie correlate nei sostituti aggiuntivi
                elif are_categories_incompatible(food_category, candidate_category):
                    category_bonus = -30  # Malus ridotto per categorie incompatibili
                
                # Penalità per grammature irrealistiche
                gram_penalty = 0
                if equivalent_grams > 500:
                    gram_penalty = min(30, (equivalent_grams - 500) / 20)
                elif equivalent_grams < 20:
                    gram_penalty = min(20, (20 - equivalent_grams) / 2)
                
                # NUOVA PENALITÀ: Distanza dalle grammature ideali (100g)
                # Penalità sempre proporzionale alla distanza dall'ideale
                gram_distance_penalty = 0
                distance_from_ideal = abs(equivalent_grams - 100)
                # Penalità proporzionale: più ci si allontana da 100g, più penalità
                # Formula: distanza / 10 con cap a 20 punti massimi
                gram_distance_penalty = min(20, distance_from_ideal / 10)
                
                # Penalità specifiche per scoraggiare certi alimenti come sostituti
                food_penalty = 0
                if "burro" in candidate_name.lower():
                    food_penalty = 20  # Penalità per il burro
                elif candidate_name.lower() == "pollo_ali":
                    food_penalty = 70  # Penalità per ali di pollo
                elif "gelato" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "gelato_fiordilatte" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "caffe" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                elif "zucchero" in candidate_name.lower():
                    food_penalty = 70  # Penalità per tutti i gelati
                
                # PENALITÀ IMPORTANTE per sostituti aggiuntivi (per garantire priorità ai primi 5)
                additional_substitute_penalty = 25  # Deficit importante di 25 punti
                
                # Score finale
                final_score = macro_similarity + category_bonus - gram_penalty - gram_distance_penalty - food_penalty - additional_substitute_penalty
                
                # Filtri di esclusione logica (mantieni quelli esistenti)
                if should_exclude_combination(food_name, candidate_name, food_category, candidate_category):
                    continue
                
                # Soglia più bassa per permettere più varietà da altre categorie
                if final_score >= 50:  # Ridotto da 60 a 45 per più varietà
                    all_category_candidates.append({
                        'name': candidate_name,
                        'grams': round(equivalent_grams, 1),
                        'similarity_score': round(final_score, 1),
                        'category': candidate_category,
                        'macro_similarity': round(macro_similarity, 1),
                        'category_bonus': category_bonus
                    })
            
            # Ordina e prendi i migliori 5 da tutte le categorie
            all_category_candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
            additional_candidates = all_category_candidates[:5]
            
            # Combina i risultati: prima i 5 della categoria principale, poi i 5 aggiuntivi
            all_substitutes = top_candidates + additional_candidates
            
            if all_substitutes:
                substitutes[food_name] = {}
                for candidate in all_substitutes:
                    substitutes[food_name][candidate['name']] = {
                        'grams': candidate['grams'],
                        'similarity_score': candidate['similarity_score']
                    }
        
        return substitutes
    
    # Sostituisci la funzione
    calculate_logical_substitutes = patched_calculate_logical_substitutes
    
    database = create_logical_substitutes_database() 