from nutridb import NutriDB
import logging
from typing import Dict, Any, Union, List, Optional
import json
import os

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza il database
try:
    db = NutriDB("Dati_processed")
except Exception as e:
    logger.error(f"Errore nell'inizializzazione del database: {str(e)}")
    raise

def validate_parameters(function_name: str, parameters: Dict[str, Any]) -> None:
    """Valida i parametri per ogni funzione."""
    required_params = {
        "get_macros": ["alimento"],
        "get_LARN_protein": ["sesso", "età"],
        "get_standard_portion": ["categoria", "sottocategoria"],
        "get_weight_from_volume": ["alimento", "tipo_misura"],
        "get_fattore_cottura": ["categoria", "metodo_cottura", "sotto_categoria"],
        "get_LARN_fibre": ["kcal"],
        "get_LARN_lipidi_percentuali": [],
        "get_LARN_vitamine": ["sesso", "età"],
        "compute_Harris_Benedict_Equation": ["sesso", "peso", "altezza", "età", "livello_attività"],
        "get_protein_multiplier": ["tipo_attivita", "is_vegan"],
        "check_ultraprocessed_foods": ["foods_with_grams"],
        "calculate_sport_expenditure": ["sports"]
    }
    
    if function_name not in required_params:
        raise ValueError(f"Funzione '{function_name}' non supportata")
    
    missing = [p for p in required_params[function_name] if p not in parameters]
    if missing:
        raise ValueError(f"Parametri mancanti per {function_name}: {', '.join(missing)}")

def convert_activity_to_laf(activity: str) -> float:
    """Converte il livello di attività testuale nel corrispondente valore LAF."""
    activity_map = {
        "Sedentario": 1.45,
        "Leggermente attivo": 1.60,
        "Attivo": 1.75,
        "Molto attivo": 2.10
    }
    activity = activity.strip()
    if activity not in activity_map:
        closest = min(activity_map.keys(), key=lambda x: abs(len(x) - len(activity)))
        logger.warning(f"Livello di attività '{activity}' non valido, uso '{closest}'")
        return activity_map[closest]
    return activity_map[activity]

def get_protein_multiplier(tipo_attivita: str, is_vegan: bool = False) -> Dict[str, Any]:
    """
    Calcola il moltiplicatore proteico in base al tipo di attività e alla dieta.
    
    Args:
        tipo_attivita: Tipo di attività fisica/sport
        is_vegan: Se True, aggiunge il supplemento per dieta vegana
    
    Returns:
        Dict con moltiplicatore base, range se disponibile, e descrizione
    """
    # Legge i protein requirements dal file JSON
    try:
        protein_requirements_path = os.path.join("Dati_processed", "protein_requirements.json")
        with open(protein_requirements_path, 'r', encoding='utf-8') as file:
            protein_requirements = json.load(file)
    except Exception as e:
        logger.error(f"Errore nella lettura del file protein_requirements.json: {str(e)}")
        raise ValueError(f"Impossibile leggere i requisiti proteici: {str(e)}")
    
    tipo_attivita = tipo_attivita.lower()
    if tipo_attivita not in protein_requirements:
        valid_activities = ", ".join(protein_requirements.keys())
        raise ValueError(f"Tipo attività non valido. Valori accettati: {valid_activities}")
    
    result = protein_requirements[tipo_attivita].copy()
    
    # Aggiunge il supplemento per vegani (usiamo 0.25 come media tra 0.2 e 0.3)
    if is_vegan:
        result["base"] += 0.25
        if "range" in result:
            result["range"] = [x + 0.25 for x in result["range"]]
        result["description"] += " (supplemento vegano incluso)"
    
    return result

