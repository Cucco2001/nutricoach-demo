"""
Tool per l'ottimizzazione delle porzioni di un pasto.

Questo tool calcola le porzioni ottimali di alimenti specificati
per un pasto in modo da rispettare i target nutrizionali del pasto.
"""

import os
import json
import streamlit as st
from typing import Dict, List, Any, Tuple
import logging
from scipy.optimize import minimize
import numpy as np

from .nutridb import NutriDB

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza il database
try:
    db = NutriDB("Dati_processed")
except Exception as e:
    logger.error(f"Errore nell'inizializzazione del database: {str(e)}")
    raise


def get_user_id() -> str:
    """Estrae l'ID dell'utente dalla sessione Streamlit."""
    if "user_info" not in st.session_state or "id" not in st.session_state.user_info:
        raise ValueError("Nessun utente autenticato. ID utente non disponibile.")
    return st.session_state.user_info["id"]


def load_user_meal_targets(user_id: str, meal_name: str) -> Dict[str, float]:
    """
    Carica i target nutrizionali per un pasto specifico dal file utente.
    
    Args:
        user_id: ID dell'utente
        meal_name: Nome del pasto (es: 'Colazione', 'Pranzo', etc.)
        
    Returns:
        Dict con target di kcal, proteine_g, carboidrati_g, grassi_g
        
    Raises:
        ValueError: Se i dati non sono disponibili
    """
    user_file_path = f"user_data/{user_id}.json"
    
    if not os.path.exists(user_file_path):
        raise ValueError(f"File utente {user_id} non trovato.")
    
    with open(user_file_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    nutritional_info = user_data.get("nutritional_info_extracted", {})
    daily_macros = nutritional_info.get("daily_macros", {})
    distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
    
    # Crea un mapping robusto per i nomi dei pasti
    def normalize_meal_name(name):
        """Normalizza un nome di pasto per il confronto"""
        return name.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Mapping completo con tutte le varianti possibili
    meal_mappings = {
        # COLAZIONE
        "colazione": "colazione",
        "breakfast": "colazione",
        "prima_colazione": "colazione",
        
        # SPUNTINO MATTUTINO
        "spuntino_mattutino": "spuntino_mattutino",
        "spuntino_mattina": "spuntino_mattutino",
        "spuntino_del_mattino": "spuntino_mattutino",
        "spuntino_di_mattina": "spuntino_mattutino",
        "merenda_mattutina": "spuntino_mattutino",
        "merenda_mattina": "spuntino_mattutino",
        "snack_mattutino": "spuntino_mattutino",
        "snack_mattina": "spuntino_mattutino",
        "break_mattutino": "spuntino_mattutino",
        "break_mattina": "spuntino_mattutino",
        
        # PRANZO
        "pranzo": "pranzo",
        "lunch": "pranzo",
        "pasto_principale": "pranzo",
        
        # SPUNTINO POMERIDIANO
        "spuntino_pomeridiano": "spuntino_pomeridiano",
        "spuntino_pomeriggio": "spuntino_pomeridiano",
        "spuntino_del_pomeriggio": "spuntino_pomeridiano",
        "spuntino_di_pomeriggio": "spuntino_pomeridiano",
        "merenda_pomeridiana": "spuntino_pomeridiano",
        "merenda_pomeriggio": "spuntino_pomeridiano",
        "merenda": "spuntino_pomeridiano",
        "snack_pomeridiano": "spuntino_pomeridiano",
        "snack_pomeriggio": "spuntino_pomeridiano",
        "break_pomeridiano": "spuntino_pomeridiano",
        "break_pomeriggio": "spuntino_pomeridiano",
        
        # CENA
        "cena": "cena",
        "dinner": "cena",
        "secondo_pasto": "cena",
        
        # EXTRA (eventuali altri pasti che potrebbero essere nei dati)
        "spuntino_serale": "cena",  # fallback se qualcuno cerca uno spuntino serale
        "merenda_serale": "cena",
    }
    
    # Normalizza il nome del pasto in input
    normalized_input = normalize_meal_name(meal_name)
    
    # Cerca prima nel mapping
    canonical_meal_name = meal_mappings.get(normalized_input)
    
    # Se non trovato nel mapping, prova una ricerca più flessibile
    if not canonical_meal_name:
        # Prova con parole chiave parziali
        input_words = normalized_input.replace("_", " ").split()
        
        for key_words in [
            ["colazione"], 
            ["spuntino", "mattutino", "mattina"],
            ["pranzo"],
            ["spuntino", "pomeridiano", "pomeriggio", "merenda"],
            ["cena"]
        ]:
            # Se almeno una parola chiave è presente nell'input
            if any(word in input_words for word in key_words):
                if "mattut" in normalized_input or "mattina" in normalized_input:
                    canonical_meal_name = "spuntino_mattutino"
                    break
                elif "pomer" in normalized_input or "merenda" in normalized_input:
                    canonical_meal_name = "spuntino_pomeridiano"
                    break
                elif "colazione" in key_words:
                    canonical_meal_name = "colazione"
                    break
                elif "pranzo" in key_words:
                    canonical_meal_name = "pranzo"
                    break
                elif "cena" in key_words:
                    canonical_meal_name = "cena"
                    break
    
    # Cerca il pasto nei dati utente
    meal_data = None
    
    # Prova prima con il nome canonico trovato
    if canonical_meal_name and canonical_meal_name in distribuzione_pasti:
        meal_data = distribuzione_pasti[canonical_meal_name]
    
    # Se non trovato, prova con tutte le chiavi disponibili confrontando i nomi normalizzati
    if not meal_data:
        for available_meal_key in distribuzione_pasti.keys():
            normalized_available = normalize_meal_name(available_meal_key)
            
            # Confronto diretto
            if normalized_available == normalized_input:
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                break
            
            # Confronto parziale (se il nome input è contenuto nella chiave disponibile o viceversa)
            if (normalized_input in normalized_available or 
                normalized_available in normalized_input or
                # Confronto parole chiave
                any(word in normalized_available for word in normalized_input.split("_"))):
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                break
    
    # Se ancora non trovato, restituisci errore con informazioni utili
    if not meal_data:
        available_meals = list(distribuzione_pasti.keys())
        available_meals_formatted = [meal.replace("_", " ").title() for meal in available_meals]
        
        error_msg = (
            f"Pasto '{meal_name}' non trovato. "
            f"Pasti disponibili: {', '.join(available_meals_formatted)}. "
            f"Prova con nomi come: 'Colazione', 'Spuntino Mattutino', 'Pranzo', "
            f"'Spuntino Pomeridiano', 'Cena', 'Merenda', ecc."
        )
        raise ValueError(error_msg)
    
    return {
        "kcal": float(meal_data.get("kcal", 0)),
        "proteine_g": float(meal_data.get("proteine_g", 0)),
        "carboidrati_g": float(meal_data.get("carboidrati_g", 0)),
        "grassi_g": float(meal_data.get("grassi_g", 0))
    }


def get_food_nutrition_per_100g(food_list: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Estrae i dati nutrizionali per 100g di ogni alimento dalla banca alimenti.
    
    Args:
        food_list: Lista dei nomi degli alimenti
        
    Returns:
        Dict con i dati nutrizionali per 100g di ogni alimento
        
    Raises:
        ValueError: Se alcuni alimenti non sono trovati
    """
    foods_nutrition = {}
    foods_not_found = []
    
    for food in food_list:
        # Normalizza il nome dell'alimento usando la stessa logica del database
        normalized_food = food.lower().replace("_", " ")
        
        # Controlla se l'alimento è presente negli alias
        if normalized_food in db.alias:
            # Ottieni la chiave canonica dell'alimento
            canonical_key = db.alias[normalized_food]
            
            try:
                # Ottieni i macronutrienti per 100g usando la chiave canonica
                macros = db.get_macros(food, 100)
                
                # Converte esplicitamente a float per evitare errori di tipo
                foods_nutrition[food] = {
                    "energia_kcal": float(macros.get("energia_kcal", 0)),
                    "proteine_g": float(macros.get("proteine_g", 0)),
                    "carboidrati_g": float(macros.get("carboidrati_g", 0)),
                    "grassi_g": float(macros.get("grassi_g", 0)),
                    "categoria": macros.get("categoria", "alimento_misto")
                }
            except (ValueError, TypeError) as e:
                logger.error(f"Errore conversione dati per {food}: {str(e)}")
                foods_not_found.append(food)
        else:
            foods_not_found.append(food)
    
    if foods_not_found:
        raise ValueError(f"Alimenti non trovati nel database: {', '.join(foods_not_found)}")
    
    return foods_nutrition


def get_portion_constraints():
    """
    Restituisce i vincoli di porzione per categoria di alimento.
    
    Returns:
        Dict con min, max e preferred per ogni categoria
    """
    return {
        # CATEGORIE PRINCIPALI DALLA BANCA ALIMENTI
        "proteine_animali": {"min": 80, "max": 250, "preferred": 120},
        "latticini": {"min": 50, "max": 300, "preferred": 150},
        "cereali": {"min": 30, "max": 150, "preferred": 80},
        "tuberi": {"min": 80, "max": 300, "preferred": 150},  # Simile ai cereali ma porzioni più grandi
        "legumi": {"min": 40, "max": 200, "preferred": 100},
        "verdure": {"min": 50, "max": 400, "preferred": 150},
        "frutta": {"min": 80, "max": 300, "preferred": 150},
        "frutta_secca": {"min": 10, "max": 50, "preferred": 25},
        "grassi_aggiunti": {"min": 5, "max": 30, "preferred": 15},
        "uova": {"min": 50, "max": 200, "preferred": 100},  # ~1-2 uova
        "dolci": {"min": 10, "max": 80, "preferred": 30},   # Porzioni piccole per dolci
        "integratori": {"min": 10, "max": 50, "preferred": 25},  # Porzioni piccole per integratori
        
        # CATEGORIA FALLBACK
        "alimento_misto": {"min": 20, "max": 200, "preferred": 100}
    }


def optimize_portions(target_nutrients: Dict[str, float], 
                     foods_nutrition: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Ottimizza le porzioni degli alimenti per raggiungere i target nutrizionali.
    
    Args:
        target_nutrients: Target di kcal, proteine_g, carboidrati_g, grassi_g
        foods_nutrition: Dati nutrizionali per 100g di ogni alimento
        
    Returns:
        Dict con le porzioni ottimizzate in grammi per ogni alimento
    """
    food_names = list(foods_nutrition.keys())
    n_foods = len(food_names)
    constraints = get_portion_constraints()
    
    # Estrai i bounds per ogni alimento basati sulla categoria
    bounds = []
    preferred_portions = []
    
    for food in food_names:
        categoria = foods_nutrition[food]["categoria"]
        constraint = constraints.get(categoria, constraints["alimento_misto"])
        
        bounds.append((constraint["min"], constraint["max"]))
        preferred_portions.append(constraint["preferred"])
    
    # Funzione obiettivo: minimizza la differenza dai target nutrizionali
    def objective(portions):
        total_kcal = sum(foods_nutrition[food]["energia_kcal"] * portions[i] / 100 
                        for i, food in enumerate(food_names))
        total_proteine = sum(foods_nutrition[food]["proteine_g"] * portions[i] / 100 
                           for i, food in enumerate(food_names))
        total_carboidrati = sum(foods_nutrition[food]["carboidrati_g"] * portions[i] / 100 
                              for i, food in enumerate(food_names))
        total_grassi = sum(foods_nutrition[food]["grassi_g"] * portions[i] / 100 
                         for i, food in enumerate(food_names))
        
        # Calcola gli errori relativi rispetto ai target
        kcal_error = abs(total_kcal - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1)
        proteine_error = abs(total_proteine - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1)
        carboidrati_error = abs(total_carboidrati - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1)
        grassi_error = abs(total_grassi - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
        
        # Errore totale pesato (calorie hanno peso maggiore)
        total_error = (3 * kcal_error + 2 * proteine_error + carboidrati_error + grassi_error)
        
        # Aggiunge una penalità per l'allontanamento dalle porzioni preferite
        portion_penalty = sum(abs(portions[i] - preferred_portions[i]) / preferred_portions[i] 
                            for i in range(n_foods)) * 0.1
        
        return total_error + portion_penalty
    
    # Punto di partenza: porzioni preferite
    initial_guess = np.array(preferred_portions)
    
    # Ottimizzazione
    try:
        result = minimize(
            objective,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimized_portions = result.x
        else:
            logger.warning("Ottimizzazione non convergente, uso porzioni preferite")
            optimized_portions = initial_guess
    except Exception as e:
        logger.error(f"Errore nell'ottimizzazione: {str(e)}")
        optimized_portions = initial_guess
    
    # Costruisci il risultato con conversione esplicita a tipi Python nativi
    portions_result = {}
    for i, food in enumerate(food_names):
        # Converte esplicitamente a float Python nativo per evitare errori di serializzazione JSON
        portions_result[food] = float(round(optimized_portions[i], 1))
    
    return portions_result


def calculate_actual_nutrients(portions: Dict[str, float], 
                             foods_nutrition: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Calcola i valori nutrizionali effettivi dalle porzioni ottimizzate.
    
    Args:
        portions: Porzioni in grammi per ogni alimento
        foods_nutrition: Dati nutrizionali per 100g di ogni alimento
        
    Returns:
        Dict con i valori nutrizionali totali
    """
    total_kcal = sum(foods_nutrition[food]["energia_kcal"] * grams / 100 
                    for food, grams in portions.items())
    total_proteine = sum(foods_nutrition[food]["proteine_g"] * grams / 100 
                        for food, grams in portions.items())
    total_carboidrati = sum(foods_nutrition[food]["carboidrati_g"] * grams / 100 
                           for food, grams in portions.items())
    total_grassi = sum(foods_nutrition[food]["grassi_g"] * grams / 100 
                      for food, grams in portions.items())
    
    # Converte esplicitamente a float Python nativi per evitare errori di serializzazione JSON
    return {
        "kcal": float(round(total_kcal, 1)),
        "proteine_g": float(round(total_proteine, 1)),
        "carboidrati_g": float(round(total_carboidrati, 1)),
        "grassi_g": float(round(total_grassi, 1))
    }


def optimize_meal_portions(meal_name: str, food_list: List[str]) -> Dict[str, Any]:
    """
    Ottimizza automaticamente le porzioni degli alimenti per un pasto specifico.
    
    Verifica automaticamente che tutti gli alimenti siano presenti nel database
    e calcola le quantità in grammi per rispettare i target nutrizionali 
    dell'utente per quel pasto.
    
    Args:
        meal_name: Nome del pasto (es: 'Colazione', 'Pranzo', 'Cena', 'Spuntino')
        food_list: Lista degli alimenti da includere nel pasto
        
    Returns:
        Dict contenente:
        - success: bool se l'ottimizzazione è riuscita
        - portions: dict con alimento -> grammi ottimizzati
        - target_nutrients: target nutrizionali del pasto
        - actual_nutrients: valori nutrizionali effettivi
        - error_message: messaggio di errore se fallisce
        
    Raises:
        ValueError: Se alimenti non sono nel database o dati utente mancanti
    """
    try:
        # 1. Estrai l'ID utente
        user_id = get_user_id()
        
        # 2. Verifica che tutti gli alimenti siano nel database
        all_found, foods_not_found = db.check_foods_in_db(food_list)
        
        if not all_found:
            return {
                "success": False,
                "error_message": f"I seguenti alimenti non sono stati trovati nel database: {', '.join(foods_not_found)}",
                "portions": {},
                "target_nutrients": {},
                "actual_nutrients": {},
                "foods_not_found": foods_not_found
            }
        
        # 3. Carica i target nutrizionali per il pasto
        target_nutrients = load_user_meal_targets(user_id, meal_name)
        
        # 4. Estrai i dati nutrizionali degli alimenti
        foods_nutrition = get_food_nutrition_per_100g(food_list)
        
        # 5. Ottimizza le porzioni
        optimized_portions = optimize_portions(target_nutrients, foods_nutrition)
        
        # 6. Calcola i valori nutrizionali effettivi
        actual_nutrients = calculate_actual_nutrients(optimized_portions, foods_nutrition)
        
        # 7. Calcola gli errori percentuali
        errors = {}
        for nutrient in ["kcal", "proteine_g", "carboidrati_g", "grassi_g"]:
            target = target_nutrients[nutrient]
            actual = actual_nutrients[nutrient]
            if target > 0:
                error_pct = abs(actual - target) / target * 100
                # Converte esplicitamente a float Python nativo per evitare errori di serializzazione JSON
                errors[f"{nutrient}_error_pct"] = float(round(error_pct, 1))
            else:
                errors[f"{nutrient}_error_pct"] = 0.0
        
        return {
            "success": True,
            "portions": optimized_portions,
            "target_nutrients": target_nutrients,
            "actual_nutrients": actual_nutrients,
            "errors": errors,
            "meal_name": meal_name,
            "foods_included": food_list,
            "optimization_summary": f"Ottimizzazione completata per {meal_name} con {len(food_list)} alimenti"
        }
        
    except Exception as e:
        logger.error(f"Errore nell'ottimizzazione del pasto: {str(e)}")
        return {
            "success": False,
            "error_message": f"Errore nell'ottimizzazione: {str(e)}",
            "portions": {},
            "target_nutrients": {},
            "actual_nutrients": {}
        } 