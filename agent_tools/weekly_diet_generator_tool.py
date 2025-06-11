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


def load_predefined_days(user_id: str) -> Dict[str, Any]:
    """
    Carica i 6 giorni di dieta predefiniti dal file JSON.
    Seleziona automaticamente la versione pro o no_pro in base al fabbisogno proteico dell'utente.
    
    LOGICA SELEZIONE:
    - Se proteine totali giornaliere > 130g → usa "predefined_days_pro"
    - Se proteine totali giornaliere ≤ 130g → usa "predefined_days_no_pro"
    
    Args:
        user_id: ID dell'utente per calcolare il fabbisogno proteico
        
    Returns:
        Dict con i giorni predefiniti della versione appropriata
    """
    predefined_file = "agent_tools/predefined_weekly_meals.json"
    
    try:
        if os.path.exists(predefined_file):
            with open(predefined_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Calcola le proteine totali giornaliere dell'utente
            total_daily_proteins = calculate_user_daily_proteins(user_id)
            
            # Seleziona la versione appropriata
            if total_daily_proteins > 130:
                predefined_days = data.get("predefined_days_pro", {})
                version_used = "pro"
                logger.info(f"Proteine giornaliere: {total_daily_proteins:.1f}g > 130g → Uso versione PRO")
            else:
                predefined_days = data.get("predefined_days_no_pro", {})
                version_used = "no_pro"
                logger.info(f"Proteine giornaliere: {total_daily_proteins:.1f}g ≤ 130g → Uso versione NO_PRO")
            
            logger.info(f"Caricati giorni predefiniti da {predefined_file} (versione: {version_used})")
            
        else:
            logger.error(f"File {predefined_file} non trovato")
            predefined_days = {}
    except Exception as e:
        logger.error(f"Errore nel caricamento di {predefined_file}: {str(e)}")
        predefined_days = {}
    
    return predefined_days


def calculate_user_daily_proteins(user_id: str) -> float:
    """
    Calcola le proteine totali giornaliere dell'utente sommando tutti i pasti.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        Proteine totali giornaliere in grammi
    """
    try:
        # Fix: Handle user_id that may already contain 'user_' prefix
        if user_id.startswith("user_"):
            user_file_path = f"user_data/{user_id}.json"
        else:
            user_file_path = f"user_data/user_{user_id}.json"
        
        if not os.path.exists(user_file_path):
            logger.warning(f"File utente {user_id} non trovato, uso default 100g proteine")
            return 100.0
        
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        # Estrai i totali giornalieri
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        daily_macros = nutritional_info.get("daily_macros", {})
        totali_giornalieri = daily_macros.get("totali_giornalieri", {})
        
        total_proteins = totali_giornalieri.get("proteine_totali", 100.0)
        
        logger.info(f"Proteine totali giornaliere utente {user_id}: {total_proteins}g")
        return float(total_proteins)
        
    except Exception as e:
        logger.error(f"Errore nel calcolo proteine per utente {user_id}: {str(e)}")
        return 100.0  # Default fallback

def extract_day1_meal_structure(user_id: str) -> Optional[Dict[str, List[str]]]:
    """
    Estrae la struttura dei pasti del giorno 1 dal file utente.
    
    STRUTTURA OUTPUT:
    {
        "colazione": ["nome_alimento_1", "nome_alimento_2", ...],          # Lista alimenti per colazione
        "spuntino_mattutino": ["nome_alimento_1", ...],                    # Lista alimenti per spuntino mattutino
        "pranzo": ["nome_alimento_1", "nome_alimento_2", ...],             # Lista alimenti per pranzo
        "spuntino_pomeridiano": ["nome_alimento_1", ...],                  # Lista alimenti per spuntino pomeridiano
        "cena": ["nome_alimento_1", "nome_alimento_2", ...],               # Lista alimenti per cena
        "spuntino_serale": ["nome_alimento_1", ...]                        # Lista alimenti per spuntino serale
    }
    
    LOGICA:
    - Cerca in user_data/user_{user_id}.json -> nutritional_info_extracted -> registered_meals
    - Per ogni pasto registrato, estrae solo gli alimenti con quantita_g > 0
    - Normalizza i nomi dei pasti usando get_canonical_meal_name()
    - Include solo i pasti che hanno almeno un alimento valido
    - I pasti vuoti risultano come liste vuote []
    
    ESEMPIO OUTPUT REALE:
    {
        "colazione": ["fiocchi d'avena", "latte scremato", "uva", "burro di arachidi"],
        "spuntino_mattutino": [],           # Pasto non registrato o senza alimenti
        "pranzo": [],                       # Pasto non registrato o senza alimenti
        "spuntino_pomeridiano": [],         # Pasto non registrato o senza alimenti
        "cena": [],                         # Pasto non registrato o senza alimenti
        "spuntino_serale": []               # Pasto non registrato o senza alimenti
    }
    
    Args:
        user_id: ID dell'utente per cui estrarre la struttura
        
    Returns:
        Dict con la struttura dei pasti o None se errore/file non trovato
    """
    # Fix: Handle user_id that may already contain 'user_' prefix
    if user_id.startswith("user_"):
        user_file_path = f"user_data/{user_id}.json"
    else:
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
    """
    Adatta i pasti di un giorno predefinito alla struttura del giorno 1, escludendo i pasti vuoti.
    
    STRUTTURA INPUT:
    predefined_day = {
        "colazione": ["avena", "banana", "mandorle", "latte_scremato"],
        "spuntino_mattutino": ["yogurt_greco", "mirtilli"],
        "pranzo": ["riso_basmati", "pollo_petto", "zucchine", "olio_oliva"],
        "spuntino_pomeridiano": ["mela", "noci"],
        "cena": ["salmone", "patate_dolci", "broccoli", "olio_oliva"]
    }
    
    day1_structure = {
        "colazione": ["fiocchi d'avena", "latte scremato", "uva", "burro di arachidi"],  # NON VUOTO
        "spuntino_mattutino": [],                                                        # VUOTO
        "pranzo": [],                                                                    # VUOTO
        "spuntino_pomeridiano": [],                                                      # VUOTO
        "cena": [],                                                                      # VUOTO
        "spuntino_serale": []                                                            # VUOTO
    }
    
    STRUTTURA OUTPUT:
    {
        "colazione": ["avena", "banana", "mandorle", "latte_scremato"]  # Solo questo pasto viene incluso
        # Altri pasti NON vengono inclusi perché vuoti nel day1_structure
    }
    
    LOGICA:
    1. Itera sui pasti del GIORNO 1 (day1_structure)
    2. Per ogni pasto del giorno 1:
       - Se ha alimenti (lista NON vuota):
         * Cerca lo stesso pasto nel giorno predefinito
         * Se lo trova: copia gli alimenti del predefinito nell'output
         * Se non lo trova: crea un pasto vuoto nell'output
       - Se è vuoto (lista vuota):
         * SALTA completamente (non appare nell'output)
    3. I pasti del predefinito non presenti nel giorno 1 vengono IGNORATI
    
    CASO D'USO:
    - Serve per mantenere la stessa struttura temporale dei pasti dell'utente
    - Evita di generare pasti che l'utente normalmente non consuma
    - Garantisce coerenza tra giorno 1 (esistente) e giorni generati
    
    Args:
        predefined_day: Giorno predefinito con pasti completi
        day1_structure: Struttura estratta dal giorno 1 dell'utente
        
    Returns:
        Dict con solo i pasti corrispondenti a quelli non vuoti del giorno 1
    """
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
    """
    Applica le regole speciali per i giorni 3, 5, 7: copia specifici pasti dal giorno 1.
    
    SCOPO:
    Crea coerenza nella settimana copiando colazione e spuntini dal giorno 1 
    ai giorni 3, 5, 7, mantenendo varietà solo per pranzo e cena.
    
    STRUTTURA INPUT:
    days_dict = {
        "giorno_2": {"colazione": ["cereali"], "pranzo": ["pasta"], ...},
        "giorno_3": {"colazione": ["pane"], "pranzo": ["riso"], ...},
        ...
    }
    
    day1_structure = {
        "colazione": ["avena", "latte"],              # Verrà copiato
        "spuntino_mattutino": ["yogurt"],             # Verrà copiato  
        "spuntino_pomeridiano": ["frutta"],           # Verrà copiato
        "spuntino_serale": ["tisana"],                # Verrà copiato (AGGIUNTO)
        "pranzo": ["pasta"],                          # NON verrà copiato
        "cena": ["pollo"]                             # NON verrà copiato
    }
    
    STRUTTURA OUTPUT:
    days_dict = {
        "giorno_2": {"colazione": ["cereali"], ...},           # INVARIATO
        "giorno_3": {"colazione": ["avena", "latte"], ...},    # MODIFICATO: copiato dal giorno 1
        "giorno_4": {"colazione": ["pane"], ...},              # INVARIATO
        "giorno_5": {"colazione": ["avena", "latte"], ...},    # MODIFICATO: copiato dal giorno 1
        "giorno_6": {"colazione": ["toast"], ...},             # INVARIATO
        "giorno_7": {"colazione": ["avena", "latte"], ...}     # MODIFICATO: copiato dal giorno 1
    }
    
    LOGICA:
    1. Identifica giorni speciali: ["giorno_3", "giorno_5", "giorno_7"]
    2. Identifica pasti da copiare: ["colazione", "spuntino_mattutino", "spuntino_pomeridiano", "spuntino_serale"]
    3. Per ogni giorno speciale:
       - Per ogni pasto da copiare:
         * Copia ESATTAMENTE la lista alimenti dal day1_structure
         * SOVRASCRIVE completamente il contenuto esistente
         * Mantiene invariati pranzo e cena (varietà)
    
    MODIFICA RECENTE:
    - Aggiunto "spuntino_serale" alla lista meals_to_copy
    - Ora i giorni 3, 5, 7 avranno anche lo spuntino serale identico al giorno 1
    - Maggiore coerenza negli spuntini durante la settimana
    
    BENEFICI:
    • Pattern riconoscibile: giorni 1,3,5,7 hanno colazione/spuntini identici
    • Abitudini consolidate: rispetta le preferenze per i pasti minori
    • Varietà mantenuta: pranzo e cena rimangono diversificati
    • Semplificazione: meno decisioni per pasti di routine
    
    Args:
        days_dict: Dizionario con tutti i giorni già adattati
        day1_structure: Struttura pasti del giorno 1 di riferimento
        
    Returns:
        Dizionario modificato con regole speciali applicate ai giorni 3, 5, 7
    """
    special_days = ["giorno_3", "giorno_5", "giorno_7"]
    meals_to_copy = ["colazione", "spuntino_mattutino", "spuntino_pomeridiano", "spuntino_serale"]
    
    for day_key in special_days:
        if day_key in days_dict:
            for meal in meals_to_copy:
                if meal in day1_structure:
                    days_dict[day_key][meal] = day1_structure[meal].copy()
                    logger.info(f"Copiato {meal} dal giorno 1 al {day_key}")
    
    return days_dict


def optimize_day_portions(day_meals: Dict[str, List[str]], user_id: str) -> Dict[str, Any]:
    """Ottimizza le porzioni per tutti i pasti di un giorno."""
    optimized_day = {}
    
    for meal_name, food_list in day_meals.items():
        if not food_list:
            continue
            
        try:
            optimization_result = optimize_meal_portions(meal_name, food_list, user_id)
            
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
    """
    Genera automaticamente 6 giorni aggiuntivi di dieta (giorni 2-7) per l'utente.
    
    PIPELINE COMPLETA:
    1. Estrae la struttura dei pasti del giorno 1 dell'utente
    2. Carica i 6 giorni predefiniti dal file JSON
    3. Adatta ogni giorno predefinito alla struttura del giorno 1
    4. Applica regole speciali per giorni 3, 5, 7 (copia colazione e spuntini dal giorno 1)
    5. Ottimizza le porzioni di ogni pasto per ogni giorno
    
    STRUTTURA INPUT UTENTE (esempio):
    user_data/user_{user_id}.json → nutritional_info_extracted → registered_meals
    [
        {"nome_pasto": "colazione", "alimenti": [{"nome_alimento": "Avena", "quantita_g": 100}]},
        {"nome_pasto": "pranzo", "alimenti": [{"nome_alimento": "Pollo", "quantita_g": 110}, ...]},
        {"nome_pasto": "spuntino_pomeridiano", "alimenti": [{"nome_alimento": "Grissini", "quantita_g": 60}]},
        {"nome_pasto": "cena", "alimenti": [{"nome_alimento": "Salmone al forno", "quantita_g": 150}]}
    ]
    
    STRUTTURA OUTPUT:
    {
        "success": True,
        "giorni_generati": {
            "giorno_2": {
                "colazione": {
                    "alimenti": {"avena": 45, "banana": 120, "mandorle": 15, "latte_scremato": 200},
                    "target_nutrients": {"kcal": 592, "proteine": 28, "carboidrati": 76, "grassi": 20},
                    "actual_nutrients": {"kcal": 587, "proteine": 26, "carboidrati": 74, "grassi": 21},
                    "optimization_summary": "Ottimizzazione completata con successo"
                },
                "pranzo": {...},
                "spuntino_pomeridiano": {...},
                "cena": {...}
            },
            "giorno_3": {
                "colazione": {  # ← COPIATO dal giorno 1 (regola speciale)
                    "alimenti": {"Avena": 100},  # Identico al giorno 1
                    ...
                },
                "pranzo": {...},  # Diverso dal giorno 1
                "spuntino_pomeridiano": {  # ← COPIATO dal giorno 1 (regola speciale)
                    "alimenti": {"Grissini": 60, "Scaglie di Parmigiano": 30},  # Identico al giorno 1
                    ...
                },
                "cena": {...}  # Diverso dal giorno 1
            },
            "giorno_4": {...},  # Completamente diverso dal giorno 1
            "giorno_5": {...},  # Colazione e spuntini identici al giorno 1 (regola speciale)
            "giorno_6": {...},  # Completamente diverso dal giorno 1
            "giorno_7": {...}   # Colazione e spuntini identici al giorno 1 (regola speciale)
        },
        "user_id": "1749309652",
        "giorni_totali": 6,
        "summary": "Generati con successo 6 giorni aggiuntivi di dieta"
    }
    
    LOGICA ADATTAMENTO:
    • Solo i pasti NON vuoti del giorno 1 vengono generati negli altri giorni
    • Se l'utente ha solo colazione e cena, tutti i giorni avranno solo colazione e cena
    • Garantisce coerenza con le abitudini alimentari dell'utente
    
    REGOLE SPECIALI GIORNI 3, 5, 7:
    • Colazione identica al giorno 1 (abitudini consolidate)
    • Spuntino mattutino identico al giorno 1 (se presente)
    • Spuntino pomeridiano identico al giorno 1 (se presente)  
    • Spuntino serale identico al giorno 1 (se presente)
    • Pranzo e cena mantengono varietà (diversi dal giorno 1)
    
    VANTAGGI:
    • Pattern riconoscibile: giorni 1,3,5,7 hanno colazione/spuntini identici
    • Varietà garantita: pranzo e cena sempre diversi
    • Rispetto abitudini: mantiene la struttura temporale dell'utente
    • Ottimizzazione automatica: calcola grammature precise per ogni pasto
    
    REQUISITI:
    • File utente valido con pasti registrati
    • Contesto Streamlit attivo per l'ottimizzazione delle porzioni
    • File predefined_weekly_meals.json presente
    
    Args:
        user_id: ID dell'utente (opzionale, usa get_user_id() se None)
        
    Returns:
        Dict con i giorni generati e metadati del processo
        
    Raises:
        ValueError: Se impossibile estrarre struttura giorno 1
        Exception: Se errori durante il processo di generazione
        
    Examples:
        >>> result = generate_6_additional_days("1749309652")
        >>> print(f"Giorni generati: {result['giorni_totali']}")
        >>> print(f"Pasti nel giorno 2: {len(result['giorni_generati']['giorno_2'])}")
    """
    try:
        if user_id is None:
            user_id = get_user_id()
        
        logger.info(f"Avvio generazione 6 giorni aggiuntivi per utente {user_id}")
        
        predefined_days = load_predefined_days(user_id)
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
            final_days[day_key] = optimize_day_portions(day_meals, user_id)
        
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