def calculate_sport_expenditure(sports: Union[List[Dict[str, Any]], Dict[str, Any], str], hours: Optional[float] = None) -> Dict[str, Any]:
    """
    Calcola il dispendio energetico per uno o più sport in base alle ore di attività.
    
    Args:
        sports: Può essere:
               - Una lista di dizionari, ognuno con sport_name, hours e opzionalmente intensity
               - Un dizionario con sport_name e hours
               - Una stringa con il nome dello sport (richiede anche il parametro hours)
        hours: Ore di attività settimanali (usato solo se sports è una stringa)
        
    Returns:
        Dict contenente:
        - sports_details: Lista dei dettagli per ogni sport
        - total_kcal_per_week: Calorie totali bruciate settimanalmente
        - total_kcal_per_day: Media giornaliera totale di calorie bruciate
    """
    try:
        sport_calories_path = os.path.join("Dati_processed", "sport_calories.json")
        with open(sport_calories_path, 'r', encoding='utf-8') as file:
            sports_data = json.load(file)
        
        # Normalizza l'input in una lista di sport
        sports_list = []
        if isinstance(sports, str):
            if hours is None:
                raise ValueError("Il parametro 'hours' è richiesto quando si specifica un singolo sport come stringa")
            sports_list = [{"sport_name": sports, "hours": hours}]
        elif isinstance(sports, dict):
            sports_list = [sports]
        elif isinstance(sports, list):
            sports_list = sports
        else:
            raise ValueError("Formato sport non valido")
        
        total_results = {
            "sports_details": [],
            "total_kcal_per_week": 0,
            "total_kcal_per_day": 0
        }
        
        # Calcola il dispendio per ogni sport
        for sport in sports_list:
            sport_name = sport["sport_name"].lower().replace(" ", "_")
            sport_hours = float(sport["hours"])
            intensity_multiplier = 1.0
            
            # Applica il moltiplicatore di intensità se specificato
            if "intensity" in sport:
                intensity_map = {"easy": 0.8, "medium": 1.0, "hard": 1.2}
                intensity_multiplier = intensity_map.get(sport["intensity"], 1.0)
            
            # Cerca il nome esatto dello sport
            if sport_name in sports_data["sports"]:
                sport_info = sports_data["sports"][sport_name]
            else:
                # Cerca per sottostringa/somiglianza
                possible_sports = [s for s in sports_data["sports"] if sport_name in s]
                if not possible_sports:
                    raise ValueError(f"Sport '{sport_name}' non trovato nel database")
                
                # Usa il primo risultato trovato
                sport_info = sports_data["sports"][possible_sports[0]]
                sport_name = possible_sports[0]
            
            # Calcola il dispendio energetico per questo sport
            kcal_per_hour = sport_info["kcal_per_hour"] * intensity_multiplier
            kcal_per_session = kcal_per_hour * sport_hours
            kcal_per_week = kcal_per_session
            kcal_per_day = kcal_per_week / 7
            
            sport_result = {
                "sport_name": sport_name,
                "kcal_per_hour": round(kcal_per_hour),
                "hours_per_week": sport_hours,
                "kcal_per_session": round(kcal_per_session),
                "kcal_per_week": round(kcal_per_week),
                "kcal_per_day": round(kcal_per_day),
                "sport_info": {
                    "category": sport_info["category"],
                    "description": sport_info["description"]
                }
            }
            
            total_results["sports_details"].append(sport_result)
            total_results["total_kcal_per_week"] += kcal_per_week
            total_results["total_kcal_per_day"] += kcal_per_day
        
        # Arrotonda i totali
        total_results["total_kcal_per_week"] = round(total_results["total_kcal_per_week"])
        total_results["total_kcal_per_day"] = round(total_results["total_kcal_per_day"])
        
        return total_results
        
    except Exception as e:
        logger.error(f"Errore nel calcolo del dispendio energetico per lo sport: {str(e)}")
        raise ValueError(f"Errore nel calcolo del dispendio sportivo: {str(e)}")

