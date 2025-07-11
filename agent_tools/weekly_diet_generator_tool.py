"""
Tool per la generazione automatica di 6 giorni aggiuntivi di dieta.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

from .meal_optimization_tool import optimize_meal_portions
from .nutridb_tool import get_user_id

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def normalize_meal_name(name):
    """Normalizza un nome di pasto per il confronto"""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def parse_day_range(day_range_str: str) -> List[int]:
    """
    Parsa una stringa di range giorni e restituisce una lista di numeri di giorni validi.
    
    FORMATI SUPPORTATI:
    - Range: "2-4" → [2, 3, 4]
    - Lista: "3,5,7" → [3, 5, 7] 
    - Singolo: "2" → [2]
    - Mix: "2,4-6" → [2, 4, 5, 6]
    
    VALIDAZIONE:
    - Solo giorni nel range 2-7 (il giorno 1 è già presente)
    - Rimuove duplicati e ordina
    - Solleva ValueError per input non validi
    
    Args:
        day_range_str: Stringa che specifica i giorni da generare
        
    Returns:
        Lista ordinata di numeri di giorni validi (2-7)
        
    Raises:
        ValueError: Se il formato è invalido o contiene giorni fuori range
        
    Examples:
        >>> parse_day_range("2-4")
        [2, 3, 4]
        >>> parse_day_range("3,5,7")
        [3, 5, 7]
        >>> parse_day_range("2,4-6")
        [2, 4, 5, 6]
    """
    if not day_range_str or not isinstance(day_range_str, str):
        raise ValueError("day_range deve essere una stringa non vuota")
    
    try:
        days = set()  # Usa set per evitare duplicati
        
        # Dividi per virgole per gestire liste
        parts = [part.strip() for part in day_range_str.split(',')]
        
        for part in parts:
            if '-' in part:
                # Gestisci range (es. "2-4")
                range_parts = part.split('-')
                if len(range_parts) != 2:
                    raise ValueError(f"Range invalido: '{part}'. Usa formato 'start-end'")
                
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
                
                if start > end:
                    raise ValueError(f"Range invalido: '{part}'. Start deve essere <= end")
                
                days.update(range(start, end + 1))
            else:
                # Gestisci numero singolo
                day = int(part.strip())
                days.add(day)
        
        # Valida che tutti i giorni siano nel range 2-7
        valid_days = []
        for day in days:
            if not (2 <= day <= 7):
                raise ValueError(f"Giorno {day} fuori range. Giorni validi: 2-7")
            valid_days.append(day)
        
        # Ordina e restituisci
        valid_days.sort()
        
        if not valid_days:
            raise ValueError("Nessun giorno valido trovato")
        
        logger.info(f"Range giorni parsato: '{day_range_str}' → {valid_days}")
        return valid_days
        
    except ValueError as ve:
        # Re-raise ValueError con messaggio originale
        raise ve
    except Exception as e:
        raise ValueError(f"Errore nel parsing range '{day_range_str}': {str(e)}")


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
        "spuntino": "spuntino_pomeridiano",  # Spuntino generico = pomeridiano per default
        "snack": "spuntino_pomeridiano",     # Snack generico = pomeridiano per default
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

# get_user_id è ora importato da nutridb_tool


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
    Estrae la struttura dei pasti da daily_macros invece che da weekly_diet_day_1.
    
    STRUTTURA OUTPUT:
    {
        "colazione": ["placeholder"],           # Pasto sempre presente se definito in daily_macros
        "spuntino_mattutino": [],              # Pasto presente solo se definito
        "pranzo": ["placeholder"],             # Pasto sempre presente se definito in daily_macros  
        "spuntino_pomeridiano": ["placeholder"], # Pasto presente solo se definito
        "cena": ["placeholder"],               # Pasto sempre presente se definito in daily_macros
        "spuntino_serale": []                  # Pasto presente solo se definito
    }
    
    LOGICA:
    - Usa daily_macros.distribuzione_pasti come fonte di verità per la struttura dei pasti
    - Questa struttura è sempre completa e definita, a differenza di weekly_diet_day_1
    - Per ogni pasto presente in daily_macros, crea una voce con placeholder
    - Garantisce che tutti i pasti pianificati (inclusa la cena) siano inclusi
    
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
        
        # Estrai la struttura dai daily_macros invece che da weekly_diet_day_1
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        daily_macros = nutritional_info.get("daily_macros", {})
        distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
        
        if not distribuzione_pasti:
            logger.warning("Nessuna distribuzione pasti trovata in daily_macros")
            return None
        
        # Inizializza la struttura usando i pasti definiti in daily_macros
        day1_structure = {}
        
        # Per ogni pasto definito in daily_macros, crea una voce
        for meal_name in distribuzione_pasti.keys():
            # Ottieni il nome canonico del pasto
            canonical_meal_name = get_canonical_meal_name(meal_name)
            
            # Aggiungi il pasto con un placeholder (indica che il pasto è previsto)
            day1_structure[canonical_meal_name] = ["placeholder"]
            logger.info(f"Aggiunto pasto {canonical_meal_name} (da daily_macros)")
        
        # Verifica che almeno un pasto sia stato estratto
        if not day1_structure:
            logger.warning("Nessun pasto trovato in daily_macros")
            return None
        
        logger.info(f"Struttura estratta da daily_macros: {list(day1_structure.keys())}")
        return day1_structure
        
    except Exception as e:
        logger.error(f"Errore nel leggere il file utente: {str(e)}")
        return None


def extract_day1_real_meals(user_id: str) -> Optional[Dict[str, List[str]]]:
    """
    Estrae gli alimenti REALI dal giorno 1 dell'utente (non placeholder).
    
    SCOPO:
    Diversamente da extract_day1_meal_structure che estrae solo la struttura dei pasti,
    questa funzione estrae gli alimenti concreti registrati nel weekly_diet_day_1.
    
    STRUTTURA INPUT:
    user_data/user_{user_id}.json → nutritional_info_extracted → weekly_diet_day_1
    [
        {"nome_pasto": "colazione", "alimenti": [{"nome_alimento": "Avena", "quantita_g": 100}]},
        {"nome_pasto": "pranzo", "alimenti": [{"nome_alimento": "Pollo", "quantita_g": 110}, ...]},
        {"nome_pasto": "spuntino_pomeridiano", "alimenti": [{"nome_alimento": "Grissini", "quantita_g": 60}]},
        {"nome_pasto": "cena", "alimenti": [{"nome_alimento": "Salmone al forno", "quantita_g": 150}]}
    ]
    
    STRUTTURA OUTPUT:
    {
        "colazione": ["avena"],
        "pranzo": ["pollo", "zucchine", "olio_oliva"],
        "spuntino_pomeridiano": ["grissini"],
        "cena": ["salmone_al_forno", "patate_dolci", "broccoli"]
    }
    
    LOGICA:
    1. Legge weekly_diet_day_1 dal file utente
    2. Per ogni pasto registrato:
       - Estrae tutti i nomi degli alimenti
       - Normalizza i nomi per la compatibilità con il database
       - Salta alimenti con quantità 0 o nulle
    3. Restituisce solo pasti con alimenti effettivi
    
    DIFFERENZA CON extract_day1_meal_structure:
    - extract_day1_meal_structure: restituisce {"colazione": ["placeholder"]}
    - extract_day1_real_meals: restituisce {"colazione": ["avena", "latte_scremato"]}
    
    USO:
    Questa funzione è destinata ad apply_special_rules_for_days_357 per copiare
    gli alimenti REALI del giorno 1 ai giorni 3, 5, 7.
    
    Args:
        user_id: ID dell'utente per cui estrarre gli alimenti reali
        
    Returns:
        Dict con liste di alimenti reali per ogni pasto o None se errore
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
        
        # Estrai i pasti reali dal weekly_diet_day_1
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        weekly_diet_day_1 = nutritional_info.get("weekly_diet_day_1", [])
        
        if not weekly_diet_day_1:
            logger.warning("Nessun pasto trovato in weekly_diet_day_1")
            return None
        
        # Inizializza la struttura per gli alimenti reali
        day1_real_meals = {}
        
        # Per ogni pasto registrato nel giorno 1
        for meal_data in weekly_diet_day_1:
            meal_name = meal_data.get("nome_pasto", "")
            alimenti = meal_data.get("alimenti", [])
            
            if not meal_name or not alimenti:
                continue
            
            # Ottieni il nome canonico del pasto
            canonical_meal_name = get_canonical_meal_name(meal_name)
            
            # Estrai i nomi degli alimenti
            food_names = []
            for alimento in alimenti:
                nome_alimento = alimento.get("nome_alimento", "")
                quantita = alimento.get("quantita_g", 0)
                
                # Salta alimenti vuoti o con quantità 0
                if not nome_alimento or quantita <= 0:
                    continue
                
                # Normalizza il nome dell'alimento
                normalized_name = nome_alimento.lower().replace(" ", "_")
                food_names.append(normalized_name)
            
            # Aggiungi il pasto solo se ha alimenti
            if food_names:
                day1_real_meals[canonical_meal_name] = food_names
                logger.info(f"Estratti {len(food_names)} alimenti per {canonical_meal_name}")
        
        # Verifica che almeno un pasto sia stato estratto
        if not day1_real_meals:
            logger.warning("Nessun alimento reale trovato in weekly_diet_day_1")
            return None
        
        logger.info(f"Alimenti reali estratti dal giorno 1: {list(day1_real_meals.keys())}")
        return day1_real_meals
        
    except Exception as e:
        logger.error(f"Errore nell'estrazione degli alimenti reali: {str(e)}")
        return None


