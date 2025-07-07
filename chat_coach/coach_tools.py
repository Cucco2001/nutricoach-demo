"""
Coach tools per la modalità chat coach.

Questo modulo contiene gli strumenti specializzati per il Coach Nutrizionale:
- current_meal_query_tool: Recupera il pasto attuale basato su giorno/ora e configurazione utente
- optimize_meal_portions: Ottimizza le porzioni di un pasto richiamando il tool esistente
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import del tool esistente
from agent_tools.meal_optimization_tool import optimize_meal_portions as meal_optimization_optimize_meal_portions
from agent_tools.nutridb_tool import get_user_id


def extract_substitutes_from_text(text_content: str) -> List[str]:
    """
    Estrae i sostituti dal testo esistente nei dati utente.
    
    Args:
        text_content: Contenuto testuale che potrebbe contenere sostituti
        
    Returns:
        Lista di sostituti trovati
    """
    substitutes = []
    
    try:
        # Pattern per trovare sostituti nel testo (es: "Sostituti: 300g di yogurt magro, 350g di latte scremato")
        substitute_pattern = r'Sostituti:\s*([^\n]+)'
        matches = re.findall(substitute_pattern, text_content, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            # Dividi per virgola e pulisci
            items = [item.strip() for item in match.split(',')]
            substitutes.extend(items)
        
    except Exception as e:
        logger.warning(f"Errore nell'estrazione sostituti dal testo: {str(e)}")
    
    return substitutes


def get_user_meal_configuration(user_id: str) -> Dict[str, Any]:
    """
    Recupera la configurazione dei pasti dell'utente.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        Dict con configurazione pasti (num_meals, meal_times, etc.)
    """
    try:
        # Fix: Handle user_id that may already contain 'user_' prefix
        if user_id.startswith("user_"):
            user_file_path = f"user_data/{user_id}.json"
        else:
            user_file_path = f"user_data/user_{user_id}.json"
        
        if not os.path.exists(user_file_path):
            logger.error(f"File utente {user_id} non trovato")
            return {}
        
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # Recupera la configurazione pasti dall'anamnesi iniziale
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        daily_macros = nutritional_info.get("daily_macros", {})
        distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
        
        # Cerca i meal_times nei dati utente (potrebbero essere in chat_history)
        meal_times = {}
        chat_history = user_data.get("chat_history", [])
        
        # Analizza la chat history per trovare gli orari dei pasti
        for message in chat_history:
            if message.get("role") == "assistant":
                content = message.get("content", "")
                if "orari:" in content.lower() or "ore:" in content.lower():
                    # Cerca pattern di orari (es: "Colazione 07:30")
                    lines = content.split('\n')
                    for line in lines:
                        if ":" in line and any(pasto in line.lower() for pasto in ["colazione", "pranzo", "spuntino", "cena"]):
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if ":" in part and len(part) == 5:  # Format HH:MM
                                    meal_name = parts[i-1].lower().strip()
                                    meal_times[meal_name] = part
        
        # Determina il numero di pasti basandosi sui pasti disponibili
        meal_names = list(distribuzione_pasti.keys())
        num_meals = len(meal_names)
        
        # Mappa standard dei pasti in base al numero
        standard_meal_labels = [
            "colazione",
            "spuntino_mattutino", 
            "pranzo",
            "spuntino_pomeridiano",
            "cena"
        ]
        
        return {
            "num_meals": num_meals,
            "meal_names": meal_names,
            "meal_times": meal_times,
            "standard_meal_labels": standard_meal_labels[:num_meals],
            "distribuzione_pasti": distribuzione_pasti
        }
        
    except Exception as e:
        logger.error(f"Errore recupero configurazione pasti: {str(e)}")
        return {}


def get_user_weekly_diet(user_id: str) -> Dict[str, Any]:
    """
    Recupera la dieta settimanale dell'utente.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        Dict con la dieta settimanale strutturata
    """
    try:
        # Fix: Handle user_id that may already contain 'user_' prefix
        if user_id.startswith("user_"):
            user_file_path = f"user_data/{user_id}.json"
        else:
            user_file_path = f"user_data/user_{user_id}.json"
        
        if not os.path.exists(user_file_path):
            logger.error(f"File utente {user_id} non trovato")
            return {}
        
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        
        # Recupera i dati della dieta settimanale
        weekly_diet = {}
        
        # Giorno 1 (formato array)
        day_1_data = nutritional_info.get("weekly_diet_day_1", [])
        if day_1_data:
            weekly_diet["lunedì"] = day_1_data
        
        # Giorni 2-7 (formato object)
        days_2_7_data = nutritional_info.get("weekly_diet_days_2_7", {})
        if days_2_7_data:
            # Mappa i giorni dalla struttura dati
            day_mapping = {
                "giorno_2": "martedì",
                "giorno_3": "mercoledì", 
                "giorno_4": "giovedì",
                "giorno_5": "venerdì",
                "giorno_6": "sabato",
                "giorno_7": "domenica"
            }
            
            for day_key, day_name in day_mapping.items():
                if day_key in days_2_7_data:
                    weekly_diet[day_name] = days_2_7_data[day_key]
        
        return weekly_diet
        
    except Exception as e:
        logger.error(f"Errore recupero dieta settimanale: {str(e)}")
        return {}


def determine_current_meal(user_id: str, current_time: str = None, current_day: str = None) -> Dict[str, Any]:
    """
    Determina il pasto corrente basandosi su orario, giorno e configurazione utente.
    
    Args:
        user_id: ID dell'utente
        current_time: Ora corrente (formato HH:MM), se None usa ora attuale
        current_day: Giorno corrente (italiano), se None usa giorno attuale
        
    Returns:
        Dict con informazioni sul pasto determinato
    """
    try:
        # Usa ora e giorno correnti se non specificati
        if current_time is None or current_day is None:
            now = datetime.now()
            if current_time is None:
                current_time = now.strftime("%H:%M")
            if current_day is None:
                day_map = {
                    "Monday": "lunedì",
                    "Tuesday": "martedì", 
                    "Wednesday": "mercoledì",
                    "Thursday": "giovedì",
                    "Friday": "venerdì",
                    "Saturday": "sabato",
                    "Sunday": "domenica"
                }
                current_day = day_map.get(now.strftime("%A"), "lunedì")
        
        # Recupera configurazione pasti
        meal_config = get_user_meal_configuration(user_id)
        if not meal_config:
            return {"error": "Configurazione pasti non disponibile"}
        
        # Converti l'ora corrente in minuti dal midnight per il confronto
        try:
            current_hour, current_minute = map(int, current_time.split(':'))
            current_minutes = current_hour * 60 + current_minute
        except ValueError:
            return {"error": "Formato ora non valido"}
        
        # Se ci sono orari specifici, usali
        meal_times = meal_config.get("meal_times", {})
        if meal_times:
            # Trova il pasto più vicino basato sull'orario
            closest_meal = None
            min_diff = float('inf')
            
            for meal_name, meal_time in meal_times.items():
                try:
                    meal_hour, meal_minute = map(int, meal_time.split(':'))
                    meal_minutes = meal_hour * 60 + meal_minute
                    
                    # Calcola la differenza (considerando anche il giorno dopo)
                    diff = abs(current_minutes - meal_minutes)
                    if diff > 12 * 60:  # Se più di 12 ore, considera il giorno dopo/prima
                        diff = 24 * 60 - diff
                    
                    if diff < min_diff:
                        min_diff = diff
                        closest_meal = meal_name
                except ValueError:
                    continue
            
            if closest_meal:
                return {
                    "meal_type": closest_meal,
                    "current_time": current_time,
                    "current_day": current_day,
                    "method": "orari_specifici"
                }
        
        # Usa la logica standard basata sull'ora per il numero di pasti
        num_meals = meal_config.get("num_meals", 4)
        standard_labels = meal_config.get("standard_meal_labels", [])
        
        # Logica basata sull'ora per determinare il pasto
        if num_meals == 1:
            return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "1_pasto"}
        elif num_meals == 2:
            if current_minutes < 15 * 60:  # Prima delle 15:00
                return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "2_pasti"}
            else:
                return {"meal_type": "pranzo", "current_time": current_time, "current_day": current_day, "method": "2_pasti"}
        elif num_meals == 3:
            if current_minutes < 11 * 60:  # Prima delle 11:00
                return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "3_pasti"}
            elif current_minutes < 17 * 60:  # Prima delle 17:00
                return {"meal_type": "pranzo", "current_time": current_time, "current_day": current_day, "method": "3_pasti"}
            else:
                return {"meal_type": "cena", "current_time": current_time, "current_day": current_day, "method": "3_pasti"}
        elif num_meals == 4:
            if current_minutes < 10 * 60:  # Prima delle 10:00
                return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "4_pasti"}
            elif current_minutes < 14 * 60:  # Prima delle 14:00
                return {"meal_type": "pranzo", "current_time": current_time, "current_day": current_day, "method": "4_pasti"}
            elif current_minutes < 18 * 60:  # Prima delle 18:00
                return {"meal_type": "spuntino_pomeridiano", "current_time": current_time, "current_day": current_day, "method": "4_pasti"}
            else:
                return {"meal_type": "cena", "current_time": current_time, "current_day": current_day, "method": "4_pasti"}
        elif num_meals == 5:
            if current_minutes < 9 * 60:  # Prima delle 9:00
                return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "5_pasti"}
            elif current_minutes < 11 * 60:  # Prima delle 11:00
                return {"meal_type": "spuntino_mattutino", "current_time": current_time, "current_day": current_day, "method": "5_pasti"}
            elif current_minutes < 15 * 60:  # Prima delle 15:00
                return {"meal_type": "pranzo", "current_time": current_time, "current_day": current_day, "method": "5_pasti"}
            elif current_minutes < 18 * 60:  # Prima delle 18:00
                return {"meal_type": "spuntino_pomeridiano", "current_time": current_time, "current_day": current_day, "method": "5_pasti"}
            else:
                return {"meal_type": "cena", "current_time": current_time, "current_day": current_day, "method": "5_pasti"}
        
        # Fallback
        return {"meal_type": "colazione", "current_time": current_time, "current_day": current_day, "method": "fallback"}
        
    except Exception as e:
        logger.error(f"Errore determinazione pasto corrente: {str(e)}")
        return {"error": f"Errore determinazione pasto: {str(e)}"}


def current_meal_query_tool(day: str = None, meal_type: str = None) -> Dict[str, Any]:
    """
    Recupera il pasto previsto per un giorno e tipo di pasto specifici.
    
    Args:
        day: Giorno della settimana (opzionale, default: oggi)
        meal_type: Tipo di pasto (opzionale, default: auto-determinato dall'ora)
        
    Returns:
        Dict con informazioni sul pasto inclusi sostituti e misure casalinghe
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return {"error": "Utente non identificato"}
        
        # Se meal_type non è specificato, determinalo automaticamente
        if meal_type is None:
            meal_info = determine_current_meal(user_id, current_day=day)
            if "error" in meal_info:
                return meal_info
            meal_type = meal_info["meal_type"]
            if day is None:
                day = meal_info["current_day"]
        
        # Se day non è specificato, usa il giorno corrente
        if day is None:
            now = datetime.now()
            day_map = {
                "Monday": "lunedì",
                "Tuesday": "martedì", 
                "Wednesday": "mercoledì",
                "Thursday": "giovedì",
                "Friday": "venerdì",
                "Saturday": "sabato",
                "Sunday": "domenica"
            }
            day = day_map.get(now.strftime("%A"), "lunedì")
        
        # Normalizza il giorno
        day = day.lower().strip()
        
        # Recupera la dieta settimanale
        weekly_diet = get_user_weekly_diet(user_id)
        if not weekly_diet:
            return {"error": "Dieta settimanale non disponibile"}
        
        # Trova il giorno nella dieta
        day_data = weekly_diet.get(day)
        if not day_data:
            return {"error": f"Dati non disponibili per {day}"}
        
        # Normalizza il tipo di pasto per la ricerca
        meal_type_normalized = meal_type.lower().strip()
        
        # Mapping tipi di pasto
        meal_type_mapping = {
            "colazione": ["colazione", "breakfast"],
            "spuntino_mattutino": ["spuntino_mattutino", "spuntino_mattina", "spuntino mattutino"],
            "pranzo": ["pranzo", "lunch"],
            "spuntino_pomeridiano": ["spuntino_pomeridiano", "spuntino", "spuntino_pomeriggio", "spuntino pomeridiano"],
            "cena": ["cena", "dinner"]
        }
        
        # Trova il tipo di pasto corretto
        canonical_meal_type = None
        for canonical, variants in meal_type_mapping.items():
            if any(variant in meal_type_normalized for variant in variants):
                canonical_meal_type = canonical
                break
        
        if not canonical_meal_type:
            canonical_meal_type = meal_type_normalized
        
        # Cerca il pasto nei dati del giorno
        meal_found = None
        meal_text_content = ""
        
        # I dati potrebbero essere in formato diverso (array o object)
        if isinstance(day_data, list):
            # Formato array - cerca nelle descrizioni
            for item in day_data:
                if isinstance(item, dict):
                    nome_pasto = item.get("nome_pasto", "").lower()
                    if any(variant in nome_pasto for variant in meal_type_mapping.get(canonical_meal_type, [canonical_meal_type])):
                        meal_found = item
                        meal_text_content = str(item)
                        break
        elif isinstance(day_data, dict):
            # Formato object - cerca nelle chiavi
            for key, value in day_data.items():
                key_lower = key.lower()
                if any(variant in key_lower for variant in meal_type_mapping.get(canonical_meal_type, [canonical_meal_type])):
                    meal_found = value
                    meal_text_content = str(value)
                    break
        
        if not meal_found:
            return {
                "error": f"Pasto '{meal_type}' non trovato per {day}",
                "available_meals": list(day_data.keys()) if isinstance(day_data, dict) else "Formato dati non standard"
            }
        
        # Estrai misure casalinghe e sostituti dai dati strutturati
        serving_sizes = {}
        substitutes = []
        
        # Se meal_found ha alimenti, estrai le misure casalinghe
        if isinstance(meal_found, dict) and "alimenti" in meal_found:
            for alimento in meal_found["alimenti"]:
                if isinstance(alimento, dict):
                    nome = alimento.get("nome_alimento", "")
                    quantita = alimento.get("quantita_g", 0)
                    misura = alimento.get("misura_casalinga", "")
                    
                    if nome and quantita and misura:
                        serving_sizes[nome] = f"{quantita}g → {misura}"
        
        # Estrai sostituti dal testo esistente se presente
        substitutes = extract_substitutes_from_text(meal_text_content)
        
        return {
            "success": True,
            "day": day,
            "meal_type": meal_type,
            "meal_data": meal_found,
            "canonical_meal_type": canonical_meal_type,
            "serving_sizes": serving_sizes,
            "substitutes": substitutes,
            "detailed_info": {
                "day": day.title(),
                "meal": meal_type.replace("_", " ").title(),
                "auto_determined": meal_type is None
            }
        }
        
    except Exception as e:
        logger.error(f"Errore in current_meal_query_tool: {str(e)}")
        return {"error": f"Errore nella query del pasto: {str(e)}"}


def optimize_meal_portions(food_list: List[str], meal_name: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Ottimizza le porzioni di un pasto richiamando il tool di ottimizzazione esistente.
    
    Args:
        food_list: Lista degli alimenti da ottimizzare
        meal_name: Nome del pasto (opzionale, auto-determinato se None)
        user_id: ID dell'utente (opzionale, usa get_user_id() se None)
        
    Returns:
        Dict con risultato dell'ottimizzazione
    """
    try:
        # Recupera user_id se non fornito
        if user_id is None:
            user_id = get_user_id()
            if not user_id:
                return {"error": "Utente non identificato"}
        
        # Se meal_name non è specificato, determinalo automaticamente
        auto_determined = meal_name is None
        if meal_name is None:
            meal_info = determine_current_meal(user_id)
            if "error" in meal_info:
                return meal_info
            meal_name = meal_info["meal_type"]
            
            # Converti da formato interno a formato richiesto dal tool
            meal_name_mapping = {
                "colazione": "Colazione",
                "spuntino_mattutino": "Spuntino Mattutino",
                "pranzo": "Pranzo", 
                "spuntino_pomeridiano": "Spuntino Pomeridiano",
                "cena": "Cena"
            }
            meal_name = meal_name_mapping.get(meal_name, meal_name.title())
        
        # Valida la lista degli alimenti
        if not food_list or not isinstance(food_list, list):
            return {"error": "Lista alimenti non valida"}
        
        # Richiama il tool di ottimizzazione esistente
        result = meal_optimization_optimize_meal_portions(
            meal_name=meal_name,
            food_list=food_list,
            user_id=user_id
        )
        
        # Aggiungi informazioni aggiuntive al risultato
        if result.get("success"):
            result["meal_name_determined"] = meal_name
            result["auto_determined"] = auto_determined
            
            # Aggiungi informazioni per il coach
            result["coach_info"] = {
                "meal_type": meal_name,
                "total_foods": len(food_list),
                "optimization_status": "completed",
                "auto_determined": auto_determined
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Errore in optimize_meal_portions: {str(e)}")
        return {"error": f"Errore nell'ottimizzazione: {str(e)}"}


# Lista dei tool disponibili per il coach
COACH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "current_meal_query_tool",
            "description": "Recupera il pasto previsto per un giorno e tipo di pasto. Se non specificati, determina automaticamente basandosi su ora corrente e configurazione pasti utente. Include sostituti e misure casalinghe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "Giorno della settimana (lunedì, martedì, etc.). Opzionale, default: oggi",
                        "enum": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
                    },
                    "meal_type": {
                        "type": "string", 
                        "description": "Tipo di pasto (colazione, pranzo, cena, spuntino, etc.). Opzionale, default: auto-determinato dall'ora corrente",
                        "enum": ["colazione", "spuntino_mattutino", "pranzo", "spuntino_pomeridiano", "cena", "spuntino"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_meal_portions",
            "description": "Ottimizza le porzioni di un pasto in base ai target nutrizionali dell'utente. Calcola automaticamente le quantità ideali per ogni alimento e fornisce sostituti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista degli alimenti da ottimizzare (es: ['pasta', 'pomodoro', 'olio'])"
                    },
                    "meal_name": {
                        "type": "string",
                        "description": "Nome del pasto (Colazione, Pranzo, Cena, etc.). Opzionale, auto-determinato se non specificato",
                        "enum": ["Colazione", "Spuntino Mattutino", "Pranzo", "Spuntino Pomeridiano", "Cena"]
                    }
                },
                "required": ["food_list"]
            }
        }
    }
]


 