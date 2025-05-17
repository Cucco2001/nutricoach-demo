from nutridb import NutriDB
import logging
from typing import Dict, Any, Union, List

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
        "get_LARN_protein": ["sesso", "età", "peso"],
        "get_LARN_energy": ["sesso", "età", "altezza", "LAF"],
        "get_standard_portion": ["categoria", "sottocategoria"],
        "get_weight_from_volume": ["alimento", "tipo_misura"],
        "get_fattore_cottura": ["categoria", "metodo_cottura", "sotto_categoria"],
        "get_LARN_fibre": ["kcal"],
        "get_LARN_carboidrati_percentuali": [],
        "get_LARN_lipidi_percentuali": [],
        "get_LARN_vitamine": ["sesso", "età"]
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

def nutridb_tool(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Tool principale per accedere alle funzioni del database nutrizionale."""
    try:
        # Log della chiamata
        logger.info(f"Chiamata a {function_name} con parametri: {parameters}")
        
        # Valida i parametri
        validate_parameters(function_name, parameters)
        
        # Validazione aggiuntiva per valori specifici
        if function_name == "get_LARN_energy":
            # Se LAF è una stringa (livello di attività), convertila
            if isinstance(parameters["LAF"], str):
                parameters["LAF"] = convert_activity_to_laf(parameters["LAF"])
            else:
                # Altrimenti usa la validazione numerica esistente
                valid_lafs = [1.45, 1.60, 1.75, 2.10]
                laf = float(parameters["LAF"])
                if laf not in valid_lafs:
                    closest_laf = min(valid_lafs, key=lambda x: abs(x - laf))
                    logger.warning(f"LAF {laf} non valido, uso il più vicino: {closest_laf}")
                    parameters["LAF"] = closest_laf
        
        # Esegui la funzione richiesta
        if function_name == "get_macros":
            result = db.get_macros(parameters["alimento"], parameters.get("quantità", 100))
            logger.info(f"Risultato get_macros: {result}")
            return {"macronutrienti": result}

        elif function_name == "get_LARN_protein":
            g_proteine = db.get_LARN_protein(
                parameters["sesso"], parameters["età"], parameters["peso"])
            logger.info(f"Risultato get_LARN_protein: {g_proteine}g")
            return {"g_proteine": g_proteine}

        elif function_name == "get_LARN_energy":
            kcal = db.get_LARN_energy(
                parameters["sesso"], parameters["età"], 
                parameters["altezza"], parameters["LAF"])
            logger.info(f"Risultato get_LARN_energy: {kcal}kcal")
            return {"kcal": kcal}

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

        elif function_name == "get_LARN_carboidrati_percentuali":
            return {"range_percentuale": db.get_LARN_carboidrati_percentuali()}

        elif function_name == "get_LARN_lipidi_percentuali":
            return {"range_percentuale": db.get_LARN_lipidi_percentuali()}

        elif function_name == "get_LARN_vitamine":
            vitamine = db.get_LARN_vitamine(parameters["sesso"], parameters["età"])
            return {"vitamine": vitamine}

    except ValueError as e:
        logger.warning(f"Errore di validazione: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Errore nell'esecuzione di {function_name}: {str(e)}")
        return {"error": f"Errore interno: {str(e)}"}

    return {"error": f"Funzione '{function_name}' non implementata"}