def adapt_meals_to_day1_structure(predefined_day: Dict[str, List[str]], 
                                day1_structure: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Adatta i pasti di un giorno predefinito alla struttura definita in daily_macros.
    
    STRUTTURA INPUT:
    predefined_day = {
        "colazione": ["avena", "banana", "mandorle", "latte_scremato"],
        "spuntino_mattutino": ["yogurt_greco", "mirtilli"],
        "pranzo": ["riso_basmati", "pollo_petto", "zucchine", "olio_oliva"],
        "spuntino_pomeridiano": ["mela", "noci"],
        "cena": ["salmone", "patate_dolci", "broccoli", "olio_oliva"]
    }
    
    day1_structure = {
        "colazione": ["placeholder"],           # Presente in daily_macros
        "pranzo": ["placeholder"],             # Presente in daily_macros
        "spuntino_pomeridiano": ["placeholder"], # Presente in daily_macros
        "cena": ["placeholder"]                # Presente in daily_macros
    }
    
    STRUTTURA OUTPUT:
    {
        "colazione": ["avena", "banana", "mandorle", "latte_scremato"],
        "pranzo": ["riso_basmati", "pollo_petto", "zucchine", "olio_oliva"],
        "spuntino_pomeridiano": ["mela", "noci"],
        "cena": ["salmone", "patate_dolci", "broccoli", "olio_oliva"]
    }
    
    LOGICA:
    1. Itera sui pasti definiti in daily_macros (day1_structure)
    2. Per ogni pasto definito:
       - Cerca lo stesso pasto nel giorno predefinito
       - Se lo trova: copia gli alimenti del predefinito nell'output
       - Se non lo trova: crea un pasto vuoto nell'output
    3. Tutti i pasti definiti in daily_macros vengono sempre inclusi
    
    CASO D'USO:
    - Garantisce che tutti i pasti pianificati (inclusa la cena) siano generati
    - Mantiene la struttura definita dall'utente in daily_macros
    - Risolve il problema delle cene mancanti
    
    Args:
        predefined_day: Giorno predefinito con pasti completi
        day1_structure: Struttura estratta da daily_macros
        
    Returns:
        Dict con tutti i pasti definiti in daily_macros
    """
    adapted_day = {}
    
    # Includi tutti i pasti definiti in daily_macros (tutti hanno placeholder)
    for meal_name in day1_structure.keys():
        if meal_name in predefined_day:
            adapted_day[meal_name] = predefined_day[meal_name]
            logger.info(f"Adattato {meal_name} dal giorno predefinito")
        else:
            adapted_day[meal_name] = []
            logger.warning(f"Pasto '{meal_name}' non trovato nel giorno predefinito")
    
    return adapted_day


def apply_special_rules_for_days_357(days_dict: Dict[str, Dict[str, List[str]]],
                                   day1_structure: Dict[str, List[str]], 
                                   user_id: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Applica le regole speciali per i giorni 3, 5, 7: copia specifici pasti dal giorno 1.
    
    SCOPO:
    Crea coerenza nella settimana copiando colazione e spuntini REALI dal giorno 1 
    ai giorni 3, 5, 7, mantenendo varietà solo per pranzo e cena.
    
    MODIFICA IMPORTANTE:
    Ora questa funzione copia gli alimenti REALI dal giorno 1, non i placeholder.
    Usa extract_day1_real_meals per ottenere gli alimenti effettivi registrati.
    
    STRUTTURA INPUT:
    days_dict = {
        "giorno_2": {"colazione": ["cereali"], "pranzo": ["pasta"], ...},
        "giorno_3": {"colazione": ["pane"], "pranzo": ["riso"], ...},
        ...
    }
    
    day1_structure = {
        "colazione": ["placeholder"],              # NON viene più usato per la copia
        "spuntino_mattutino": ["placeholder"],     # NON viene più usato per la copia  
        ...
    }
    
    user_id = "1749309652"  # Usato per estrarre alimenti reali
    
    STRUTTURA ESTRATTA (day1_real_meals):
    {
        "colazione": ["avena", "latte_scremato"],         # Alimenti REALI dal giorno 1
        "spuntino_mattutino": ["yogurt_greco"],           # Alimenti REALI dal giorno 1  
        "spuntino_pomeridiano": ["grissini", "parmigiano"], # Alimenti REALI dal giorno 1
        "pranzo": ["pollo", "zucchine", "olio_oliva"],    # NON verrà copiato
        "cena": ["salmone", "patate", "broccoli"]         # NON verrà copiato
    }
    
    STRUTTURA OUTPUT:
    days_dict = {
        "giorno_2": {"colazione": ["cereali"], ...},                    # INVARIATO
        "giorno_3": {"colazione": ["avena", "latte_scremato"], ...},    # MODIFICATO: alimenti reali dal giorno 1
        "giorno_4": {"colazione": ["pane"], ...},                       # INVARIATO
        "giorno_5": {"colazione": ["avena", "latte_scremato"], ...},    # MODIFICATO: alimenti reali dal giorno 1
        "giorno_6": {"colazione": ["toast"], ...},                      # INVARIATO
        "giorno_7": {"colazione": ["avena", "latte_scremato"], ...}     # MODIFICATO: alimenti reali dal giorno 1
    }
    
    LOGICA:
    1. Estrae gli alimenti REALI dal giorno 1 usando extract_day1_real_meals
    2. Identifica giorni speciali: ["giorno_3", "giorno_5", "giorno_7"]
    3. Identifica pasti da copiare: ["colazione", "spuntino_mattutino", "spuntino_pomeridiano", "spuntino_serale"]
    4. Per ogni giorno speciale:
       - Per ogni pasto da copiare:
         * Copia ESATTAMENTE la lista alimenti REALI dal giorno 1
         * SOVRASCRIVE completamente il contenuto esistente
         * Mantiene invariati pranzo e cena (varietà)
    
    BENEFICI:
    • Risolve il problema dei "placeholder" nell'ottimizzazione
    • Garantisce che i giorni 3, 5, 7 abbiano alimenti identici al giorno 1
    • Mantiene pattern riconoscibili e abitudini consolidate
    • Evita errori di "alimenti non trovati nel database"
    
    Args:
        days_dict: Dizionario con tutti i giorni già adattati
        day1_structure: Struttura pasti del giorno 1 (per controllo compatibilità)
        user_id: ID utente per estrarre alimenti reali dal giorno 1
        
    Returns:
        Dizionario modificato con regole speciali applicate ai giorni 3, 5, 7
    """
    # Estrai gli alimenti REALI dal giorno 1
    day1_real_meals = extract_day1_real_meals(user_id)
    
    if not day1_real_meals:
        logger.warning("Impossibile estrarre alimenti reali dal giorno 1, uso fallback ai giorni predefiniti")
        return days_dict
    
    special_days = ["giorno_3", "giorno_5", "giorno_7"]
    meals_to_copy = ["colazione", "spuntino_mattutino", "spuntino_pomeridiano", "spuntino_serale"]
    
    for day_key in special_days:
        if day_key in days_dict:
            for meal in meals_to_copy:
                # Copia gli alimenti REALI se disponibili
                if meal in day1_real_meals:
                    days_dict[day_key][meal] = day1_real_meals[meal].copy()
                    logger.info(f"Copiati {len(day1_real_meals[meal])} alimenti reali di {meal} dal giorno 1 al {day_key}")
                # Fallback: mantieni la struttura se il pasto esiste ma non ha alimenti reali
                elif meal in day1_structure:
                    logger.info(f"Mantenuto {meal} predefinito per {day_key} (nessun alimento reale nel giorno 1)")
    
    return days_dict


def optimize_day_portions(day_meals: Dict[str, List[str]], user_id: str, include_substitutes: bool = True) -> Dict[str, Any]:
    """Ottimizza le porzioni per tutti i pasti di un giorno."""
    optimized_day = {}
    
    for meal_name, food_list in day_meals.items():
        if not food_list:
            continue
            
        try:
            optimization_result = optimize_meal_portions(meal_name, food_list, user_id)
            
            if optimization_result.get("success", False):
                meal_data = {
                    "alimenti": optimization_result.get("portions", {}),
                    "target_nutrients": optimization_result.get("target_nutrients", {}),
                    "actual_nutrients": optimization_result.get("actual_nutrients", {}),
                    "macro_single_foods": optimization_result.get("macro_single_foods", {}),
                    "optimization_summary": optimization_result.get("optimization_summary", "")
                }
                
                # Includi i sostituti solo se richiesto
                if include_substitutes:
                    meal_data["substitutes"] = optimization_result.get("substitutes", {})
                
                optimized_day[meal_name] = meal_data
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


def generate_6_additional_days(user_id: Optional[str] = None, day_range: Optional[str] = None) -> Dict[str, Any]:
    """
    Genera automaticamente giorni aggiuntivi di dieta per l'utente.
    
    Se day_range non è specificato, genera tutti i 6 giorni (giorni 2-7).
    Se day_range è specificato, genera solo i giorni richiesti (es. "2-4" per giorni 2,3,4).
    
    PIPELINE COMPLETA:
    1. Estrae la struttura dei pasti del giorno 1 dell'utente
    2. Parsa il range giorni richiesto (se specificato)
    3. Carica i 6 giorni predefiniti dal file JSON
    4. Adatta ogni giorno predefinito alla struttura del giorno 1
    5. Applica regole speciali per giorni 3, 5, 7 (copia colazione e spuntini dal giorno 1)
    6. Ottimizza le porzioni di ogni pasto per ogni giorno
    7. Include nei risultati finali solo i giorni richiesti
    
    STRUTTURA INPUT UTENTE (esempio):
    user_data/user_{user_id}.json → nutritional_info_extracted → weekly_diet_day_1
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
        day_range: Range giorni da generare (opzionale, tutti i giorni 2-7 se None)
                  Formati supportati: "2-4", "3,5,7", "2", "2,4-6"
        
    Returns:
        Dict con i giorni generati e metadati del processo
        
    Raises:
        ValueError: Se impossibile estrarre struttura giorno 1 o day_range invalido
        Exception: Se errori durante il processo di generazione
        
    Examples:
        >>> result = generate_6_additional_days("1749309652")
        >>> print(f"Giorni generati: {result['giorni_totali']}")
        >>> print(f"Pasti nel giorno 2: {len(result['giorni_generati']['giorno_2'])}")
        
        >>> result = generate_6_additional_days("1749309652", "2-4")
        >>> print(f"Giorni richiesti: 2-4")
        >>> print(f"Giorni generati: {list(result['giorni_generati'].keys())}")
        
        >>> result = generate_6_additional_days("1749309652", "3,5,7")
        >>> print(f"Solo giorni dispari: {list(result['giorni_generati'].keys())}")
    """
    try:
        if user_id is None:
            user_id = get_user_id()
        
        # Parsa il range giorni richiesto
        if day_range is not None:
            requested_days = parse_day_range(day_range)
            logger.info(f"Avvio generazione giorni {requested_days} per utente {user_id} (range: '{day_range}')")
        else:
            requested_days = None  # None significa tutti i giorni
            logger.info(f"Avvio generazione 6 giorni aggiuntivi per utente {user_id} (comportamento standard)")
        
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
        
        adapted_days = apply_special_rules_for_days_357(adapted_days, day1_structure, user_id)
        logger.info("Applicate regole speciali per giorni 3, 5, 7")
        
        final_days = {}
        for day_key, day_meals in adapted_days.items():
            # Estrai il numero del giorno dalla chiave (es. "giorno_2" → 2)
            day_number = int(day_key.split("_")[1])
            
            # Se è specificato un range, controlla se questo giorno è incluso
            if requested_days is not None and day_number not in requested_days:
                logger.info(f"Saltato {day_key} (non nel range richiesto)")
                continue
            
            logger.info(f"Ottimizzazione {day_key}...")
            final_days[day_key] = optimize_day_portions(day_meals, user_id, include_substitutes=False)
        
        logger.info("Generazione completata con successo")
        
        import time
        
        result = {
            "success": True,
            "giorni_generati": final_days,
            "user_id": user_id,
            "giorni_totali": len(final_days),
            "day_range_requested": day_range,
            "requested_days": requested_days,
            "generation_timestamp": time.time(),
            "summary": f"Generati con successo {len(final_days)} giorni{f' (range: {day_range})' if day_range else ' aggiuntivi'} di dieta"
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