def nutridb_tool(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Tool principale per accedere alle funzioni del database nutrizionale."""
    try:
        # Log della chiamata
        logger.info(f"Chiamata a {function_name} con parametri: {parameters}")
        
        # Valida i parametri
        validate_parameters(function_name, parameters)
        
        # Esegui la funzione richiesta
        if function_name == "get_macros":
            result = db.get_macros(parameters["alimento"], parameters.get("quantità", 100))
            logger.info(f"Risultato get_macros: {result}")
            return {"macronutrienti": result}

        elif function_name == "get_LARN_protein":
            g_kg = db.get_LARN_protein(parameters["sesso"], parameters["età"])
            logger.info(f"Risultato get_LARN_protein: {g_kg}g/kg")
            return {"g_kg": g_kg}

        elif function_name == "get_standard_portion":
            quantità, unità, esempi = db.get_standard_portion(
                parameters["categoria"], parameters["sottocategoria"])
            return {
                "quantità": quantità,
                "unità": unità,
                "esempi": esempi
            }

        elif function_name == "get_weight_from_volume":
            peso = db.get_weight_from_volume(
                parameters["alimento"], parameters["tipo_misura"])
            return {"peso_g": peso}

        elif function_name == "get_fattore_cottura":
            fattore = db.get_fattore_cottura(
                parameters["categoria"],
                parameters["metodo_cottura"],
                parameters["sotto_categoria"])
            return {"fattore": fattore}

        elif function_name == "get_LARN_fibre":
            try:
                kcal = float(parameters["kcal"])
                if kcal <= 0:
                    raise ValueError("kcal deve essere positivo")
                fibra_min, fibra_max = db.get_LARN_fibre(kcal)
                logger.info(f"Risultato get_LARN_fibre: {fibra_min}-{fibra_max}g")
                return {
                    "fibra_min": fibra_min,
                    "fibra_max": fibra_max
                }
            except (ValueError, TypeError) as e:
                logger.error(f"Errore nel calcolo della fibra: {str(e)}")
                return {"error": f"Errore nel calcolo della fibra: {str(e)}"}

        elif function_name == "get_LARN_lipidi_percentuali":
            return {"range_percentuale": db.get_LARN_lipidi_percentuali()}

        elif function_name == "get_LARN_vitamine":
            vitamine = db.get_LARN_vitamine(parameters["sesso"], parameters["età"])
            return {"vitamine": vitamine}

        elif function_name == "compute_Harris_Benedict_Equation":
            try:
                sesso = parameters["sesso"].lower()
                peso = float(parameters["peso"])
                altezza = float(parameters["altezza"])
                età = float(parameters["età"])
                livello_attività = parameters["livello_attività"]

                # Calcolo BMR (Metabolismo Basale)
                if sesso == "m" or sesso == "maschio":
                    bmr = 88.362 + (13.397 * peso) + (4.799 * altezza) - (5.677 * età)
                elif sesso == "f" or sesso == "femmina":
                    bmr = 447.593 + (9.247 * peso) + (3.098 * altezza) - (4.330 * età)
                else:
                    raise ValueError("Sesso non valido. Usare 'm'/'maschio' o 'f'/'femmina'")

                # Applica il fattore di attività fisica
                laf = convert_activity_to_laf(livello_attività)
                fabbisogno_giornaliero = bmr * laf

                logger.info(f"Risultato Harris-Benedict: BMR={bmr:.0f} kcal, Fabbisogno={fabbisogno_giornaliero:.0f} kcal")
                return {
                    "bmr": round(bmr),
                    "fabbisogno_giornaliero": round(fabbisogno_giornaliero),
                    "laf_utilizzato": laf
                }
            except ValueError as e:
                logger.error(f"Errore nel calcolo Harris-Benedict: {str(e)}")
                return {"error": f"Errore nel calcolo: {str(e)}"}
            except Exception as e:
                logger.error(f"Errore inaspettato nel calcolo Harris-Benedict: {str(e)}")
                return {"error": f"Errore inaspettato: {str(e)}"}

        elif function_name == "get_protein_multiplier":
            return get_protein_multiplier(parameters["tipo_attivita"], parameters["is_vegan"])

        elif function_name == "check_ultraprocessed_foods":
            try:
                foods_with_grams = parameters["foods_with_grams"]
                if not isinstance(foods_with_grams, dict):
                    raise ValueError("Il parametro foods_with_grams deve essere un dizionario")
                
                result = db.check_ultraprocessed_foods(foods_with_grams)
                logger.info(f"Risultato check_ultraprocessed_foods: {result}")
                return result
            except Exception as e:
                logger.error(f"Errore nel controllo degli alimenti ultra-processati: {str(e)}")
                return {"error": f"Errore: {str(e)}"}

        elif function_name == "calculate_sport_expenditure":
            try:
                sports = parameters["sports"]
                hours = parameters.get("hours", None)
                
                # Valida in base al tipo di input
                if isinstance(sports, str) and hours is None:
                    raise ValueError("Il parametro 'hours' è richiesto quando si specifica un singolo sport come stringa")
                elif hours is not None and float(hours) <= 0:
                    raise ValueError("Le ore di attività devono essere positive")
                
                # Converti hours a float se presente
                if hours is not None:
                    hours = float(hours)
                
                result = calculate_sport_expenditure(sports, hours)
                logger.info(f"Risultato calculate_sport_expenditure: {result}")
                return result
            except Exception as e:
                logger.error(f"Errore nel calcolo del dispendio sportivo: {str(e)}")
                return {"error": f"Errore: {str(e)}"}

    except ValueError as e:
        logger.warning(f"Errore di validazione: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Errore nell'esecuzione di {function_name}: {str(e)}")
        return {"error": f"Errore interno: {str(e)}"}

    return {"error": f"Funzione '{function_name}' non implementata"}