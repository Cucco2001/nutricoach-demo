from .nutridb import NutriDB
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
        "compute_Harris_Benedict_Equation": [],
        "get_protein_multiplier": ["sports"],
        "check_ultraprocessed_foods": [],
        "calculate_sport_expenditure": ["sports"],
        "calculate_weight_goal_calories": ["kg_change", "time_months", "goal_type"],
        "analyze_bmi_and_goals": ["peso", "altezza", "sesso", "età", "obiettivo"],
        "check_vitamins": ["foods_with_grams", "sesso", "età"],
        "get_food_substitutes": ["food_name", "grams"]
    }
    
    if function_name not in required_params:
        raise ValueError(f"Funzione '{function_name}' non supportata")
    
    missing = [p for p in required_params[function_name] if p not in parameters]
    if missing:
        raise ValueError(f"Parametri mancanti per {function_name}: {', '.join(missing)}")

def convert_activity_to_laf(activity: str) -> float:
    """Converte il livello di attività testuale nel corrispondente valore LAF."""
    activity_map = {
        "Sedentario": 1.30,
        "Leggermente attivo": 1.45,
        "Attivo": 1.60,
        "Molto attivo": 1.75
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
        "Fitness - Bodybuilding Massa": "bodybuilding_massa",
        "Fitness - Bodybuilding Definizione": "bodybuilding_definizione",
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
            original_sport_name = sport["sport_name"]
            print(f"[DEBUG] Ricevuto sport_name: '{original_sport_name}' (tipo: {type(original_sport_name)})")
            sport_hours = float(sport["hours"])
            intensity_multiplier = 1.0
            
            # Applica il moltiplicatore di intensità se specificato
            if "intensity" in sport:
                intensity_map = {"easy": 0.8, "medium": 1.0, "hard": 1.2}
                intensity_multiplier = intensity_map.get(sport["intensity"], 1.0)
            
            # Prova prima con il nome originale (esatto)
            if original_sport_name in sports_data["sports"]:
                sport_info = sports_data["sports"][original_sport_name]
                final_sport_name = original_sport_name
            else:
                # Prova con il nome convertito (minuscolo + underscore)
                converted_sport_name = original_sport_name.lower().replace(" ", "_")
                if converted_sport_name in sports_data["sports"]:
                    sport_info = sports_data["sports"][converted_sport_name]
                    final_sport_name = converted_sport_name
                else:
                    # Cerca per corrispondenza parziale (case-insensitive)
                    possible_sports = []
                    
                    # Cerca corrispondenze esatte (case-insensitive)
                    for db_sport_name in sports_data["sports"]:
                        if original_sport_name.lower() == db_sport_name.lower():
                            possible_sports.append(db_sport_name)
                            break
                    
                    # Se non trova corrispondenze esatte, cerca sottostringhe
                    if not possible_sports:
                        for db_sport_name in sports_data["sports"]:
                            if (original_sport_name.lower() in db_sport_name.lower() or 
                                db_sport_name.lower() in original_sport_name.lower()):
                                possible_sports.append(db_sport_name)
                    
                    if not possible_sports:
                        # Lista degli sport disponibili per debug
                        available_sports = list(sports_data["sports"].keys())
                        raise ValueError(
                            f"Sport '{original_sport_name}' non trovato nel database. "
                            f"Sport disponibili: {available_sports[:10]}..." if len(available_sports) > 10 
                            else f"Sport disponibili: {available_sports}"
                        )
                    
                    # Usa il primo risultato trovato
                    final_sport_name = possible_sports[0]
                    sport_info = sports_data["sports"][final_sport_name]
            
            # Calcola il dispendio energetico per questo sport
            kcal_per_hour = sport_info["kcal_per_hour"] * intensity_multiplier
            kcal_per_session = kcal_per_hour * sport_hours
            kcal_per_week = kcal_per_session
            kcal_per_day = kcal_per_week / 7
            
            sport_result = {
                "sport_name": final_sport_name,
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

def get_user_id() -> str:
    """
    Ottiene l'ID dell'utente dal session state di Streamlit.
    
    Returns:
        str: ID dell'utente
        
    Raises:
        ValueError: Se l'utente non è loggato o l'ID non è disponibile
    """
    import streamlit as st
    
    # Prova prima a estrarre l'user_id dal nome del thread (per DeepSeek)
    import threading
    thread_name = threading.current_thread().name
    if "DeepSeekExtraction-" in thread_name:
        user_id = thread_name.replace("DeepSeekExtraction-", "")
        logger.info(f"ID utente estratto dal thread DeepSeek: {user_id}")
        return user_id
    
    # Fallback al session state di Streamlit
    if "user_info" not in st.session_state or "id" not in st.session_state.user_info:
        raise ValueError("Nessun utente autenticato. ID utente non disponibile.")
    return st.session_state.user_info["id"]


def load_user_basic_data(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Carica i dati di base dell'utente dal file JSON.
    
    Args:
        user_id: ID dell'utente (opzionale, usa get_user_id() se None)
        
    Returns:
        Dict con i dati di base dell'utente
        
    Raises:
        ValueError: Se il file utente non esiste o i dati sono incompleti
    """
    if user_id is None:
        user_id = get_user_id()
    
    # Fix: Handle user_id that may already contain 'user_' prefix
    if user_id.startswith("user_"):
        user_file_path = f"user_data/{user_id}.json"
    else:
        user_file_path = f"user_data/user_{user_id}.json"
    
    logger.info(f"🔍 DEBUG load_user_basic_data:")
    logger.info(f"   📁 User ID: {user_id}")
    logger.info(f"   📄 File path: {user_file_path}")
    
    if not os.path.exists(user_file_path):
        raise ValueError(f"File utente {user_id} non trovato.")
    
    with open(user_file_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    logger.info(f"   ✅ File caricato con successo")
    
    # Estrai i dati di base dell'utente (prova multiple sezioni)
    user_info = user_data.get("user_info", {})
    nutritional_info = user_data.get("nutritional_info", {})
    
    # Mapping robusto per i campi - prova prima nutritional_info poi user_info
    basic_data = {
        "sesso": (nutritional_info.get("sesso") or user_info.get("sesso") or 
                 nutritional_info.get("gender") or user_info.get("gender", "")),
        "peso": (nutritional_info.get("peso") or user_info.get("peso") or 
                nutritional_info.get("weight") or user_info.get("weight") or 
                nutritional_info.get("peso_kg") or user_info.get("peso_kg", 0)),
        "altezza": (nutritional_info.get("altezza") or user_info.get("altezza") or 
                   nutritional_info.get("height") or user_info.get("height") or 
                   nutritional_info.get("altezza_cm") or user_info.get("altezza_cm", 0)),
        "età": (nutritional_info.get("età") or user_info.get("età") or 
               nutritional_info.get("age") or user_info.get("age") or 
               nutritional_info.get("eta") or user_info.get("eta", 0)),
        "attività": (nutritional_info.get("attività") or user_info.get("attività") or 
                    nutritional_info.get("activity_level") or user_info.get("activity_level") or 
                    nutritional_info.get("livello_attivita") or user_info.get("livello_attivita", "Sedentario"))
    }
    
    logger.info(f"   📊 Dati estratti:")
    logger.info(f"      Sesso: {basic_data['sesso']}")
    logger.info(f"      Peso: {basic_data['peso']} kg")
    logger.info(f"      Altezza: {basic_data['altezza']} cm")
    logger.info(f"      Età: {basic_data['età']} anni")
    logger.info(f"      Attività: {basic_data['attività']}")
    
    # Validazione dati
    required_fields = ["sesso", "peso", "altezza", "età"]
    missing_fields = [field for field in required_fields 
                     if not basic_data[field] or basic_data[field] == 0]
    
    if missing_fields:
        raise ValueError(f"Dati utente incompleti. Campi mancanti: {', '.join(missing_fields)}")
    
    return basic_data


def compute_Harris_Benedict_Equation(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcola il metabolismo basale e il fabbisogno energetico totale per l'utente.
    Estrae automaticamente i dati necessari dal file utente.
    
    Args:
        user_id: ID dell'utente (opzionale, usa get_user_id() se None)
        
    Returns:
        Dict con metabolismo basale e fabbisogno giornaliero
    """
    try:
        # Fix: Get user_id to avoid undefined variable reference
        if user_id is None:
            user_id = get_user_id()
        
        # Carica i dati dell'utente
        user_data = load_user_basic_data(user_id)
        
        sesso = str(user_data["sesso"]).lower()
        peso = float(user_data["peso"])
        altezza = float(user_data["altezza"])
        età = float(user_data["età"])
        livello_attività = str(user_data["attività"])
        
        logger.info(f"Calcolo Harris-Benedict per utente {user_id or 'current'}")
        logger.info(f"Parametri: {sesso}, {peso}kg, {altezza}cm, {età}anni, {livello_attività}")
        
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
            "laf_utilizzato": laf,
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Errore in compute_Harris_Benedict_Equation: {str(e)}")
        return {"error": str(e)}

def check_ultraprocessed_foods() -> Dict[str, Any]:
    """
    Controlla quali alimenti sono ultra-processati e fornisce raccomandazioni.
    
    Args:
        foods_with_grams: Dizionario con alimenti e relative grammature
    
    Returns:
        Dict con i risultati dell'analisi
    """
    result = db.check_ultraprocessed_foods()
    logger.info(f"Risultato check_ultraprocessed_foods: {result}")
    return result

def calculate_weight_goal_calories(kg_change: float, time_months: float, goal_type: str, bmr: Optional[float] = None) -> Dict[str, Any]:
    """
    Calcola il deficit o surplus calorico giornaliero per raggiungere l'obiettivo di peso.
    
    Args:
        kg_change: Numero di kg da cambiare (sempre positivo)
        time_months: Tempo in mesi per raggiungere l'obiettivo
        goal_type: "perdita_peso" o "aumento_massa"
        bmr: Metabolismo basale in kcal (opzionale, per verifica deficit)
    
    Returns:
        Dict contenente:
        - daily_calorie_adjustment: deficit/surplus calorico giornaliero (negativo per deficit, positivo per surplus)
        - warnings: lista di avvertimenti se applicabile
        - goal_type: tipo di obiettivo confermato
        - kg_per_month: velocità di cambiamento
    """
    try:
        result = db.calculate_weight_goal_calories(kg_change, time_months, goal_type, bmr)
        logger.info(f"Risultato calculate_weight_goal_calories: {result}")
        return result
    except Exception as e:
        logger.error(f"Errore in calculate_weight_goal_calories: {str(e)}")
        return {"error": str(e)}

def analyze_bmi_and_goals(peso: float, altezza: float, sesso: str, età: int, obiettivo: str) -> Dict[str, Any]:
    """
    Analizza BMI, peso forma e coerenza degli obiettivi del cliente.
    
    Args:
        peso: Peso attuale in kg
        altezza: Altezza in cm
        sesso: 'maschio' o 'femmina'
        età: Età in anni
        obiettivo: 'Perdita di peso', 'Mantenimento', 'Aumento di massa'
    
    Returns:
        Dict contenente:
        - bmi_attuale: valore BMI
        - categoria_bmi: classificazione BMI
        - peso_ideale_min/max/medio: range peso forma
        - obiettivo_coerente: bool se l'obiettivo è appropriato
        - raccomandazione: testo con raccomandazione se necessario
        - warnings: lista di avvertimenti
    """
    try:
        result = db.analyze_bmi_and_goals(peso, altezza, sesso, età, obiettivo)
        logger.info(f"Risultato analyze_bmi_and_goals: {result}")
        return result
    except Exception as e:
        logger.error(f"Errore in analyze_bmi_and_goals: {str(e)}")
        return {"error": str(e)}

def check_vitamins(foods_with_grams: Dict[str, float], sesso: str, età: int) -> Dict[str, Any]:
    """
    Controlla l'apporto vitaminico totale della dieta e lo confronta con i LARN.
    
    Args:
        foods_with_grams: Dizionario con alimenti e relative grammature {alimento: grammi}
        sesso: 'maschio' o 'femmina'
        età: Età in anni
    
    Returns:
        Dict contenente:
        - total_vitamins: totali vitaminici calcolati
        - larn_requirements: fabbisogni LARN per l'utente
        - vitamin_status: stato per ogni vitamina (sufficiente/insufficiente/eccessivo)
        - warnings: lista di avvertimenti
        - recommendations: raccomandazioni specifiche
        - foods_not_found: alimenti non trovati nel database
    """
    try:
        if not isinstance(foods_with_grams, dict):
            raise ValueError("Il parametro foods_with_grams deve essere un dizionario")
        
        result = db.check_vitamins(foods_with_grams, sesso, età)
        logger.info(f"Risultato check_vitamins: {result}")
        return result
    except Exception as e:
        logger.error(f"Errore in check_vitamins: {str(e)}")
        return {"error": str(e)}

def get_food_substitutes(food_name: str, grams: float, num_substitutes: int = 5) -> Dict[str, Any]:
    """
    Ottiene gli alimenti sostitutivi per un dato alimento e quantità basati sui macronutrienti.
    
    Args:
        food_name: Nome dell'alimento per cui cercare sostituti
        grams: Grammi dell'alimento di riferimento
        num_substitutes: Numero massimo di sostituti da restituire (default 5)
    
    Returns:
        Dict contenente:
        - available: bool se il sistema di sostituti è disponibile
        - substitutes: lista di sostituti con grammature equivalenti e dati nutrizionali
        - reference_food: dati dell'alimento di riferimento con quantità specificata
        - metadata: informazioni sul metodo di calcolo
    """
    try:
        if not isinstance(food_name, str) or not food_name.strip():
            raise ValueError("Il nome dell'alimento deve essere una stringa non vuota")
        
        try:
            grams = float(grams)
            if grams <= 0:
                raise ValueError("I grammi devono essere positivi")
        except (ValueError, TypeError):
            raise ValueError("I grammi devono essere un numero positivo")
        
        if not isinstance(num_substitutes, int) or num_substitutes < 1:
            num_substitutes = 5
        
        result = db.get_food_substitutes(food_name.strip(), grams, num_substitutes)
        logger.info(f"Risultato get_food_substitutes per {grams}g di {food_name}: {len(result.get('substitutes', []))} sostituti trovati")
        return result
    except Exception as e:
        logger.error(f"Errore in get_food_substitutes: {str(e)}")
        return {"error": str(e), "available": False}