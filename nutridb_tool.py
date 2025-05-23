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
        "get_protein_multiplier": ["sports"],
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

def get_protein_multiplier(sports: Union[List[Dict[str, str]], Dict[str, str]], is_vegan: bool = False) -> Dict[str, Any]:
    """
    Calcola il moltiplicatore proteico in base agli sport praticati e alla dieta.
    
    Args:
        sports: Può essere:
               - Una lista di dizionari, ognuno con sport_type e intensity (easy/medium/hard)
               - Un singolo dizionario con sport_type e intensity
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
    
    # Normalizza l'input in una lista di sport
    sports_list = []
    if isinstance(sports, dict):
        sports_list = [sports]
    elif isinstance(sports, list):
        sports_list = sports
    else:
        raise ValueError("Formato sport non valido")
    
    # Mappa per convertire i tipi di sport dal form ai tipi nel JSON
    sport_type_map = {
        "Fitness - Allenamento medio (principianti e livello intermedio)": "fitness",
        "Fitness - Bodybuilding Massa (solo esperti >2 anni di allenamento)": "bodybuilding_massa",
        "Fitness - Bodybuilding Definizione (solo esperti >2 anni di allenamento)": "bodybuilding_definizione",
        "Sport di forza (es: powerlifting, sollevamento pesi, strongman)": "forza",
        "Sport di resistenza (es: corsa, ciclismo, nuoto, triathlon)": "endurance",
        "Sport aciclici (es: tennis, pallavolo, arti marziali, calcio)": "aciclico",
        "Sedentario": "sedentario"
    }
    
    # Trova lo sport che richiede più proteine
    max_protein_req = None
    max_sport_type = None
    max_intensity = None
    other_sports_intense = False
    
    for sport in sports_list:
        sport_type = sport["sport_type"]
        intensity = sport.get("intensity", "medium")
        
        # Converti il tipo di sport
        if sport_type in sport_type_map:
            sport_type = sport_type_map[sport_type]
        else:
            raise ValueError(f"Tipo sport non valido: {sport_type}")
        
        # Ottieni i requisiti proteici per questo sport
        if sport_type not in protein_requirements:
            continue
            
        protein_req = protein_requirements[sport_type]
        
        # Se questo sport ha requisiti proteici più alti, diventa il principale
        if max_protein_req is None or protein_req["base"] > max_protein_req["base"]:
            max_protein_req = protein_req
            max_sport_type = sport_type
            max_intensity = intensity
        # Se questo sport ha intensità alta, lo segnaliamo
        elif intensity == "hard":
            other_sports_intense = True
    
    if max_protein_req is None:
        # Se nessuno sport valido è stato trovato, usa i valori per sedentari
        result = protein_requirements["sedentario"].copy()
    else:
        result = max_protein_req.copy()
        
        # Gestisci il range in base all'intensità
        if "range" in result:
            base_value = result["base"]
            range_values = result["range"]
            
            if max_intensity == "hard" or other_sports_intense:
                # Se lo sport principale è intenso o ci sono altri sport intensi, usa il valore più alto
                result["base"] = range_values[1]
            elif max_intensity == "easy":
                # Se l'intensità è bassa, usa il valore più basso
                result["base"] = range_values[0]
            else:
                # Per intensità media, usa il valore base
                result["base"] = base_value
                
            result["description"] += f" (intensità {max_intensity})"
    
    # Aggiunge il supplemento per vegani
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

def get_macros(alimento: str, quantità: float = 100) -> Dict[str, Any]:
    """
    Ottiene i valori nutrizionali per un dato alimento.
    
    Args:
        alimento: Nome dell'alimento
        quantità: Quantità in grammi (default 100g)
        
    Returns:
        Dict con i macronutrienti dell'alimento
    """
    try:
        result = db.get_macros(alimento, quantità)
        logger.info(f"Risultato get_macros: {result}")
        return {"macronutrienti": result}
    except Exception as e:
        logger.error(f"Errore in get_macros: {str(e)}")
        return {"error": str(e)}

def get_LARN_protein(sesso: str, età: int) -> Dict[str, Any]:
    """
    Ottiene i valori di riferimento per l'assunzione proteica.
    
    Args:
        sesso: Sesso della persona ("maschio" o "femmina")
        età: Età della persona in anni
        
    Returns:
        Dict con il fabbisogno proteico in g/kg
    """
    try:
        g_kg = db.get_LARN_protein(sesso, età)
        logger.info(f"Risultato get_LARN_protein: {g_kg}g/kg")
        return {"g_kg": g_kg}
    except Exception as e:
        logger.error(f"Errore in get_LARN_protein: {str(e)}")
        return {"error": str(e)}

def get_standard_portion(categoria: str, sottocategoria: str) -> Dict[str, Any]:
    """
    Ottiene le porzioni standard per una data categoria di alimenti.
    
    Args:
        categoria: Categoria dell'alimento
        sottocategoria: Sottocategoria dell'alimento
        
    Returns:
        Dict con quantità, unità di misura ed esempi
    """
    try:
        quantità, unità, esempi = db.get_standard_portion(categoria, sottocategoria)
        return {
            "quantità": quantità,
            "unità": unità,
            "esempi": esempi
        }
    except Exception as e:
        logger.error(f"Errore in get_standard_portion: {str(e)}")
        return {"error": str(e)}

def get_weight_from_volume(alimento: str, tipo_misura: str) -> Dict[str, Any]:
    """
    Converte una misura di volume in peso per un dato alimento.
    
    Args:
        alimento: Nome dell'alimento
        tipo_misura: Tipo di misura (es. "cucchiaio", "tazza")
        
    Returns:
        Dict con il peso equivalente in grammi
    """
    try:
        peso = db.get_weight_from_volume(alimento, tipo_misura)
        return {"peso_g": peso}
    except Exception as e:
        logger.error(f"Errore in get_weight_from_volume: {str(e)}")
        return {"error": str(e)}

def get_fattore_cottura(categoria: str, metodo_cottura: str, sotto_categoria: str) -> Dict[str, Any]:
    """
    Ottiene il fattore di conversione per la cottura di un alimento.
    
    Args:
        categoria: Categoria dell'alimento
        metodo_cottura: Metodo di cottura
        sotto_categoria: Sottocategoria dell'alimento
        
    Returns:
        Dict con il fattore di conversione
    """
    try:
        fattore = db.get_fattore_cottura(categoria, metodo_cottura, sotto_categoria)
        return {"fattore": fattore}
    except Exception as e:
        logger.error(f"Errore in get_fattore_cottura: {str(e)}")
        return {"error": str(e)}

def get_LARN_fibre(kcal: float) -> Dict[str, Any]:
    """
    Ottiene il fabbisogno di fibre in base alle calorie totali.
    
    Args:
        kcal: Fabbisogno calorico giornaliero
        
    Returns:
        Dict con i valori minimo e massimo di fibre raccomandate
    """
    try:
        if kcal <= 0:
            raise ValueError("kcal deve essere positivo")
        fibra_min, fibra_max = db.get_LARN_fibre(kcal)
        logger.info(f"Risultato get_LARN_fibre: {fibra_min}-{fibra_max}g")
        return {
            "fibra_min": fibra_min,
            "fibra_max": fibra_max
        }
    except Exception as e:
        logger.error(f"Errore in get_LARN_fibre: {str(e)}")
        return {"error": str(e)}

def get_LARN_lipidi_percentuali() -> Dict[str, Any]:
    """
    Ottiene il range percentuale raccomandato per i lipidi.
    
    Returns:
        Dict con il range percentuale
    """
    try:
        return {"range_percentuale": db.get_LARN_lipidi_percentuali()}
    except Exception as e:
        logger.error(f"Errore in get_LARN_lipidi_percentuali: {str(e)}")
        return {"error": str(e)}

def get_LARN_vitamine(sesso: str, età: int) -> Dict[str, Any]:
    """
    Ottiene i valori di riferimento per le vitamine.
    
    Args:
        sesso: Sesso della persona ("maschio" o "femmina")
        età: Età della persona in anni
        
    Returns:
        Dict con i valori raccomandati per le vitamine
    """
    try:
        vitamine = db.get_LARN_vitamine(sesso, età)
        return {"vitamine": vitamine}
    except Exception as e:
        logger.error(f"Errore in get_LARN_vitamine: {str(e)}")
        return {"error": str(e)}

def compute_Harris_Benedict_Equation(sesso: str, peso: float, altezza: float, età: float, livello_attività: str) -> Dict[str, Any]:
    """
    Calcola il metabolismo basale e il fabbisogno energetico totale.
    
    Args:
        sesso: Sesso della persona ("maschio" o "femmina")
        peso: Peso in kg
        altezza: Altezza in cm
        età: Età in anni
        livello_attività: Livello di attività fisica
        
    Returns:
        Dict con metabolismo basale e fabbisogno giornaliero
    """
    try:
        sesso = sesso.lower()
        
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
    except Exception as e:
        logger.error(f"Errore in compute_Harris_Benedict_Equation: {str(e)}")
        return {"error": str(e)}

def check_ultraprocessed_foods(foods_with_grams: Dict[str, float]) -> Dict[str, Any]:
    """
    Controlla quali alimenti sono ultra-processati e fornisce raccomandazioni.
    
    Args:
        foods_with_grams: Dizionario con alimenti e relative grammature
    
    Returns:
        Dict con i risultati dell'analisi
    """
    try:
        if not isinstance(foods_with_grams, dict):
            raise ValueError("Il parametro foods_with_grams deve essere un dizionario")
        
        result = db.check_ultraprocessed_foods(foods_with_grams)
        logger.info(f"Risultato check_ultraprocessed_foods: {result}")
        return result
    except Exception as e:
        logger.error(f"Errore nel controllo degli alimenti ultra-processati: {str(e)}")
        return {"error": f"Errore: {str(e)}"}