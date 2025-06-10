"""
Tool per la generazione automatica di 6 giorni aggiuntivi di dieta.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import streamlit as st

from .meal_optimization_tool import optimize_meal_portions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_meal_name(name):
    """Normalizza un nome di pasto per il confronto"""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def get_canonical_meal_name(meal_name: str) -> str:
    """
    Converte un nome di pasto in forma canonica usando lo stesso mapping del meal_optimization_tool.
    
    Args:
        meal_name: Nome del pasto da normalizzare
        
    Returns:
        Nome canonico del pasto o il nome originale se non trovato
    """
    # Mapping completo con tutte le varianti possibili (copiato dal meal_optimization_tool)
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
    
    # Se ancora non trovato, restituisce il nome normalizzato originale
    if not canonical_meal_name:
        canonical_meal_name = normalized_input
        logger.warning(f"Nome pasto '{meal_name}' non riconosciuto nel mapping, uso '{canonical_meal_name}'")
    
    return canonical_meal_name

def get_user_id() -> str:
    """Estrae l'ID dell'utente dalla sessione Streamlit."""
    if "user_info" not in st.session_state or "id" not in st.session_state.user_info:
        raise ValueError("Nessun utente autenticato. ID utente non disponibile.")
    return st.session_state.user_info["id"]


def load_predefined_days() -> Dict[str, Any]:
    """Carica i 6 giorni di dieta predefiniti dal file JSON."""
    predefined_file = "agent_tools/predefined_weekly_meals.json"
    
    try:
        if os.path.exists(predefined_file):
            with open(predefined_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                predefined_days = data.get("predefined_days", {})
                logger.info(f"Caricati giorni predefiniti da {predefined_file}")
        else:
            logger.error(f"File {predefined_file} non trovato")
            predefined_days = {}
    except Exception as e:
        logger.error(f"Errore nel caricamento di {predefined_file}: {str(e)}")
        predefined_days = {}
    
    return predefined_days

def extract_day1_meal_structure(user_id: str) -> Optional[Dict[str, List[str]]]:
    """Estrae la struttura dei pasti del giorno 1 dal file utente."""
    user_file_path = f"user_data/user_{user_id}.json"
    
    if not os.path.exists(user_file_path):
        logger.error(f"File utente {user_id} non trovato.")
        return None
    
    try:
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # Estrai i pasti registrati dalla struttura del file utente
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        registered_meals = nutritional_info.get("registered_meals", [])
        
        if not registered_meals:
            logger.warning("Nessun pasto registrato trovato nel file utente")
            return None
        
        # Inizializza la struttura del giorno 1
        day1_structure = {
            "colazione": [],
            "spuntino_mattutino": [],
            "pranzo": [],
            "spuntino_pomeridiano": [],
            "cena": [],
            "spuntino_serale": []
        }
        
        # Estrai gli alimenti da ogni pasto registrato
        for meal in registered_meals:
            meal_name = meal.get("nome_pasto", "").lower()
            alimenti = meal.get("alimenti", [])
            
            # Ottieni il nome canonico del pasto usando lo stesso mapping del meal_optimization_tool
            canonical_meal_name = get_canonical_meal_name(meal_name)
            
            # Verifica se il nome canonico corrisponde a uno dei pasti standard
            if canonical_meal_name in day1_structure:
                # Estrai solo gli alimenti con quantità > 0 (pasti effettivamente completati)
                food_list = []
                for alimento in alimenti:
                    quantita = alimento.get("quantita_g", 0)
                    if quantita > 0:
                        nome_alimento = alimento.get("nome_alimento", "")
                        if nome_alimento:
                            food_list.append(nome_alimento)
                
                if food_list:
                    day1_structure[canonical_meal_name] = food_list
                    logger.info(f"Estratto {canonical_meal_name} (da '{meal_name}'): {food_list}")
                else:
                    logger.info(f"Pasto {canonical_meal_name} saltato (quantità 0 o vuoto)")
            else:
                logger.warning(f"Nome pasto '{meal_name}' (canonico: '{canonical_meal_name}') non riconosciuto")
        
        # Verifica che almeno un pasto sia stato estratto
        total_foods = sum(len(foods) for foods in day1_structure.values())
        if total_foods == 0:
            logger.warning("Nessun alimento valido estratto dai pasti registrati")
            return None
        
        logger.info(f"Struttura giorno 1 estratta con successo: {total_foods} alimenti totali")
        return day1_structure
        
    except Exception as e:
        logger.error(f"Errore nel leggere il file utente: {str(e)}")
        return None


def adapt_meals_to_day1_structure(predefined_day: Dict[str, List[str]], 
                                day1_structure: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Adatta i pasti di un giorno predefinito alla struttura del giorno 1, escludendo i pasti vuoti."""
    adapted_day = {}
    
    for meal_name, food_list in day1_structure.items():
        # Includi solo i pasti che hanno alimenti nel giorno 1
        if food_list:  # Se la lista non è vuota
            if meal_name in predefined_day:
                adapted_day[meal_name] = predefined_day[meal_name]
                logger.info(f"Adattato {meal_name} dal giorno predefinito")
            else:
                adapted_day[meal_name] = []
                logger.warning(f"Pasto '{meal_name}' non trovato nel giorno predefinito")
        else:
            logger.info(f"Saltato {meal_name} (vuoto nel giorno 1)")
    
    return adapted_day


