from nutridb import NutriDB
import logging
from typing import Dict, Any, Union, List
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
        "check_ultraprocessed_foods": ["foods_with_grams"]
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

    except ValueError as e:
        logger.warning(f"Errore di validazione: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Errore nell'esecuzione di {function_name}: {str(e)}")
        return {"error": f"Errore interno: {str(e)}"}

    return {"error": f"Funzione '{function_name}' non implementata"}