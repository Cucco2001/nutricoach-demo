#!/usr/bin/env python3
"""
Generatore di diete alternative basato su sostituti alimentari
"""

import json
import random
import os
from typing import Dict, List, Any, Optional
import sys
import logging

# Aggiungi il percorso del progetto per importare i tool
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent_tools.user_data_manager import UserDataManager

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURAZIONE: ALIMENTI DA NON SOSTITUIRE
# =============================================================================
# Lista degli alimenti che devono essere mantenuti invariati nelle diete alternative
# Questi alimenti vengono considerati "ingredienti base" o "condimenti essenziali"
FOODS_NOT_TO_SUBSTITUTE = {
    # Oli e grassi di condimento
    "olio_oliva", "olio_extravergine_oliva", "olio_oliva_extravergine", "latte_intero", "latte_scremato"
}

# Nota: Puoi facilmente modificare questa lista aggiungendo o rimuovendo alimenti
# I nomi devono corrispondere ai nomi nel database (formato snake_case)
# =============================================================================

def get_user_id() -> str:
    """Ottiene l'ID utente da Streamlit o usa il valore di debug"""
    try:
        import streamlit as st
        if hasattr(st, 'session_state') and 'user_info' in st.session_state:
            return st.session_state.user_info["id"]
    except ImportError:
        pass
    
    # Fallback per debug - usa l'utente che termina per 52
    return "user_1749309652"