def apply_special_rules_for_days_357(days_dict: Dict[str, Dict[str, List[str]]],
                                   day1_structure: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
    """Applica le regole speciali per i giorni 3, 5, 7."""
    special_days = ["giorno_3", "giorno_5", "giorno_7"]
    meals_to_copy = ["colazione", "spuntino_mattutino", "spuntino_pomeridiano"]
    
    for day_key in special_days:
        if day_key in days_dict:
            for meal in meals_to_copy:
                if meal in day1_structure:
                    days_dict[day_key][meal] = day1_structure[meal].copy()
                    logger.info(f"Copiato {meal} dal giorno 1 al {day_key}")
    
    return days_dict


def optimize_day_portions(day_meals: Dict[str, List[str]]) -> Dict[str, Any]:
    """Ottimizza le porzioni per tutti i pasti di un giorno."""
    optimized_day = {}
    
    for meal_name, food_list in day_meals.items():
        if not food_list:
            continue
            
        try:
            optimization_result = optimize_meal_portions(meal_name, food_list)
            
            if optimization_result.get("success", False):
                optimized_day[meal_name] = {
                    "alimenti": optimization_result.get("portions", {}),
                    "target_nutrients": optimization_result.get("target_nutrients", {}),
                    "actual_nutrients": optimization_result.get("actual_nutrients", {}),
                    "macro_single_foods": optimization_result.get("macro_single_foods", {}),
                    "optimization_summary": optimization_result.get("optimization_summary", "")
                }
                logger.info(f"Ottimizzato con successo {meal_name}")
            else:
                error_msg = optimization_result.get("error_message", "Errore sconosciuto")
                logger.error(f"Errore nell'ottimizzazione di {meal_name}: {error_msg}")
                optimized_day[meal_name] = {
                    "error": error_msg,
                    "alimenti_originali": food_list
                }
                
        except Exception as e:
            logger.error(f"Errore nell'ottimizzazione di {meal_name}: {str(e)}")
            optimized_day[meal_name] = {
                "error": str(e),
                "alimenti_originali": food_list
            }
    
    return optimized_day


def generate_6_additional_days(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Genera automaticamente 6 giorni aggiuntivi di dieta."""
    try:
        if user_id is None:
            user_id = get_user_id()
        
        logger.info(f"Avvio generazione 6 giorni aggiuntivi per utente {user_id}")
        
        predefined_days = load_predefined_days()
        logger.info("Caricati giorni predefiniti")
        
        day1_structure = extract_day1_meal_structure(user_id)
        if not day1_structure:
            raise ValueError("Impossibile estrarre la struttura del giorno 1")
        logger.info("Estratta struttura giorno 1")
        
        adapted_days = {}
        for day_key, day_meals in predefined_days.items():
            adapted_days[day_key] = adapt_meals_to_day1_structure(day_meals, day1_structure)
        logger.info("Adattati giorni alla struttura del giorno 1")
        
        adapted_days = apply_special_rules_for_days_357(adapted_days, day1_structure)
        logger.info("Applicate regole speciali per giorni 3, 5, 7")
        
        final_days = {}
        for day_key, day_meals in adapted_days.items():
            logger.info(f"Ottimizzazione {day_key}...")
            final_days[day_key] = optimize_day_portions(day_meals)
        
        logger.info("Generazione completata con successo")
        
        result = {
            "success": True,
            "giorni_generati": final_days,
            "user_id": user_id,
            "giorni_totali": len(final_days),
            "summary": f"Generati con successo {len(final_days)} giorni aggiuntivi di dieta"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Errore nella generazione dei 6 giorni: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "user_id": user_id,
            "giorni_generati": {},
            "summary": f"Errore durante la generazione: {str(e)}"
        } 