def load_user_data(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Carica i dati dell'utente utilizzando UserDataManager"""
    if user_id is None:
        user_id = get_user_id()
    
    # Inizializza il manager dei dati utente
    user_manager = UserDataManager()
    
    # Verifica che il file utente esista
    user_dir = "user_data"
    user_file = os.path.join(user_dir, f"{user_id}.json")
    
    if not os.path.exists(user_file):
        raise FileNotFoundError(f"File utente {user_file} non trovato")
    
    # Carica i dati usando il manager
    user_manager._load_user_data(user_id)
    
    # Carica i dati completi dal file per accedere anche ai dati di DeepSeek
    with open(user_file, 'r', encoding='utf-8') as f:
        complete_user_data = json.load(f)
    
    logger.info(f"📁 Dati caricati per utente {user_id}")
    return complete_user_data

def load_substitutes_database() -> Dict[str, Dict[str, Dict[str, float]]]:
    """Carica il database dei sostituti alimentari"""
    substitutes_file = "Dati_processed/alimenti_sostitutivi.json"
    
    if not os.path.exists(substitutes_file):
        raise FileNotFoundError(f"File dei sostituti {substitutes_file} non trovato")
    
    with open(substitutes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("substitutes", {})

def load_nutridb():
    """Carica l'istanza del database nutrizionale"""
    try:
        from agent_tools.nutridb import NutriDB
        return NutriDB("Dati_processed")
    except Exception as e:
        logger.error(f"Errore nel caricamento del NutriDB: {str(e)}")
        raise

def should_substitute_food(food_name: str) -> bool:
    """
    Controlla se un alimento deve essere sostituito o mantenuto invariato
    
    Args:
        food_name: Nome dell'alimento (formato database)
        
    Returns:
        True se l'alimento deve essere sostituito, False se deve essere mantenuto
    """
    # Normalizza il nome per il confronto
    normalized_name = food_name.lower().replace(" ", "_")
    
    # Controlla se è nella lista degli alimenti da non sostituire
    if normalized_name in FOODS_NOT_TO_SUBSTITUTE:
        return False
    
    # Controlli aggiuntivi per varianti comuni
    for protected_food in FOODS_NOT_TO_SUBSTITUTE:
        # Controlla se il nome contiene uno degli alimenti protetti
        if protected_food in normalized_name or normalized_name in protected_food:
            return False
        
        # Controlli speciali per varianti comuni di oli
        if "olio" in protected_food and "olio" in normalized_name:
            # Se entrambi contengono "olio", controlla se condividono altri elementi
            protected_parts = set(protected_food.split("_"))
            name_parts = set(normalized_name.split("_"))
            
            # Se condividono "olio" e almeno un altro elemento (oliva, extravergine, etc.)
            common_parts = protected_parts.intersection(name_parts)
            if len(common_parts) >= 2 and "olio" in common_parts:
                return False
    
    return True

def map_food_name_to_db_format(food_name: str) -> str:
    """
    Mappa il nome dell'alimento al formato utilizzato nel database usando gli alias di NutriDB
    
    Args:
        food_name: Nome dell'alimento da mappare
        
    Returns:
        Nome dell'alimento nel formato del database
    """
    global _nutridb_instance
    if '_nutridb_instance' not in globals():
        _nutridb_instance = load_nutridb()
    
    # Normalizza il nome come fa il NutriDB
    normalized_name = food_name.lower().replace("_", " ").strip()
    
    # Usa il sistema di alias del NutriDB
    db_key = _nutridb_instance.alias.get(normalized_name)
    
    if db_key:
        return db_key
    else:
        # Fallback: restituisce il nome originale se non trovato negli alias
        logger.warning(f"Alimento '{food_name}' non trovato negli alias, uso nome originale")
        return food_name.lower().replace(" ", "_")

def get_food_substitute(food_name: str, substitutes_db: Dict[str, Any]) -> Optional[str]:
    """
    Ottiene un sostituto randomico pesato per un alimento
    
    Args:
        food_name: Nome dell'alimento nel formato database
        substitutes_db: Database dei sostituti
        
    Returns:
        Nome del sostituto scelto o None se non ci sono sostituti
    """
    if food_name not in substitutes_db:
        logger.warning(f"Nessun sostituto trovato per {food_name}")
        return None
    
    substitutes = substitutes_db[food_name]
    
    if not substitutes:
        return None
    
    # Crea liste per la selezione pesata
    substitute_names = list(substitutes.keys())
    weights = [substitutes[name]["similarity_score"] for name in substitute_names]
    
    # Normalizza i pesi (similarity_score è già 0-100, ma assicuriamoci che siano positivi)
    weights = [max(w, 1) for w in weights]  # Peso minimo 1
    
    # Selezione randomica pesata
    selected_substitute = random.choices(substitute_names, weights=weights, k=1)[0]
    
    logger.info(f"Sostituto scelto per {food_name}: {selected_substitute} (score: {substitutes[selected_substitute]['similarity_score']})")
    
    return selected_substitute

def get_breakfast_substitute(food_name: str, substitutes_db: Dict[str, Any]) -> Optional[List[str]]:
    """
    Ottiene sostituti specifici per la colazione con regole speciali
    
    Args:
        food_name: Nome dell'alimento nel formato database
        substitutes_db: Database dei sostituti
        
    Returns:
        Lista di nomi dei sostituti o None se non ci sono sostituti
    """
    # Usa gli alias di NutriDB per identificare correttamente uova e albumi
    global _nutridb_instance
    if '_nutridb_instance' not in globals():
        _nutridb_instance = load_nutridb()
    
    # Normalizza il nome come fa il NutriDB
    normalized_name = food_name.lower().replace("_", " ").strip()
    
    # Ottieni la chiave canonica usando gli alias
    canonical_key = _nutridb_instance.alias.get(normalized_name, food_name.lower())
    
    # Regole speciali per la colazione
    
    # Caso 1: Uova/albumi a colazione - sostituisci hard-coded con ENTRAMBI prosciutto E formaggio
    if canonical_key in ["uova", "albume_uova"] or "uova" in canonical_key or "albume" in canonical_key:
        logger.info(f"🍳 Regola speciale colazione: sostituzione hard-coded per {canonical_key}")
        
        # Lista hard-coded di ENTRAMBI i sostituti per uova a colazione
        egg_breakfast_substitutes = [
            "prosciutto_crudo",
            "parmigiano_reggiano"
        ]
        
        logger.info(f"🍳 Sostituti colazione per uova/albumi: {egg_breakfast_substitutes}")
        return egg_breakfast_substitutes
    
    # Caso 2: Pane a colazione - non può essere sostituito
    if "pane" in canonical_key:
        logger.info(f"🍞 Regola speciale colazione: il pane non può essere sostituito")
        return None
    
    # Per altri alimenti, usa la logica standard (ritorna come lista per compatibilità)
    single_substitute = get_food_substitute(food_name, substitutes_db)
    return [single_substitute] if single_substitute else None

def get_snack_substitute(food_name: str, substitutes_db: Dict[str, Any]) -> Optional[List[str]]:
    """
    Ottiene sostituti specifici per gli spuntini con regole speciali
    
    Args:
        food_name: Nome dell'alimento nel formato database
        substitutes_db: Database dei sostituti
        
    Returns:
        Lista di nomi dei sostituti o None se non ci sono sostituti
    """
    # Usa gli alias di NutriDB per identificare correttamente gli alimenti
    global _nutridb_instance
    if '_nutridb_instance' not in globals():
        _nutridb_instance = load_nutridb()
    
    # Normalizza il nome come fa il NutriDB
    normalized_name = food_name.lower().replace("_", " ").strip()
    
    # Ottieni la chiave canonica usando gli alias
    canonical_key = _nutridb_instance.alias.get(normalized_name, food_name.lower())
    
    # Regole speciali per gli spuntini
    
    # Caso 1: Pane negli spuntini - sostituisci solo con pan bauletto
    if "pane" in canonical_key:
        logger.info(f"🥖 Regola speciale spuntino: sostituzione pane con pan bauletto per {canonical_key}")
        
        # Lista hard-coded per sostituire il pane negli spuntini
        bread_snack_substitutes = [
            "pan_bauletto"
        ]
        
        logger.info(f"🥖 Sostituti spuntino per pane: {bread_snack_substitutes}")
        return bread_snack_substitutes
    
    # Per altri alimenti, usa la logica standard (ritorna come lista per compatibilità)
    single_substitute = get_food_substitute(food_name, substitutes_db)
    return [single_substitute] if single_substitute else None

def create_alternative_meal(original_meal: Dict[str, Any], substitutes_db: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un pasto alternativo sostituendo gli alimenti con sostituti randomici e ottimizza le porzioni
    
    Args:
        original_meal: Pasto originale
        substitutes_db: Database dei sostituti
        
    Returns:
        Nuovo pasto con alimenti sostituiti e porzioni ottimizzate
    """
    meal_name = original_meal["nome_pasto"]
    
    # Usa normalize_meal_name per determinare se siamo a colazione o negli spuntini
    try:
        from agent_tools.meal_optimization_tool import normalize_meal_name
        
        # Normalizza il nome del pasto
        normalized_meal = normalize_meal_name(meal_name)
        
        # Controlla se siamo a colazione
        is_breakfast = normalized_meal == "colazione"
        if is_breakfast:
            logger.info(f"🍳 Applicando regole speciali per colazione: {meal_name} (normalizzato: {normalized_meal})")
        
        # Controlla se siamo negli spuntini
        is_snack = normalized_meal in ["spuntino_mattutino", "spuntino_pomeridiano", "spuntino_serale", "spuntino_notte"]
        if is_snack:
            logger.info(f"🥪 Applicando regole speciali per spuntino: {meal_name} (normalizzato: {normalized_meal})")
        
    except ImportError:
        # Fallback se non riesce a importare
        logger.warning("Non riesco a importare normalize_meal_name, uso fallback")
        is_breakfast = "colazione" in meal_name.lower() or "breakfast" in meal_name.lower()
        if is_breakfast:
            logger.info(f"🍳 Applicando regole speciali per colazione (fallback): {meal_name}")
        
        is_snack = ("spuntino" in meal_name.lower() or 
                   "snack" in meal_name.lower() or 
                   "merenda" in meal_name.lower())
        if is_snack:
            logger.info(f"🥪 Applicando regole speciali per spuntino (fallback): {meal_name}")
    
    alternative_meal = {
        "nome_pasto": meal_name,
        "alimenti": [],
        "totali_pasto": original_meal.get("totali_pasto", {})
    }
    
    # Lista degli alimenti sostituiti per l'ottimizzazione
    substitute_food_names = []
    
    # Prima fase: trova tutti i sostituti
    for alimento in original_meal["alimenti"]:
        nome_alimento = alimento["nome_alimento"]
        
        # Mappa il nome al formato database
        db_food_name = map_food_name_to_db_format(nome_alimento)
        
        # Controlla se l'alimento deve essere sostituito
        if not should_substitute_food(db_food_name):
            # Alimento protetto: mantieni invariato
            logger.info(f"🔒 Alimento protetto mantenuto: {nome_alimento}")
            alternative_meal["alimenti"].append(alimento.copy())
            substitute_food_names.append(db_food_name)
            continue
        
        # Ottieni sostituti solo se l'alimento può essere sostituito        
        if is_breakfast:
            substitutes = get_breakfast_substitute(db_food_name, substitutes_db)
        elif is_snack:
            substitutes = get_snack_substitute(db_food_name, substitutes_db)
        else:
            single_substitute = get_food_substitute(db_food_name, substitutes_db)
            substitutes = [single_substitute] if single_substitute else None
        
        if substitutes:
            # Crea nuovi alimenti per ogni sostituto
            for substitute in substitutes:
                new_alimento = {
                    "nome_alimento": substitute.replace("_", " ").title(),
                    "quantita_g": 0,  # Sarà calcolata dall'ottimizzatore
                    "stato": alimento.get("stato", "non specificato"),
                    "metodo_cottura": alimento.get("metodo_cottura", "non specificato"), 
                    "misura_casalinga": "ottimizzata",
                    "macronutrienti": {
                        "proteine": 0,
                        "carboidrati": 0,
                        "grassi": 0,
                        "kcal": 0
                    }
                }
                alternative_meal["alimenti"].append(new_alimento)
                substitute_food_names.append(substitute)
        else:
            # Se non ci sono sostituti, mantieni l'alimento originale
            logger.warning(f"Mantiene alimento originale: {nome_alimento} (nessun sostituto trovato)")
            alternative_meal["alimenti"].append(alimento.copy())
            substitute_food_names.append(db_food_name)
    
    # Seconda fase: ottimizza le porzioni usando optimize_meal_portions
    logger.info(f"🔄 Ottimizzazione porzioni per {meal_name}...")
    
    try:
        # Importa qui per evitare problemi di import circolari
        from agent_tools.meal_optimization_tool import optimize_meal_portions
        
        # Ottimizza le porzioni
        optimization_result = optimize_meal_portions(meal_name, substitute_food_names)
        
        if optimization_result.get("success", False):
            # Aggiorna il pasto alternativo con i risultati ottimizzati
            optimized_portions = optimization_result["portions"]
            macro_contributions = optimization_result.get("macro_single_foods", {})
            
            # Aggiorna le quantità e i macronutrienti
            for alimento in alternative_meal["alimenti"]:
                food_key = map_food_name_to_db_format(alimento["nome_alimento"])
                
                if food_key in optimized_portions:
                    alimento["quantita_g"] = optimized_portions[food_key]
                    
                    if food_key in macro_contributions:
                        contribution = macro_contributions[food_key]
                        alimento["macronutrienti"] = {
                            "proteine": contribution["proteine_g"],
                            "carboidrati": contribution["carboidrati_g"], 
                            "grassi": contribution["grassi_g"],
                            "kcal": contribution["kcal"]
                        }
            
            # Aggiorna i totali del pasto
            alternative_meal["totali_pasto"] = {
                "kcal_finali": optimization_result["actual_nutrients"]["kcal"],
                "proteine_totali": optimization_result["actual_nutrients"]["proteine_g"],
                "carboidrati_totali": optimization_result["actual_nutrients"]["carboidrati_g"],
                "grassi_totali": optimization_result["actual_nutrients"]["grassi_g"]
            }
            
            # Aggiungi informazioni sull'ottimizzazione
            alternative_meal["optimization_info"] = {
                "success": True,
                "target_nutrients": optimization_result["target_nutrients"],
                "errors": optimization_result.get("errors", {}),
                "optimization_summary": optimization_result.get("optimization_summary", ""),
                "foods_included": optimization_result.get("foods_included", substitute_food_names)
            }
            
            logger.info(f"✅ {meal_name} ottimizzato con successo")
            
        else:
            # Ottimizzazione fallita, mantieni il pasto alternativo base con quantità originali
            logger.warning(f"⚠️ Ottimizzazione fallita per {meal_name}: {optimization_result.get('error_message', 'Errore sconosciuto')}")
            
            # Ripristina le quantità originali
            for i, alimento in enumerate(alternative_meal["alimenti"]):
                if i < len(original_meal["alimenti"]):
                    alimento["quantita_g"] = original_meal["alimenti"][i]["quantita_g"]
            
            alternative_meal["optimization_info"] = {
                "success": False,
                "error_message": optimization_result.get("error_message", "Errore sconosciuto")
            }
            
    except Exception as e:
        logger.error(f"❌ Errore nell'ottimizzazione di {meal_name}: {str(e)}")
        
        # In caso di errore, ripristina le quantità originali
        for i, alimento in enumerate(alternative_meal["alimenti"]):
            if i < len(original_meal["alimenti"]):
                alimento["quantita_g"] = original_meal["alimenti"][i]["quantita_g"]
        
        alternative_meal["optimization_info"] = {
            "success": False,
            "error_message": f"Errore nell'ottimizzazione: {str(e)}"
        }
    
    return alternative_meal

def generate_alternative_diet(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Genera una dieta alternativa basata sui pasti registrati dell'utente
    
    Returns:
        Dizionario con la nuova dieta generata
    """
    try:
        # Carica i dati necessari
        logger.info("🔄 Caricamento dati utente e database sostituti...")
        user_data = load_user_data(user_id)
        substitutes_db = load_substitutes_database()
        
        # Estrai i pasti registrati dalla struttura corretta
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        weekly_diet_day_1 = nutritional_info.get("weekly_diet_day_1", [])
        
        # Debug: verifica le chiavi presenti
        logger.info(f"🔍 Chiavi principali nel file utente: {list(user_data.keys())}")
        logger.info(f"🔍 Chiavi in nutritional_info_extracted: {list(nutritional_info.keys()) if nutritional_info else 'None'}")
        logger.info(f"🔍 Numero di pasti registrati trovati: {len(weekly_diet_day_1)}")
        
        if not weekly_diet_day_1:
            raise ValueError("Nessun pasto registrato trovato per l'utente")
        
        logger.info(f"📊 Trovati {len(weekly_diet_day_1)} pasti registrati")
        
        alternative_diet = {
            "metadata": {
                "description": "Dieta alternativa generata automaticamente con sostituti alimentari",
                "generation_method": "Sostituzione randomica pesata + ottimizzazione porzioni",
                "original_meals_count": len(weekly_diet_day_1),
                "substitution_source": "Database sostituti logici"
            },
            "alternative_meals": []
        }
        
        successful_optimizations = 0
        
        # Processa ogni pasto
        for i, meal in enumerate(weekly_diet_day_1):
            meal_name = meal.get("nome_pasto", f"Pasto_{i+1}")
            
            # Salta pasti vuoti (con quantità 0)
            if not meal.get("alimenti") or all(alimento.get("quantita_g", 0) == 0 for alimento in meal["alimenti"]):
                logger.info(f"⏭️ Saltato {meal_name} (pasto vuoto)")
                continue
            
            logger.info(f"🔄 Elaborazione {meal_name}...")
            
            try:
                # Crea pasto alternativo con sostituti e ottimizzazione integrata
                alternative_meal = create_alternative_meal(meal, substitutes_db)
                
                # Conta le ottimizzazioni riuscite
                if alternative_meal.get("optimization_info", {}).get("success", False):
                    successful_optimizations += 1
                
                alternative_diet["alternative_meals"].append(alternative_meal)
                
            except Exception as e:
                logger.error(f"❌ Errore nell'elaborazione di {meal_name}: {str(e)}")
                continue
        
        # Aggiungi statistiche finali
        alternative_diet["metadata"]["successful_optimizations"] = successful_optimizations
        alternative_diet["metadata"]["total_alternative_meals"] = len(alternative_diet["alternative_meals"])
        
        logger.info(f"✅ Dieta alternativa generata con successo!")
        logger.info(f"📊 Pasti alternativi creati: {len(alternative_diet['alternative_meals'])}")
        logger.info(f"📊 Ottimizzazioni riuscite: {successful_optimizations}")
        
        return alternative_diet
        
    except Exception as e:
        logger.error(f"❌ Errore nella generazione della dieta alternativa: {str(e)}")
        return {
            "error": True,
            "error_message": str(e),
            "alternative_meals": []
        }

def generate_week_diet(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Genera una settimana completa di diete alternative (Giorni 2-7) con pattern alternati
    
    Utilizza generate_alternative_diet per creare 6 giorni aggiuntivi di dieta,
    numerati dal Giorno 2 al Giorno 7. Il Giorno 1 è considerato quello già presente nel sistema.
    
    Pattern di alternanza:
    - Pattern A (Giorni 1, 3, 5, 7): Stessa colazione e spuntini
    - Pattern B (Giorni 2, 4, 6): Stessa colazione e spuntini (diversa dal Pattern A)
    
    Args:
        user_id: ID dell'utente (opzionale, usa fallback se non specificato)
        
    Returns:
        Dizionario con la settimana di diete alternative strutturata per giorni
        
    Raises:
        Exception: Se ci sono errori nella generazione delle diete
    """
    logger.info("🗓️ Inizio generazione settimana diete alternative con pattern alternati (Giorni 2-7)")
    
    # Configurazione settimana con pattern alternati
    WEEK_CONFIG = {
        "base_day": 1,  # Il giorno base già presente nel sistema
        "days_to_generate": [2, 3, 4, 5, 6, 7],  # Giorni da generare
        "total_days": 7,
        "pattern_a_days": [1, 3, 5, 7],  # Pattern A: Giorno base + giorni dispari
        "pattern_b_days": [2, 4, 6],     # Pattern B: Giorni pari
        "pasti_da_mantenere": ["colazione", "spuntino_mattutino", "spuntino_pomeridiano"]
    }
    
    # Struttura risultato
    weekly_diet_days_2_7 = {
        "metadata": {
            "description": "Settimana completa di diete alternative con pattern alternati",
            "generation_method": "Pattern alternati: A(1,3,5,7) B(2,4,6) per colazione/spuntini + ottimizzazione porzioni",
            "base_day": WEEK_CONFIG["base_day"],
            "generated_days": WEEK_CONFIG["days_to_generate"],
            "total_days": WEEK_CONFIG["total_days"],
            "pattern_a_days": WEEK_CONFIG["pattern_a_days"],
            "pattern_b_days": WEEK_CONFIG["pattern_b_days"],
            "generation_timestamp": None,
            "successful_days": 0,
            "failed_days": [],
            "user_id": user_id or get_user_id()
        },
        "weekly_diet_days_2_7": {},
        "meal_patterns": {
            "pattern_a": None,  # Pattern per giorni 1,3,5,7
            "pattern_b": None   # Pattern per giorni 2,4,6
        }
    }
    
    successful_generations = 0
    failed_generations = []
    
    try:
        # Ottieni timestamp di generazione
        from datetime import datetime
        weekly_diet_days_2_7["metadata"]["generation_timestamp"] = datetime.now().isoformat()
        
        logger.info(f"📊 Configurazione settimana con pattern alternati:")
        logger.info(f"   - Giorno base (esistente): {WEEK_CONFIG['base_day']}")
        logger.info(f"   - Pattern A (1,3,5,7): {WEEK_CONFIG['pattern_a_days']}")
        logger.info(f"   - Pattern B (2,4,6): {WEEK_CONFIG['pattern_b_days']}")
        logger.info(f"   - Pasti con pattern: {WEEK_CONFIG['pasti_da_mantenere']}")
        
        # FASE 1: Estrai Pattern A dal Giorno 1 (già presente nel sistema)
        logger.info("🔍 Estrazione Pattern A dal Giorno 1...")
        pattern_a = _extract_pattern_from_day1(user_id, WEEK_CONFIG["pasti_da_mantenere"])
        weekly_diet_days_2_7["meal_patterns"]["pattern_a"] = pattern_a
        
        if pattern_a:
            logger.info(f"✅ Pattern A estratto: {len(pattern_a)} pasti trovati")
            for meal_name in pattern_a.keys():
                logger.info(f"   - {meal_name}: {len(pattern_a[meal_name]['alimenti'])} alimenti")
        else:
            logger.warning("⚠️ Nessun Pattern A estratto, userò generazione standard")
        
        # FASE 2: Genera Pattern B (diverso dal Pattern A)
        logger.info("🔄 Generazione Pattern B...")
        pattern_b = _generate_pattern_b(user_id, WEEK_CONFIG["pasti_da_mantenere"])
        weekly_diet_days_2_7["meal_patterns"]["pattern_b"] = pattern_b
        
        if pattern_b:
            logger.info(f"✅ Pattern B generato: {len(pattern_b)} pasti")
            for meal_name in pattern_b.keys():
                logger.info(f"   - {meal_name}: {len(pattern_b[meal_name]['alimenti'])} alimenti")
        else:
            logger.warning("⚠️ Errore nella generazione Pattern B, userò generazione standard")
        
        # FASE 3: Genera ogni giorno della settimana applicando i pattern
        for day_number in WEEK_CONFIG["days_to_generate"]:
            day_key = f"day_{day_number}"
            
            logger.info(f"🔄 Generazione Giorno {day_number}...")
            
            try:
                # Determina quale pattern usare
                if day_number in WEEK_CONFIG["pattern_a_days"]:
                    current_pattern = pattern_a
                    pattern_name = "A"
                elif day_number in WEEK_CONFIG["pattern_b_days"]:
                    current_pattern = pattern_b
                    pattern_name = "B"
                else:
                    current_pattern = None
                    pattern_name = "Standard"
                
                logger.info(f"   📋 Usando Pattern {pattern_name} per Giorno {day_number}")
                
                # Genera dieta alternativa per questo giorno
                day_diet = generate_alternative_diet(user_id)
                
                # Controlla se la generazione è riuscita
                if day_diet.get("error"):
                    logger.error(f"❌ Errore nella generazione del Giorno {day_number}: {day_diet.get('error_message')}")
                    failed_generations.append({
                        "day": day_number,
                        "error": day_diet.get("error_message", "Errore sconosciuto")
                    })
                    continue
                
                # FASE 4: Applica il pattern appropriato
                if current_pattern:
                    day_diet = _apply_meal_pattern(day_diet, current_pattern, WEEK_CONFIG["pasti_da_mantenere"])
                    logger.info(f"   ✅ Pattern {pattern_name} applicato al Giorno {day_number}")
                
                # Aggiungi metadati specifici del giorno
                day_diet["day_metadata"] = {
                    "day_number": day_number,
                    "day_type": _get_day_type(day_number),
                    "pattern_used": pattern_name,
                    "generation_order": len(weekly_diet_days_2_7["weekly_diet_days_2_7"]) + 1,
                    "meals_count": len(day_diet.get("alternative_meals", [])),
                    "successful_optimizations": day_diet.get("metadata", {}).get("successful_optimizations", 0)
                }
                
                # Salva il giorno nella struttura settimanale
                weekly_diet_days_2_7["weekly_diet_days_2_7"][day_key] = day_diet
                successful_generations += 1
                
                logger.info(f"✅ Giorno {day_number} generato con successo:")
                logger.info(f"   - Pattern: {pattern_name}")
                logger.info(f"   - Pasti alternativi: {day_diet['day_metadata']['meals_count']}")
                logger.info(f"   - Ottimizzazioni riuscite: {day_diet['day_metadata']['successful_optimizations']}")
                
            except Exception as e:
                logger.error(f"❌ Errore imprevisto nella generazione del Giorno {day_number}: {str(e)}")
                failed_generations.append({
                    "day": day_number,
                    "error": f"Errore imprevisto: {str(e)}"
                })
                continue
        
        # Aggiorna metadati finali
        weekly_diet_days_2_7["metadata"]["successful_days"] = successful_generations
        weekly_diet_days_2_7["metadata"]["failed_days"] = failed_generations
        
        # Log risultati finali
        logger.info(f"🎯 Generazione settimana completata:")
        logger.info(f"   - Giorni generati con successo: {successful_generations}/6")
        logger.info(f"   - Giorni falliti: {len(failed_generations)}")
        
        if failed_generations:
            logger.warning(f"⚠️ Giorni con errori: {[f['day'] for f in failed_generations]}")
            for failure in failed_generations:
                logger.warning(f"   - Giorno {failure['day']}: {failure['error']}")
        
        if successful_generations == 0:
            raise Exception("Nessun giorno è stato generato con successo")
        
        logger.info(f"✅ Settimana diete alternative generata con successo!")
        
        return weekly_diet_days_2_7
        
    except Exception as e:
        logger.error(f"❌ Errore critico nella generazione della settimana: {str(e)}")
        
        # Struttura di errore
        error_result = {
            "error": True,
            "error_message": str(e),
            "metadata": weekly_diet_days_2_7["metadata"],
            "weekly_diet_days_2_7": weekly_diet_days_2_7["weekly_diet_days_2_7"]  # Mantieni eventuali giorni già generati
        }
        
        return error_result

def _extract_pattern_from_day1(user_id: Optional[str], pasti_da_mantenere: List[str]) -> Optional[Dict[str, Any]]:
    """
    Estrae il pattern di colazione e spuntini dal Giorno 1 (già presente nel sistema)
    
    Args:
        user_id: ID dell'utente
        pasti_da_mantenere: Lista dei nomi dei pasti da estrarre
        
    Returns:
        Dizionario con i pasti del Pattern A o None se errore
    """
    try:
        # Carica i dati dell'utente
        user_data = load_user_data(user_id)
        
        # Estrai i pasti registrati
        nutritional_info = user_data.get("nutritional_info_extracted", {})
        weekly_diet_day_1 = nutritional_info.get("weekly_diet_day_1", [])
        
        if not weekly_diet_day_1:
            logger.warning("Nessun pasto registrato trovato per estrarre Pattern A")
            return None
        
        # Estrai i pasti che corrispondono ai nomi richiesti
        pattern_a = {}
        
        for meal in weekly_diet_day_1:
            meal_name = meal.get("nome_pasto", "").lower()
            
            # Normalizza il nome del pasto per confronto
            try:
                from agent_tools.meal_optimization_tool import normalize_meal_name
                normalized_meal = normalize_meal_name(meal_name)
            except ImportError:
                normalized_meal = meal_name.replace(" ", "_").lower()
            
            # Se è uno dei pasti che ci interessano, aggiungilo al pattern
            if normalized_meal in pasti_da_mantenere:
                # Salta pasti vuoti
                if not meal.get("alimenti") or all(alimento.get("quantita_g", 0) == 0 for alimento in meal["alimenti"]):
                    continue
                    
                pattern_a[normalized_meal] = meal.copy()
                logger.info(f"   📋 Estratto per Pattern A: {normalized_meal} ({len(meal['alimenti'])} alimenti)")
        
        if pattern_a:
            logger.info(f"✅ Pattern A estratto con {len(pattern_a)} pasti")
            return pattern_a
        else:
            logger.warning("⚠️ Nessun pasto valido trovato per Pattern A")
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore nell'estrazione Pattern A: {str(e)}")
        return None


def _generate_pattern_b(user_id: Optional[str], pasti_da_mantenere: List[str]) -> Optional[Dict[str, Any]]:
    """
    Genera il Pattern B per colazione e spuntini (diverso dal Pattern A)
    
    Args:
        user_id: ID dell'utente
        pasti_da_mantenere: Lista dei nomi dei pasti da generare
        
    Returns:
        Dizionario con i pasti del Pattern B o None se errore
    """
    try:
        # Genera una dieta alternativa temporanea
        temp_diet = generate_alternative_diet(user_id)
        
        if temp_diet.get("error"):
            logger.error(f"Errore nella generazione dieta temporanea per Pattern B: {temp_diet.get('error_message')}")
            return None
        
        # Estrai solo i pasti di interesse
        pattern_b = {}
        
        for meal in temp_diet.get("alternative_meals", []):
            meal_name = meal.get("nome_pasto", "").lower()
            
            # Normalizza il nome del pasto
            try:
                from agent_tools.meal_optimization_tool import normalize_meal_name
                normalized_meal = normalize_meal_name(meal_name)
            except ImportError:
                normalized_meal = meal_name.replace(" ", "_").lower()
            
            # Se è uno dei pasti che ci interessano, aggiungilo al pattern
            if normalized_meal in pasti_da_mantenere:
                pattern_b[normalized_meal] = meal.copy()
                logger.info(f"   📋 Generato per Pattern B: {normalized_meal} ({len(meal['alimenti'])} alimenti)")
        
        if pattern_b:
            logger.info(f"✅ Pattern B generato con {len(pattern_b)} pasti")
            return pattern_b
        else:
            logger.warning("⚠️ Nessun pasto valido generato per Pattern B")
            return None
            
    except Exception as e:
        logger.error(f"❌ Errore nella generazione Pattern B: {str(e)}")
        return None


def _apply_meal_pattern(day_diet: Dict[str, Any], pattern: Dict[str, Any], target_meals: List[str]) -> Dict[str, Any]:
    """
    Applica un pattern di pasti a una dieta giornaliera
    
    Args:
        day_diet: Dieta del giorno da modificare
        pattern: Pattern di pasti da applicare  
        target_meals: Lista dei nomi dei pasti da sostituire
        
    Returns:
        Dieta modificata con il pattern applicato
    """
    try:
        # Crea una nuova lista di pasti
        new_meals = []
        pattern_applied_meals = set()
        
        # Prima passa: sostituisci i pasti che matchano il pattern
        for meal in day_diet.get("alternative_meals", []):
            meal_name = meal.get("nome_pasto", "").lower()
            
            # Normalizza il nome del pasto
            try:
                from agent_tools.meal_optimization_tool import normalize_meal_name
                normalized_meal = normalize_meal_name(meal_name)
            except ImportError:
                normalized_meal = meal_name.replace(" ", "_").lower()
            
            # Se è un pasto che deve seguire il pattern, sostituiscilo
            if normalized_meal in target_meals and normalized_meal in pattern:
                new_meals.append(pattern[normalized_meal].copy())
                pattern_applied_meals.add(normalized_meal)
                logger.info(f"   🔄 Pattern applicato a: {normalized_meal}")
            else:
                # Mantieni il pasto originale
                new_meals.append(meal)
        
        # Seconda passa: aggiungi eventuali pasti del pattern non ancora applicati
        for pattern_meal_name, pattern_meal_data in pattern.items():
            if pattern_meal_name not in pattern_applied_meals:
                new_meals.append(pattern_meal_data.copy())
                logger.info(f"   ➕ Aggiunto pasto pattern: {pattern_meal_name}")
        
        # Aggiorna la dieta
        day_diet["alternative_meals"] = new_meals
        
        # Aggiungi informazioni sul pattern applicato
        day_diet["pattern_info"] = {
            "pattern_applied": True,
            "meals_replaced": list(pattern_applied_meals),
            "total_pattern_meals": len(pattern)
        }
        
        return day_diet
        
    except Exception as e:
        logger.error(f"❌ Errore nell'applicazione del pattern: {str(e)}")
        # In caso di errore, restituisci la dieta originale
        return day_diet


def _get_day_type(day_number: int) -> str:
    """
    Determina il tipo di giorno per categorizzazione futura
    
    Args:
        day_number: Numero del giorno (1-7)
        
    Returns:
        Tipo di giorno per elaborazioni successive
    """
    # Mapping per futuri ragionamenti ad hoc
    day_types = {
        1: "base_day",      # Giorno base (già presente)
        2: "variation_1",   # Prima variazione
        3: "variation_2",   # Seconda variazione  
        4: "mid_week",      # Metà settimana
        5: "variation_3",   # Terza variazione
        6: "weekend_prep",  # Preparazione weekend
        7: "weekend_day"    # Giorno weekend
    }
    
    return day_types.get(day_number, "unknown")
