"""
Tool per l'ottimizzazione delle porzioni di un pasto.

Questo tool calcola le porzioni ottimali di alimenti specificati
per un pasto in modo da rispettare i target nutrizionali del pasto.
"""

import os
import json
from typing import Dict, List, Any, Tuple, Optional
import logging
from scipy.optimize import minimize
import numpy as np

from .nutridb import NutriDB
from .nutridb_tool import get_user_id

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Inizializza il database
try:
    db = NutriDB("Dati_processed")
except Exception as e:
    logger.error(f"Errore nell'inizializzazione del database: {str(e)}")
    raise


# get_user_id è ora importato da nutridb_tool


def load_user_meal_targets(user_id: str, meal_name: str) -> Dict[str, float]:
    """
    Carica i target nutrizionali per un pasto specifico dal file utente.
    
    Args:
        user_id: ID dell'utente
        meal_name: Nome del pasto (es: 'Colazione', 'Pranzo', etc.)
        
    Returns:
        Dict con target di kcal, proteine_g, carboidrati_g, grassi_g
        
    Raises:
        ValueError: Se i dati non sono disponibili
    """
    # Fix: Handle user_id that may already contain 'user_' prefix
    if user_id.startswith("user_"):
        user_file_path = f"user_data/{user_id}.json"
    else:
        user_file_path = f"user_data/user_{user_id}.json"
    

    
    if not os.path.exists(user_file_path):
        raise ValueError(f"File utente {user_id} non trovato.")
    
    with open(user_file_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    nutritional_info = user_data.get("nutritional_info_extracted", {})
    daily_macros = nutritional_info.get("daily_macros", {})
    distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
    

    
    # Crea un mapping robusto per i nomi dei pasti
    def normalize_meal_name(name):
        """Normalizza un nome di pasto per il confronto"""
        return name.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Mapping completo con tutte le varianti possibili
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
    

    
    # Cerca il pasto nei dati utente
    meal_data = None
    
    # Prova prima con il nome canonico trovato
    if canonical_meal_name and canonical_meal_name in distribuzione_pasti:
        meal_data = distribuzione_pasti[canonical_meal_name]
    
    # Se non trovato, prova con tutte le chiavi disponibili confrontando i nomi normalizzati
    if not meal_data:
        for available_meal_key in distribuzione_pasti.keys():
            normalized_available = normalize_meal_name(available_meal_key)
            
            # Confronto diretto
            if normalized_available == normalized_input:
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                break
            
            # Confronto parziale (se il nome input è contenuto nella chiave disponibile o viceversa)
            if (normalized_input in normalized_available or 
                normalized_available in normalized_input or
                # Confronto parole chiave
                any(word in normalized_available for word in normalized_input.split("_"))):
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                break
    
    # Se ancora non trovato, restituisci errore con informazioni utili
    if not meal_data:
        available_meals = list(distribuzione_pasti.keys())
        available_meals_formatted = [meal.replace("_", " ").title() for meal in available_meals]
        
        error_msg = (
            f"Pasto '{meal_name}' non trovato. "
            f"Pasti disponibili: {', '.join(available_meals_formatted)}. "
            f"Prova con nomi come: 'Colazione', 'Spuntino Mattutino', 'Pranzo', "
            f"'Spuntino Pomeridiano', 'Cena', 'Merenda', ecc."
        )
        print(f"   ❌ ERRORE: {error_msg}")
        raise ValueError(error_msg)
    
    result = {
        "kcal": float(meal_data.get("kcal") or 0),
        "proteine_g": float(meal_data.get("proteine_g") or 0),
        "carboidrati_g": float(meal_data.get("carboidrati_g") or 0),
        "grassi_g": float(meal_data.get("grassi_g") or 0)
    }
    
    return result


def get_food_nutrition_per_100g(food_list: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Estrae i dati nutrizionali per 100g di ogni alimento dalla banca alimenti.
    
    Args:
        food_list: Lista dei nomi degli alimenti
        
    Returns:
        Dict con i dati nutrizionali per 100g di ogni alimento
        
    Raises:
        ValueError: Se alcuni alimenti non sono trovati
    """
    foods_nutrition = {}
    foods_not_found = []
    
    for food in food_list:
        # Normalizza il nome dell'alimento usando la stessa logica del database
        normalized_food = food.lower().replace("_", " ")
        
        # Controlla se l'alimento è presente negli alias
        if normalized_food in db.alias:
            # Ottieni la chiave canonica dell'alimento
            canonical_key = db.alias[normalized_food]
            
            try:
                # Ottieni i macronutrienti per 100g usando la chiave canonica
                macros = db.get_macros(food, 100)
                
                # Converte esplicitamente a float per evitare errori di tipo, gestendo anche valori None
                foods_nutrition[food] = {
                    "energia_kcal": float(macros.get("energia_kcal") or 0),
                    "proteine_g": float(macros.get("proteine_g") or 0),
                    "carboidrati_g": float(macros.get("carboidrati_g") or 0),
                    "grassi_g": float(macros.get("grassi_g") or 0),
                    "categoria": macros.get("categoria", "alimento_misto")
                }
            except (ValueError, TypeError) as e:
                logger.error(f"Errore conversione dati per {food}: {str(e)}")
                foods_not_found.append(food)
        else:
            foods_not_found.append(food)
    
    if foods_not_found:
        raise ValueError(f"Alimenti non trovati nel database: {', '.join(foods_not_found)}")
    
    return foods_nutrition


def get_portion_constraints():
    """
    Restituisce i vincoli di porzione per categoria di alimento.
    
    Returns:
        Dict con min e max per ogni categoria (rimosso preferred per maggiore flessibilità)
    """
    return {
        # CATEGORIE PRINCIPALI DALLA BANCA ALIMENTI
        "caffè": {"min": 5, "max": 5},
        "zucchero": {"min": 5, "max": 10},
        "proteine_animali": {"min": 70, "max": 300},
        "latte": {"min": 100, "max": 500},
        "affettati": {"min": 50, "max": 150},
        "formaggi": {"min": 30, "max": 300},
        "latticini": {"min": 100, "max": 300},  # Per yogurt e altri latticini
        "cereali": {"min": 60, "max": 170},
        "cereali_colazione": {"min": 20, "max": 60},
        "tuberi": {"min": 100, "max": 500},  # Aumentato max per patate
        "legumi": {"min": 100, "max": 400},
        "verdure": {"min": 100, "max": 400},
        "insalata": {"min": 50, "max": 150},
        "frutta": {"min": 80, "max": 300},
        "frutta_secca": {"min": 5, "max": 40},
        "grassi_aggiunti": {"min": 5, "max": 120},
        "creme_spalmabili": {"min": 10, "max": 40},
        "creme_spalmabili_light": {"min": 10, "max": 30},
        "uova": {"min": 60, "max": 200},  # ~1-2 uova
        "dolci": {"min": 10, "max": 80},   # Porzioni piccole per dolci
        "integratori": {"min": 10, "max": 50},  # Maggiore flessibilità per integratori        
        # CATEGORIA FALLBACK
        "alimento_misto": {"min": 10, "max": 200}
    }


def optimize_portions(target_nutrients: Dict[str, float], 
                     foods_nutrition: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Ottimizza le porzioni degli alimenti per raggiungere i target nutrizionali.
    
    Args:
        target_nutrients: Target di kcal, proteine_g, carboidrati_g, grassi_g
        foods_nutrition: Dati nutrizionali per 100g di ogni alimento
        
    Returns:
        Dict con le porzioni ottimizzate in grammi per ogni alimento
    """
    food_names = list(foods_nutrition.keys())
    n_foods = len(food_names)
    constraints = get_portion_constraints()
    
    # Estrai i bounds per ogni alimento basati sulla categoria
    bounds = []
    initial_values = []
    
    for food in food_names:
        categoria = foods_nutrition[food]["categoria"]
        constraint = constraints.get(categoria, constraints["alimento_misto"])
        
        bounds.append((constraint["min"], constraint["max"]))
        # Usa il punto medio tra min e max come valore iniziale
        initial_values.append((constraint["min"] + constraint["max"]) / 2)
    
    # Funzione obiettivo: minimizza la differenza dai target nutrizionali
    def objective(portions):
        total_kcal = sum(foods_nutrition[food]["energia_kcal"] * portions[i] / 100 
                        for i, food in enumerate(food_names))
        total_proteine = sum(foods_nutrition[food]["proteine_g"] * portions[i] / 100 
                           for i, food in enumerate(food_names))
        total_carboidrati = sum(foods_nutrition[food]["carboidrati_g"] * portions[i] / 100 
                              for i, food in enumerate(food_names))
        total_grassi = sum(foods_nutrition[food]["grassi_g"] * portions[i] / 100 
                         for i, food in enumerate(food_names))
        
        # Calcola gli errori relativi rispetto ai target
        kcal_error = abs(total_kcal - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1)
        proteine_error = abs(total_proteine - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1)
        carboidrati_error = abs(total_carboidrati - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1)
        grassi_error = abs(total_grassi - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
        
        # Errore totale pesato (calorie hanno peso maggiore)
        total_error = (3 * kcal_error + 2 * proteine_error + carboidrati_error + grassi_error)
        
        return total_error
    
    # Punto di partenza: punto medio tra min e max
    initial_guess = np.array(initial_values)
    
    # Ottimizzazione
    try:
        result = minimize(
            objective,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000}
        )
        
        if result.success:
            optimized_portions = result.x
            logger.info("Ottimizzazione convergente completata")
        else:
            # Anche se non converge, confronta il risultato parziale con i valori iniziali
            if hasattr(result, 'x') and result.x is not None:
                # Calcola l'errore per il risultato parziale dell'ottimizzatore
                partial_error = objective(result.x)
                # Calcola l'errore per i valori iniziali
                initial_error = objective(initial_guess)
                
                if partial_error < initial_error:
                    # Il risultato parziale è migliore dei valori iniziali
                    optimized_portions = result.x
                    logger.warning(f"Ottimizzazione non convergente, ma uso miglior risultato parziale (errore: {partial_error:.3f} vs iniziale: {initial_error:.3f})")
                else:
                    # I valori iniziali sono migliori
                    optimized_portions = initial_guess
                    logger.warning(f"Ottimizzazione non convergente, uso valori iniziali (errore iniziale: {initial_error:.3f} vs parziale: {partial_error:.3f})")
            else:
                # Fallback ai valori iniziali se non c'è result.x
                optimized_portions = initial_guess
                logger.warning("Ottimizzazione non convergente senza risultato parziale, uso valori iniziali")
    except Exception as e:
        logger.error(f"Errore nell'ottimizzazione: {str(e)}")
        optimized_portions = initial_guess
    
    # Costruisci il risultato con conversione esplicita a tipi Python nativi
    portions_result = {}
    for i, food in enumerate(food_names):
        # Converte esplicitamente a float Python nativo per evitare errori di serializzazione JSON
        portions_result[food] = float(round(optimized_portions[i], 1))
    
    return portions_result


def calculate_actual_nutrients(portions: Dict[str, float], 
                             foods_nutrition: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Calcola i valori nutrizionali effettivi dalle porzioni ottimizzate.
    
    Args:
        portions: Porzioni in grammi per ogni alimento
        foods_nutrition: Dati nutrizionali per 100g di ogni alimento
        
    Returns:
        Dict con i valori nutrizionali totali
    """
    total_kcal = sum(foods_nutrition[food]["energia_kcal"] * grams / 100 
                    for food, grams in portions.items())
    total_proteine = sum(foods_nutrition[food]["proteine_g"] * grams / 100 
                        for food, grams in portions.items())
    total_carboidrati = sum(foods_nutrition[food]["carboidrati_g"] * grams / 100 
                           for food, grams in portions.items())
    total_grassi = sum(foods_nutrition[food]["grassi_g"] * grams / 100 
                      for food, grams in portions.items())
    
    # Converte esplicitamente a float Python nativi per evitare errori di serializzazione JSON
    return {
        "kcal": float(round(total_kcal, 1)),
        "proteine_g": float(round(total_proteine, 1)),
        "carboidrati_g": float(round(total_carboidrati, 1)),
        "grassi_g": float(round(total_grassi, 1))
    }


def get_category_mappings():
    """
    Definisce i mappings delle categorie alimentari.
    Se l'utente esclude un elemento di una categoria, vengono esclusi tutti.
    
    Returns:
        Dict: Mappature categoria -> lista alimenti da escludere
    """
    return {
        # === LATTICINI E DERIVATI ===
        "latte": ["latte_intero", "latte_parzialmente_scremato", "latte_scremato"],
        "yogurt": ["yogurt_magro", "yogurt_greco_0percento", "yogurt_greco_2percento"],
        "latticini": ["latte_intero", "latte_parzialmente_scremato", "latte_scremato", 
                     "yogurt_magro", "yogurt_greco_0percento", "yogurt_greco_2percento","asiago", "grana_padano", "mozzarella", "parmigiano_reggiano", "pecorino", "ricotta", "mozzarella", "pro_milk_20g_proteine"],
        
        # === FORMAGGI ===
        "formaggio": ["asiago", "grana_padano", "mozzarella", "parmigiano_reggiano", "pecorino", "ricotta", "mozzarella"],
        "formaggi": ["asiago", "grana_padano", "mozzarella", "parmigiano_reggiano", "pecorino", "ricotta", "mozzarella"],
        
        # === CEREALI E DERIVATI ===
        "pane": ["pane_bianco", "pane_integrale"],
        "pasta": ["pasta_di_semola", "pasta_integrale"],
        "riso": ["riso", "riso_integrale"],
        "cereali": ["pasta_di_semola", "pasta_integrale", "riso", "riso_integrale", "couscous", 
                   "pane_bianco", "pane_integrale", "quinoa", "farro", "orzo"],
        "cereali_colazione": ["biscotti_secchi", "cereali_fibra_1", "cereali_integrali", 
                             "cracker", "fette_biscottate", "pan_bauletto"],
        
        # === PROTEINE ANIMALI ===
        # Pollo (sottocategoria)
        "pollo": ["pollo_petto", "pollo_coscia", "pollo_ali"],
        
        # Pesce (sottocategoria)
        "pesce": ["tonno_naturale", "tonno_fresco", "tonno_sottolio_sgocciolato", "merluzzo", 
                 "salmone_al_naturale", "salmone_affumicato", "orata", "spigola", "pesce_spada", "gamberi", "scampi",
                 "sgombro", "sgo"],
        "tonno": ["tonno_naturale", "tonno_fresco", "tonno_sottolio_sgocciolato"],
        "salmone": ["salmone_al_naturale", "salmone_affumicato"],
        
        # Carne (sottocategoria)
        "carne": ["carne_manzo", "pollo_petto", "pollo_coscia", "pollo_ali"],
        "manzo": ["carne_manzo"],
        
        # Categoria generale proteine animali
        "proteine_animali": ["carne_manzo", "gamberi", "merluzzo", "orata", "pesce_spada", 
                           "pollo_ali", "pollo_coscia", "pollo_petto", "salmone_affumicato", 
                           "salmone_al_naturale", "spigola", "tonno_fresco", "tonno_naturale", 
                           "tonno_sottolio_sgocciolato", "wurstel"],
        "proteine": ["carne_manzo", "gamberi", "merluzzo", "orata", "pesce_spada", 
                    "pollo_ali", "pollo_coscia", "pollo_petto", "salmone_affumicato", 
                    "salmone_al_naturale", "spigola", "tonno_fresco", "tonno_naturale", 
                    "tonno_sottolio_sgocciolato", "wurstel"],
        
        # === AFFETTATI ===
        "affettati": ["bresaola", "prosciutto_cotto", "speck", "fesa di tacchino", "prosciutto_crudo"],
        "prosciutto": ["prosciutto_cotto", "prosciutto_crudo"],
        
        # === UOVA ===
        "uova": ["uova", "albume_uova"],
        "uovo": ["uova", "albume_uova"],
        
        # === VERDURE ===
        "verdura": ["verdure_miste", "zucchine", "asparagi", "bieta", "broccoli", "carote", 
                   "cavolfiore", "fagiolini", "funghi", "insalata", "melanzane", "pomodoro", 
                   "spinaci", "zucca"],
        "verdure": ["verdure_miste", "zucchine", "asparagi", "bieta", "broccoli", "carote", 
                   "cavolfiore", "fagiolini", "funghi", "insalata", "melanzane", "pomodoro", 
                   "spinaci", "zucca"],
        # Sottocategorie specifiche di verdure
        "pomodori": ["pomodoro"],
        "carote": ["carote"],
        "zucchine": ["zucchine"],
        "broccoli": ["broccoli"],
        "spinaci": ["spinaci"],
        
        # === FRUTTA ===
        "frutta": ["mela", "pere", "banana", "arancia", "kiwi", "albicocche", "ciliegie", 
                  "lamponi", "mirtilli", "uva"],
        # Sottocategorie specifiche di frutta
        "mela": ["mela"],
        "mele": ["mela"],
        "banana": ["banana"],
        "banane": ["banana"],
        "arancia": ["arancia"],
        "arance": ["arancia"],
        "uva": ["uva"],
        "kiwi": ["kiwi"],
        
        # === LEGUMI ===
        "legumi": ["ceci", "fagioli_cannellini", "lenticchie", "mais", "piselli"],
        "fagioli": ["fagioli_cannellini"],
        "ceci": ["ceci"],
        "lenticchie": ["lenticchie"],
        "piselli": ["piselli"],
        
        # === FRUTTA SECCA ===
        "frutta_secca": ["anacardi", "arachidi", "mandorle", "nocciole", "noci_sgusciate"],
        "noci": ["noci_sgusciate"],
        "mandorle": ["mandorle"],
        "nocciole": ["nocciole"],
        "arachidi": ["arachidi", "burro_arachidi"],
        
        # === GRASSI E CONDIMENTI ===
        "grassi_aggiunti": ["avocado", "burro", "olio_oliva", "olive_verdi"],
        "olio": ["olio_oliva"],
        "burro": ["burro"],
        "olive": ["olive_verdi"],
        
        # === DOLCI E CREME ===
        "dolci": ["biscotti_colazione", "crostata_frutta"],
        "creme_spalmabili": ["marmellata_frutta", "nutella", "nutella_light"],
        "nutella": ["nutella", "nutella_light"],
        "marmellata": ["marmellata_frutta"],
        
        # === TUBERI ===
        "patate": ["patate"],
        "tuberi": ["patate"],
        
        # === ZUCCHERO E DOLCIFICANTI ===
        "zucchero": ["zucchero"],
        
        # === INTEGRATORI ===
        "integratori": ["iso_fuji_yamamoto", "pro_milk_20g_proteine"],
        "proteine_polvere": ["iso_fuji_yamamoto", "pro_milk_20g_proteine"],
        
        # === CIOCCOLATO ===
        "cioccolato": ["cioccolato_fondente"],
    }


def expand_category_to_excluded_foods(food_name: str) -> List[str]:
    """
    Se il cibo appartiene a una categoria, restituisce tutti i cibi della categoria.
    Ogni alimento viene mappato tramite l'alias del database.
    Altrimenti restituisce una lista vuota.
    
    Args:
        food_name: Nome del cibo (normalizzato)
        
    Returns:
        Lista dei cibi da escludere per quella categoria (mappati tramite alias), o lista vuota
    """
    mappings = get_category_mappings()
    normalized_food = food_name.lower().replace("_", " ").strip()
    
    # Controlla se il nome corrisponde direttamente a una categoria
    if normalized_food in mappings:
        category_foods = mappings[normalized_food]
        mapped_foods = []
        
        # Mappa ogni alimento della categoria tramite l'alias del database
        for food in category_foods:
            # Prova prima il nome così com'è
            if food in db.alias.values():
                mapped_foods.append(food)
            else:
                # Prova a cercarlo tramite alias
                food_normalized = food.lower().replace("_", " ")
                canonical_name = db.alias.get(food_normalized)
                if canonical_name:
                    mapped_foods.append(canonical_name)
                # Se non trovato, aggiungi comunque il nome originale come fallback
                else:
                    mapped_foods.append(food)
        
        return mapped_foods
    
    return []


def find_generic_food_variants(generic_term: str) -> List[str]:
    """
    Trova tutte le varianti specifiche di un termine generico nel database.
    
    Args:
        generic_term: Termine generico (es. "yogurt", "latte", "pane")
        
    Returns:
        Lista dei nomi canonici delle varianti trovate
    """
    variants = []
    
    # Mappature esplicite per i termini generici più comuni
    explicit_mappings = {
        "yogurt": ["yogurt_magro", "yogurt_intero", "yogurt_greco_0percento", "yogurt_greco_2percento"],
        "latte": ["latte_intero", "latte_parzialmente_scremato", "latte_scremato"],
        "latticini": ["latte_intero", "latte_parzialmente_scremato", "latte_scremato", "yogurt_magro", "yogurt_intero", "yogurt_greco_0percento", "yogurt_greco_2percento"],
        "pane": ["pane_bianco", "pane_integrale"],
        "pasta": ["pasta_di_semola", "pasta_integrale"],
        "riso": ["riso", "riso_bianco", "riso_integrale"],
        "formaggio": ["formaggio_fresco", "parmigiano_reggiano", "mozzarella", "ricotta"],
        "pollo": ["pollo_petto", "pollo_coscia"],
        "pesce": ["tonno_naturale", "merluzzo", "salmone", "orata", "branzino"],
        "verdura": ["verdure_miste", "zucchine", "carote", "pomodori", "spinaci", "broccoli"],
        "verdure": ["verdure_miste", "zucchine", "carote", "pomodori", "spinaci", "broccoli"],
        "frutta": ["mela", "pera", "banana", "arancia", "kiwi", "fragole"],
        "crackers": ["cracker"],
        "biscotti": ["biscotti_secchi", "biscotti_integrali"],
    }
    
    # Controlla prima le mappature esplicite
    if generic_term in explicit_mappings:
        # Verifica che gli alimenti esistano effettivamente nel database
        for food in explicit_mappings[generic_term]:
            # Verifica che l'alimento sia nel database
            if food in db.alias.values() or db.alias.get(food.lower().replace("_", " ")):
                variants.append(food)
    
    # Se non ci sono mappature esplicite, cerca dinamicamente in tutti gli alias
    if not variants:
        for alias_name, canonical_name in db.alias.items():
            # Verifica se l'alias contiene il termine generico (come parola intera o sottostringa)
            alias_words = alias_name.lower().split()
            generic_words = generic_term.lower().split()
            
            # Metodo 1: Controlla se tutte le parole del termine generico sono presenti nell'alias
            if all(generic_word in alias_words for generic_word in generic_words):
                variants.append(canonical_name)
            # Metodo 2: Controlla se il termine generico è una sottostringa dell'alias
            elif generic_term in alias_name:
                variants.append(canonical_name)
    
    # Rimuovi duplicati mantenendo l'ordine
    variants = list(dict.fromkeys(variants))
    
    return variants


def load_user_excluded_foods(user_id: str) -> List[str]:
    """
    Carica gli alimenti esclusi dall'utente dal file JSON.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        Lista degli alimenti esclusi (normalizzati usando alias del database)
    """
    # Fix: Handle user_id that may already contain 'user_' prefix
    if user_id.startswith("user_"):
        user_file_path = f"user_data/{user_id}.json"
    else:
        user_file_path = f"user_data/user_{user_id}.json"
    
    if not os.path.exists(user_file_path):
        return []
    
    try:
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        user_preferences = user_data.get("user_preferences", {})
        excluded_foods_raw = user_preferences.get("excluded_foods", [])
        
        # Processa ogni alimento: prima controlla se è una categoria, poi processa normalmente
        excluded_foods_mapped = []
        for food in excluded_foods_raw:
            if not food or not food.strip():
                continue
                
            # Prima controlla se questo alimento appartiene a una categoria da espandere
            category_foods = expand_category_to_excluded_foods(food)
            if category_foods:
                # Se trovata una categoria, aggiungi tutti i suoi alimenti
                excluded_foods_mapped.extend(category_foods)
            
            # Processa anche come alimento singolo (flusso normale)
            # Normalizza il nome usando la stessa logica del database
            normalized_food = food.lower().replace("_", " ").strip()
            
            # Cerca il nome principale usando gli alias
            canonical_name = db.alias.get(normalized_food)
            if canonical_name:
                excluded_foods_mapped.append(canonical_name)
            else:
                # Se non trovato esatto, cerca termini generici che espandono a varianti multiple
                generic_matches = find_generic_food_variants(normalized_food)
                if generic_matches:
                    excluded_foods_mapped.extend(generic_matches)
        
        # Rimuovi duplicati mantenendo l'ordine
        excluded_foods_mapped = list(dict.fromkeys(excluded_foods_mapped))
        return excluded_foods_mapped
        
    except Exception as e:
        print(f"   ❌ Errore nel caricamento excluded foods: {str(e)}")
        return []


def filter_substitutes_by_excluded_foods(
    substitutes: Dict[str, Dict[str, Dict[str, float]]], 
    excluded_foods: List[str]
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Filtra i sostituti rimuovendo quelli che sono tra gli alimenti esclusi.
    
    Args:
        substitutes: Dizionario dei sostituti da filtrare
        excluded_foods: Lista degli alimenti esclusi (nomi canonici)
        
    Returns:
        Dizionario dei sostituti filtrato
    """
    if not excluded_foods:
        return substitutes
    
    filtered_substitutes = {}
    
    for food_name, food_substitutes in substitutes.items():
        filtered_food_substitutes = {}
        
        for substitute_name, substitute_data in food_substitutes.items():
            # Mappa il sostituto al nome canonico
            substitute_canonical = db.alias.get(substitute_name.lower().replace("_", " "))
            if not substitute_canonical:
                substitute_canonical = substitute_name

            # Verifica che il sostituto non sia tra gli esclusi
            if substitute_canonical not in excluded_foods:
                filtered_food_substitutes[substitute_name] = substitute_data

        
        # Mantieni l'alimento solo se ha almeno un sostituto valido
        if filtered_food_substitutes:
            filtered_substitutes[food_name] = filtered_food_substitutes
    
    return filtered_substitutes


def check_and_replace_excluded_foods_final(
    final_portions: Dict[str, float],
    excluded_foods: List[str],
    meal_name: str
) -> Tuple[Dict[str, float], List[str], Dict[str, str]]:
    """
    Controlla la lista finale degli alimenti ottimizzati e sostituisce quelli esclusi.
    
    Args:
        final_portions: Porzioni finali ottimizzate
        excluded_foods: Lista degli alimenti esclusi dall'utente (nomi canonici)
        meal_name: Nome del pasto per la logica dei sostituti
        
    Returns:
        Tuple contenente:
        - Porzioni aggiornate con sostituzioni
        - Lista degli alimenti esclusi che sono stati trovati
        - Dizionario con le sostituzioni effettuate {alimento_escluso: sostituto}
    """
    if not excluded_foods:
        return final_portions, [], {}
    

    
    updated_portions = final_portions.copy()
    found_excluded = []
    replacements = {}
    
    try:
        # Carica i dati dei sostituti
        substitutes_data = load_substitutes_data()
        substitutes_db = substitutes_data.get("substitutes", {})
    except Exception as e:
        print(f"   ❌ Errore nel caricamento sostituti: {str(e)}")
        # Se non possiamo caricare i sostituti, rimuoviamo solo i cibi esclusi
        for food in list(updated_portions.keys()):
            normalized_food = db.alias.get(food.lower().replace("_", " "))
            if not normalized_food:
                normalized_food = food
            
            if normalized_food in excluded_foods:
                found_excluded.append(food)
                del updated_portions[food]
        
        return updated_portions, found_excluded, replacements
    
    for food in list(final_portions.keys()):
        # Mappa l'alimento al nome principale usando gli alias
        normalized_food = db.alias.get(food.lower().replace("_", " "))
        if not normalized_food:
            normalized_food = food
        
        # Se l'alimento è escluso dall'utente
        if normalized_food in excluded_foods:
            found_excluded.append(food)
            original_portion = final_portions[food]
            
            # Cerca un sostituto appropriato
            replacement = find_appropriate_substitute_final(
                normalized_food, 
                excluded_foods, 
                substitutes_db, 
                meal_name
            )
            
            if replacement:
                # Calcola la porzione equivalente per il sostituto
                replacement_portion = calculate_substitute_portion(
                    normalized_food, replacement, original_portion
                )
                
                # Rimuovi l'alimento escluso e aggiungi il sostituto
                del updated_portions[food]
                updated_portions[replacement] = replacement_portion
                replacements[food] = replacement
               
            else:
                # Nessun sostituto trovato nel database - prova con sostituti forzati
                forced_replacement = get_forced_substitute(normalized_food, excluded_foods, meal_name)
                
                if forced_replacement:
                    # Calcola porzione basata sui valori calorici medi
                    replacement_portion = calculate_forced_substitute_portion(
                        normalized_food, forced_replacement, original_portion
                    )
                    
                    # Rimuovi l'alimento escluso e aggiungi il sostituto forzato
                    del updated_portions[food]
                    updated_portions[forced_replacement] = replacement_portion
                    replacements[food] = forced_replacement
                   
                else:
                    # Nessun sostituto possibile, rimuovi l'alimento
                    del updated_portions[food]
    
    
    return updated_portions, found_excluded, replacements


def find_appropriate_substitute_final(
    excluded_food: str, 
    excluded_foods: List[str], 
    substitutes_db: Dict, 
    meal_name: str
) -> Optional[str]:
    """
    Trova un sostituto appropriato per un alimento escluso.
    
    Args:
        excluded_food: Nome canonico dell'alimento escluso
        excluded_foods: Lista completa degli alimenti esclusi
        substitutes_db: Database dei sostituti
        meal_name: Nome del pasto per la logica speciale
        
    Returns:
        Nome dell'alimento sostituto o None se non trovato
    """
    if excluded_food not in substitutes_db:
        return None
    
    available_substitutes = substitutes_db[excluded_food]
    
    # Determina se è colazione o spuntino per la logica speciale
    meal_name_lower = meal_name.lower()
    is_colazione_or_spuntino = any(keyword in meal_name_lower for keyword in [
        "colazione", "breakfast",
        "spuntino", "merenda", "snack",
        "spuntino_pomeridiano", "spuntino_mattutino", 
        "spuntino_serale", "spuntino_pomeriggio", 
        "spuntino_mattina", "spuntino_sera"
    ])
    
    # Ordina i sostituti per similarity_score (decrescente)
    sorted_substitutes = sorted(
        available_substitutes.items(),
        key=lambda x: x[1]['similarity_score'],
        reverse=True
    )
    
    for substitute_name, substitute_data in sorted_substitutes:
        # Mappa il sostituto al nome canonico
        substitute_canonical = db.alias.get(substitute_name.lower().replace("_", " "))
        if not substitute_canonical:
            substitute_canonical = substitute_name
        
        # Verifica che il sostituto non sia tra gli esclusi
        if substitute_canonical not in excluded_foods:
            # Logica speciale per pane durante colazione/spuntini
            if (is_colazione_or_spuntino and 
                excluded_food in ["pane_bianco", "pane_integrale"]):
                
                # Durante colazione/spuntini, sostituire pane solo con crackers/pan_bauletto
                allowed_substitutes = ["cracker", "crackers", "pan_bauletto", "pan bauletto"]
                if any(allowed in substitute_name.lower() for allowed in allowed_substitutes):
                    return substitute_name
                # Continua a cercare altri sostituti appropriati
                continue
            else:
                # Per tutti gli altri casi, usa il primo sostituto non escluso
                return substitute_name
    
    return None


def calculate_substitute_portion(
    original_food: str, 
    substitute_food: str, 
    original_portion: float
) -> float:
    """
    Calcola la porzione equivalente per un alimento sostituto.
    
    Args:
        original_food: Nome canonico dell'alimento originale
        substitute_food: Nome dell'alimento sostituto
        original_portion: Porzione originale in grammi
        
    Returns:
        Porzione equivalente del sostituto in grammi (arrotondata alla decina)
    """
    try:
        substitutes_data = load_substitutes_data()
        substitutes_db = substitutes_data.get("substitutes", {})
        
        if (original_food in substitutes_db and 
            substitute_food in substitutes_db[original_food]):
            
            substitute_data = substitutes_db[original_food][substitute_food]
            substitute_grams = (original_portion / 100.0) * substitute_data['grams']
            
            # Arrotonda alla decina più vicina
            substitute_grams_rounded = float(10 * np.floor(substitute_grams / 10 + 0.5))
            return max(10.0, substitute_grams_rounded)  # Minimo 10g
        else:
            # Fallback: mantieni la stessa porzione
            return original_portion
            
    except Exception as e:
        print(f"   ⚠️  Errore nel calcolo porzione sostituto: {str(e)}")
        return original_portion


def get_forced_substitute(excluded_food: str, excluded_foods: List[str], meal_name: str) -> Optional[str]:
    """
    Trova un sostituto forzato per un alimento escluso quando il database dei sostituti non ha opzioni.
    
    Args:
        excluded_food: Nome canonico dell'alimento escluso
        excluded_foods: Lista completa degli alimenti esclusi
        meal_name: Nome del pasto per la logica speciale
        
    Returns:
        Nome dell'alimento sostituto forzato o None se non possibile
    """
    # Determina se è colazione o spuntino per la logica speciale
    meal_name_lower = meal_name.lower()
    is_colazione_or_spuntino = any(keyword in meal_name_lower for keyword in [
        "colazione", "breakfast",
        "spuntino", "merenda", "snack",
        "spuntino_pomeridiano", "spuntino_mattutino", 
        "spuntino_serale", "spuntino_pomeriggio", 
        "spuntino_mattina", "spuntino_sera"
    ])
    
    # Mapping di sostituti forzati basati sul tipo di alimento e contesto
    forced_substitutes_map = {
        # PANE DURANTE COLAZIONE/SPUNTINI -> CRACKERS
        ("pane_bianco", True): ["cracker", "crackers"],
        ("pane_integrale", True): ["cracker", "crackers"],
        
        # PANE DURANTE PRANZO/CENA -> PASTA O PATATE
        ("pane_bianco", False): ["pasta_di_semola", "pasta", "patate"],
        ("pane_integrale", False): ["pasta_integrale", "pasta_di_semola", "pasta", "patate"],
        
        # PASTA -> RISO O PATATE
        ("pasta_di_semola", False): ["riso", "riso_bianco", "patate"],
        ("pasta_integrale", False): ["riso_integrale", "riso", "patate"],
        
        # RISO -> PASTA O PATATE  
        ("riso", False): ["pasta_di_semola", "pasta", "patate"],
        ("riso_bianco", False): ["pasta_di_semola", "pasta", "patate"],
        ("riso_integrale", False): ["pasta_integrale", "pasta_di_semola", "pasta", "patate"],
        
        # PATATE -> PASTA O RISO
        ("patate", False): ["pasta_di_semola", "pasta", "riso"],
        
        # LATTE -> YOGURT (per tutti i pasti)
        ("latte_intero", None): ["yogurt_intero", "yogurt_magro"],
        ("latte_parzialmente_scremato", None): ["yogurt_magro", "yogurt_greco_0percento"],
        ("latte_scremato", None): ["yogurt_magro", "yogurt_greco_0percento"],
        
        # YOGURT -> LATTE (per tutti i pasti)
        ("yogurt_intero", None): ["latte_intero", "latte_parzialmente_scremato"],
        ("yogurt_magro", None): ["latte_parzialmente_scremato", "latte_scremato"],
        
        # PROTEINE ANIMALI -> ALTRE PROTEINE
        ("pollo_petto", False): ["tacchino_petto", "manzo_magro", "merluzzo", "tonno_naturale"],
        ("manzo_magro", False): ["pollo_petto", "tacchino_petto", "merluzzo", "tonno_naturale"],
        ("tonno_naturale", False): ["merluzzo", "salmone", "pollo_petto"],
        ("merluzzo", False): ["tonno_naturale", "salmone", "pollo_petto"],
        
        # FRUTTA -> ALTRA FRUTTA
        ("mela", None): ["pera", "arancia", "banana", "uva"],
        ("pera", None): ["mela", "arancia", "banana", "uva"], 
        ("banana", None): ["mela", "pera", "arancia", "uva"],
        ("arancia", None): ["mela", "pera", "banana", "mandarino"],
        ("uva", None): ["mela", "pera", "banana"],
        
        # VERDURE -> ALTRE VERDURE
        ("verdure_miste", None): ["zucchine", "carote", "peperoni", "melanzane"],
        ("zucchine", None): ["verdure_miste", "carote", "peperoni"],
        ("carote", None): ["verdure_miste", "zucchine", "peperoni"],
        
        # FRUTTA SECCA -> ALTRA FRUTTA SECCA
        ("mandorle", None): ["noci", "nocciole", "arachidi"],
        ("noci", None): ["mandorle", "nocciole", "arachidi"],
        ("nocciole", None): ["mandorle", "noci", "arachidi"],
    }
    
    # Cerca il sostituto appropriato
    key = (excluded_food, is_colazione_or_spuntino)
    
    # Prova prima con il contesto specifico (colazione/spuntino)
    if key in forced_substitutes_map:
        candidates = forced_substitutes_map[key]
    else:
        # Prova con il contesto generale (None)
        key_general = (excluded_food, None)
        if key_general in forced_substitutes_map:
            candidates = forced_substitutes_map[key_general]
        else:
            return None
    
    # Trova il primo candidato che non è tra gli alimenti esclusi
    for candidate in candidates:
        # Mappa il candidato al nome canonico
        candidate_canonical = db.alias.get(candidate.lower().replace("_", " "))
        if not candidate_canonical:
            candidate_canonical = candidate
        
        if candidate_canonical not in excluded_foods:
            # Verifica che il candidato sia nel database
            found, _ = db.check_foods_in_db([candidate])
            if found:
                return candidate
    
    return None


def calculate_forced_substitute_portion(
    original_food: str, 
    substitute_food: str, 
    original_portion: float
) -> float:
    """
    Calcola la porzione equivalente per un sostituto forzato basandosi sui valori calorici medi.
    
    Args:
        original_food: Nome canonico dell'alimento originale
        substitute_food: Nome dell'alimento sostituto forzato
        original_portion: Porzione originale in grammi
        
    Returns:
        Porzione equivalente del sostituto in grammi (arrotondata alla decina)
    """
    # Valori calorici medi per 100g (database di riferimento)
    caloric_values = {
        # CEREALI E DERIVATI
        "pane_bianco": 270,
        "pane_integrale": 235,
        "pasta_di_semola": 350,
        "pasta_integrale": 340,
        "pasta": 350,
        "riso": 330,
        "riso_bianco": 330,
        "riso_integrale": 340,
        "patate": 85,
        "cracker": 430,
        "crackers": 430,
        
        # LATTICINI
        "latte_intero": 64,
        "latte_parzialmente_scremato": 50,
        "latte_scremato": 36,
        "yogurt_intero": 61,
        "yogurt_magro": 63,
        "yogurt_greco_0percento": 57,
        
        # PROTEINE ANIMALI
        "pollo_petto": 165,
        "tacchino_petto": 135,
        "manzo_magro": 158,
        "tonno_naturale": 116,
        "merluzzo": 82,
        "salmone": 185,
        
        # FRUTTA
        "mela": 52,
        "pera": 57,
        "banana": 89,
        "arancia": 47,
        "mandarino": 53,
        "uva": 60,
        
        # VERDURE
        "verdure_miste": 25,
        "zucchine": 20,
        "carote": 35,
        "peperoni": 31,
        "melanzane": 24,
        
        # FRUTTA SECCA
        "mandorle": 575,
        "noci": 654,
        "nocciole": 628,
        "arachidi": 567,
    }
    
    # Ottieni i valori calorici
    original_kcal = caloric_values.get(original_food, 200)  # Default 200 kcal/100g
    substitute_kcal = caloric_values.get(substitute_food, 200)  # Default 200 kcal/100g
    
    # Calcola la porzione equivalente basata sui valori calorici
    # Porzione_sostituto = Porzione_originale * (kcal_originale / kcal_sostituto)
    equivalent_portion = original_portion * (original_kcal / substitute_kcal)
    
    # Arrotonda alla decina più vicina
    equivalent_portion_rounded = float(10 * np.floor(equivalent_portion / 10 + 0.5))
    
    # Applica vincoli minimi e massimi ragionevoli
    min_portion = 10.0
    max_portion = 500.0  # Massimo 500g per evitare porzioni eccessive
    
    return max(min_portion, min(max_portion, equivalent_portion_rounded))


def optimize_meal_portions(meal_name: str, food_list: List[str], user_id: str = None) -> Dict[str, Any]:
    """
    Ottimizza automaticamente le porzioni degli alimenti per un pasto specifico.
    
    Verifica automaticamente che tutti gli alimenti siano presenti nel database,
    calcola le quantità in grammi per rispettare i target nutrizionali 
    dell'utente per quel pasto, e infine arrotonda le quantità alla decina
    più vicina (es. 118.7g diventa 120g).
    
    Per i pasti di colazione, esegue ottimizzazioni intelligenti:
    1. Se deficit di grassi >3g e >15%, prova ad aggiungere mandorle
    2. Se deficit di proteine >5g e >15%, prova ad aggiungere proteine in polvere
    
    Per i pasti di spuntino, esegue ottimizzazioni intelligenti:
    1. Se deficit di grassi >2g e >15%, prova ad aggiungere mandorle
    
    Per i pasti di pranzo e cena, esegue ottimizzazioni intelligenti:
    1. Prova ad aggiungere olio d'oliva se può migliorare l'ottimizzazione
    2. Aggiunge/rimuove proteine (pollo) se l'errore proteico è >15%
    3. Se l'errore sui carboidrati è >20%, prova strategie alternative:
       - Aggiunge pane per deficit di carboidrati
       - Sostituisce pasta↔riso o patate↔pane per migliorare l'equilibrio
    
    Args:
        meal_name: Nome del pasto (es: 'Colazione', 'Pranzo', 'Cena', 'Spuntino')
        food_list: Lista degli alimenti da includere nel pasto
        user_id: ID dell'utente (opzionale, usa get_user_id() se None - per compatibilità con test)
        
    Returns:
        Dict contenente:
        - success: bool se l'ottimizzazione è riuscita
        - portions: dict con alimento -> grammi ottimizzati e arrotondati
        - target_nutrients: target nutrizionali del pasto
        - actual_nutrients: valori nutrizionali effettivi (calcolati sulle porzioni arrotondate)
        - errors: dict con errori percentuali per ogni macronutriente
        - optimization_summary: messaggio di riepilogo delle modifiche apportate
        - macro_single_foods: dict con il contributo nutrizionale di ogni alimento
        - substitutes: dict con i sostituti per ogni alimento e relative grammature
        - error_message: messaggio di errore se fallisce (solo in caso di errore)
        
    Raises:
        ValueError: Se alimenti non sono nel database o dati utente mancanti
    """
    try:
        # 1. Estrai l'ID utente e carica i target nutrizionali
        if user_id is None:
            user_id = get_user_id()
        target_nutrients = load_user_meal_targets(user_id, meal_name)
        
        # 2. Verifica che tutti gli alimenti originali siano nel database
        all_found, foods_not_found = db.check_foods_in_db(food_list)
        
        if not all_found:
            return {
                "success": False,
                "error_message": f"I seguenti alimenti non sono stati trovati nel database: {', '.join(foods_not_found)}",
                "portions": {},
                "target_nutrients": {},
                "actual_nutrients": {},
                "errors": {},
                "optimization_summary": "",
                "macro_single_foods": {},
                "substitutes": {}
            }
        
        # 3. Estrai i dati nutrizionali degli alimenti originali
        foods_nutrition_original = get_food_nutrition_per_100g(food_list)
        
        # 4. Determina se dobbiamo testare anche con l'olio (solo per pranzo/cena)
        meal_name_lower = meal_name.lower()
        is_lunch_or_dinner = any(keyword in meal_name_lower for keyword in 
                               ["pranzo", "cena", "lunch", "dinner", "Pranzo", "Cena", "Lunch", "Dinner", "PRANZO", "CENA", "LUNCH", "DINNER"])
        
        # Controlla se c'è già olio nella lista
        oil_variants = ["olio", "olio_oliva", "olio d'oliva", "olio di oliva"]
        oil_already_present = any(any(oil_variant in food.lower() for oil_variant in oil_variants) for food in food_list)
        
        should_test_oil = is_lunch_or_dinner and not oil_already_present
        
        # 5. Se necessario, prepara i dati nutrizionali anche con l'olio
        foods_nutrition_with_oil = None
        if should_test_oil:
            food_list_with_oil = food_list + ["olio_oliva"]
            # Verifica che olio_oliva sia nel database
            oil_found, _ = db.check_foods_in_db(["olio_oliva"])
            if oil_found:
                foods_nutrition_with_oil = get_food_nutrition_per_100g(food_list_with_oil)
        
        # 6. Ottimizza senza olio
        optimized_portions_original = optimize_portions(target_nutrients, foods_nutrition_original)
        actual_nutrients_original = calculate_actual_nutrients(optimized_portions_original, foods_nutrition_original)
        
        # Calcola errore originale
        original_error = sum([
            abs(actual_nutrients_original["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
            abs(actual_nutrients_original["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
            abs(actual_nutrients_original["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
            abs(actual_nutrients_original["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
        ]) / 4
        
        # 7. Se necessario, ottimizza anche con l'olio e confronta
        oil_added = False
        final_portions = optimized_portions_original
        final_actual_nutrients = actual_nutrients_original
        final_food_list = food_list
        improvement = 0.0
        
        if should_test_oil and foods_nutrition_with_oil is not None and original_error > 0.1:
            # Ottimizza con olio
            optimized_portions_with_oil = optimize_portions(target_nutrients, foods_nutrition_with_oil)
            actual_nutrients_with_oil = calculate_actual_nutrients(optimized_portions_with_oil, foods_nutrition_with_oil)
            
            # Calcola errore con olio
            error_with_oil = sum([
                abs(actual_nutrients_with_oil["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                abs(actual_nutrients_with_oil["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                abs(actual_nutrients_with_oil["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                abs(actual_nutrients_with_oil["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
            ]) / 4
            
            # Calcola miglioramento
            improvement = original_error - error_with_oil
            
            # Usa la versione con olio se il miglioramento è significativo
            if improvement > 0.05 or (improvement > 0.02 and original_error > 0.15):
                oil_added = True
                final_portions = optimized_portions_with_oil
                final_actual_nutrients = actual_nutrients_with_oil
                final_food_list = food_list_with_oil
        
        # 8. Step aggiuntivo: ottimizzazione grassi per colazione
        fat_added = False
        fat_adjustment_food = None
        
        # Determina se è colazione
        is_breakfast = any(keyword in meal_name_lower for keyword in 
                          ["colazione", "breakfast", "Colazione", "Breakfast", "COLAZIONE", "BREAKFAST"])
        
        if is_breakfast:
            # Calcola errore sui grassi attuale
            fat_target = target_nutrients["grassi_g"]
            fat_actual = final_actual_nutrients["grassi_g"]
            fat_deficit = fat_target - fat_actual
            fat_error_pct = abs(fat_deficit) / fat_target * 100 if fat_target > 0 else 0
            
            # Se c'è un deficit significativo di grassi (>15%), prova ad aggiungere mandorle
            if fat_deficit > 3 and fat_error_pct > 15:  # Deficit significativo (>3g e >15%)
                # Controlla se le mandorle non sono già presenti
                almond_variants = ["mandorle", "mandorla", "mandorle_sgusciate", "mandorle sgusciate"]
                almonds_already_present = any(any(variant in food.lower() for variant in almond_variants) for food in final_food_list)
                
                if not almonds_already_present:
                    test_food_list_almonds = final_food_list + ["mandorle"]
                    almonds_found, _ = db.check_foods_in_db(["mandorle"])
                    
                    if almonds_found:
                        try:
                            # Calcola i dati nutrizionali per la lista con mandorle aggiunte
                            foods_nutrition_almonds = get_food_nutrition_per_100g(test_food_list_almonds)
                            
                            optimized_portions_almonds = optimize_portions(target_nutrients, foods_nutrition_almonds)
                            actual_nutrients_almonds = calculate_actual_nutrients(optimized_portions_almonds, foods_nutrition_almonds)
                            
                            # Calcola errore con mandorle aggiunte
                            error_with_almonds = sum([
                                abs(actual_nutrients_almonds["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(actual_nutrients_almonds["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(actual_nutrients_almonds["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(actual_nutrients_almonds["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Calcola errore attuale
                            current_error = sum([
                                abs(final_actual_nutrients["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(final_actual_nutrients["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(final_actual_nutrients["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(final_actual_nutrients["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Se aggiungere mandorle migliora significativamente
                            if error_with_almonds < current_error - 0.03:
                                fat_added = True
                                final_portions = optimized_portions_almonds
                                final_actual_nutrients = actual_nutrients_almonds
                                final_food_list = test_food_list_almonds
                                fat_adjustment_food = "mandorle"
                                
                        except Exception as e:
                            logger.warning(f"Errore nel test con mandorle aggiunte: {str(e)}")

        # 8.0.1. Step aggiuntivo: ottimizzazione proteine per colazione
        protein_added_breakfast = False
        protein_adjustment_food_breakfast = None
        
        if is_breakfast:  
            # Calcola errore proteico attuale
            protein_target = target_nutrients["proteine_g"]
            protein_actual = final_actual_nutrients["proteine_g"]
            protein_deficit = protein_target - protein_actual
            protein_error_pct = abs(protein_deficit) / protein_target * 100 if protein_target > 0 else 0
            
            # Se c'è un deficit significativo di proteine (>15%), prova ad aggiungere proteine in polvere
            if protein_deficit > 10 and protein_error_pct > 15:  # Deficit significativo (>5g e >15%)
                # Controlla se le proteine in polvere non sono già presenti
                protein_variants = ["iso_fuji_yamamoto", "pro_milk_20g_proteine", "proteine", "proteine in polvere", "iso"]
                protein_already_present = any(any(variant in food.lower() for variant in protein_variants) for food in final_food_list)
                
                if not protein_already_present:
                    test_food_list_protein = final_food_list + ["iso_fuji_yamamoto"]
                    protein_found, _ = db.check_foods_in_db(["iso_fuji_yamamoto"])
                    
                    if protein_found:
                        try:
                            # Calcola i dati nutrizionali per la lista con proteine in polvere aggiunte
                            foods_nutrition_protein = get_food_nutrition_per_100g(test_food_list_protein)
                            
                            optimized_portions_protein = optimize_portions(target_nutrients, foods_nutrition_protein)
                            actual_nutrients_protein = calculate_actual_nutrients(optimized_portions_protein, foods_nutrition_protein)
                            
                            # Calcola errore con proteine in polvere aggiunte
                            error_with_protein = sum([
                                abs(actual_nutrients_protein["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(actual_nutrients_protein["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(actual_nutrients_protein["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(actual_nutrients_protein["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Calcola errore attuale
                            current_error = sum([
                                abs(final_actual_nutrients["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(final_actual_nutrients["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(final_actual_nutrients["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(final_actual_nutrients["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Se aggiungere proteine in polvere migliora significativamente
                            if error_with_protein < current_error - 0.03:
                                protein_added_breakfast = True
                                final_portions = optimized_portions_protein
                                final_actual_nutrients = actual_nutrients_protein
                                final_food_list = test_food_list_protein
                                protein_adjustment_food_breakfast = "iso_fuji_yamamoto"
                                
                        except Exception as e:
                            logger.warning(f"Errore nel test con proteine in polvere aggiunte: {str(e)}")

        # 8.1. Step aggiuntivo: ottimizzazione grassi per spuntini
        # Determina se è uno spuntino
        is_snack = any(keyword in meal_name_lower for keyword in 
                      ["spuntino", "merenda", "snack", "Spuntino", "Merenda", "Snack", "SPUNTINO", "MERENDA", "SNACK", "spuntino_pomeridiano", "spuntino_mattutino", "spuntino_serale", "spuntino_pomeriggio", "spuntino_mattina", "spuntino_sera"])
        
        if is_snack and not fat_added:  # Solo se non abbiamo già aggiunto grassi per la colazione
            # Calcola errore sui grassi attuale
            fat_target = target_nutrients["grassi_g"]
            fat_actual = final_actual_nutrients["grassi_g"]
            fat_deficit = fat_target - fat_actual
            fat_error_pct = abs(fat_deficit) / fat_target * 100 if fat_target > 0 else 0
            
            # Se c'è un deficit significativo di grassi (>15%), prova ad aggiungere mandorle
            if fat_deficit > 2 and fat_error_pct > 15:  # Soglia più bassa per spuntini (>2g e >15%)
                # Controlla se le mandorle non sono già presenti
                almond_variants = ["mandorle", "mandorla", "mandorle_sgusciate", "mandorle sgusciate"]
                almonds_already_present = any(any(variant in food.lower() for variant in almond_variants) for food in final_food_list)
                
                if not almonds_already_present:
                    test_food_list_almonds = final_food_list + ["mandorle"]
                    almonds_found, _ = db.check_foods_in_db(["mandorle"])
                    
                    if almonds_found:
                        try:
                            # Calcola i dati nutrizionali per la lista con mandorle aggiunte
                            foods_nutrition_almonds = get_food_nutrition_per_100g(test_food_list_almonds)
                            
                            optimized_portions_almonds = optimize_portions(target_nutrients, foods_nutrition_almonds)
                            actual_nutrients_almonds = calculate_actual_nutrients(optimized_portions_almonds, foods_nutrition_almonds)
                            
                            # Calcola errore con mandorle aggiunte
                            error_with_almonds = sum([
                                abs(actual_nutrients_almonds["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(actual_nutrients_almonds["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(actual_nutrients_almonds["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(actual_nutrients_almonds["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Calcola errore attuale
                            current_error = sum([
                                abs(final_actual_nutrients["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                abs(final_actual_nutrients["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                abs(final_actual_nutrients["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                abs(final_actual_nutrients["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                            ]) / 4
                            
                            # Se aggiungere mandorle migliora significativamente
                            if error_with_almonds < current_error - 0.03:
                                fat_added = True
                                final_portions = optimized_portions_almonds
                                final_actual_nutrients = actual_nutrients_almonds
                                final_food_list = test_food_list_almonds
                                fat_adjustment_food = "mandorle"
                                
                        except Exception as e:
                            logger.warning(f"Errore nel test con mandorle aggiunte per spuntino: {str(e)}")

        # 8.2. Step aggiuntivo: ottimizzazione proteine per pranzo/cena
        protein_added = False
        protein_removed = False
        protein_adjustment_food = None
        
        if is_lunch_or_dinner:
            # Calcola errore proteico attuale
            protein_target = target_nutrients["proteine_g"]
            protein_actual = final_actual_nutrients["proteine_g"]
            protein_deficit = protein_target - protein_actual
            protein_error_pct = abs(protein_deficit) / protein_target * 100 if protein_target > 0 else 0
            
            # Se l'errore proteico è significativo (>15%), prova a correggerlo
            if protein_error_pct > 15:
                best_solution = {
                    "portions": final_portions,
                    "actual_nutrients": final_actual_nutrients,
                    "food_list": final_food_list,
                    "error": original_error if not oil_added else (original_error - improvement)
                }
                
                # CASO 1: Deficit proteico - prova ad aggiungere pollo
                if protein_deficit > 5:  # Deficit significativo (>5g)
                    # Controlla se il pollo non è già presente
                    chicken_variants = ["pollo", "petto_pollo", "petto di pollo", "pollo_petto"]
                    chicken_already_present = any(any(variant in food.lower() for variant in chicken_variants) for food in final_food_list)
                    
                    if not chicken_already_present:
                        test_food_list_protein = final_food_list + ["pollo"]
                        chicken_found, _ = db.check_foods_in_db(["pollo"])
                        
                        if chicken_found:
                            try:
                                # Calcola i dati nutrizionali per la lista con pollo aggiunto
                                foods_nutrition_protein = get_food_nutrition_per_100g(test_food_list_protein)
                                
                                optimized_portions_protein = optimize_portions(target_nutrients, foods_nutrition_protein)
                                actual_nutrients_protein = calculate_actual_nutrients(optimized_portions_protein, foods_nutrition_protein)
                                
                                # Calcola errore con pollo aggiunto
                                error_with_protein = sum([
                                    abs(actual_nutrients_protein["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                    abs(actual_nutrients_protein["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                    abs(actual_nutrients_protein["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                    abs(actual_nutrients_protein["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                                ]) / 4
                                
                                # Se aggiungere pollo migliora significativamente
                                if error_with_protein < best_solution["error"] - 0.03:
                                    best_solution = {
                                        "portions": optimized_portions_protein,
                                        "actual_nutrients": actual_nutrients_protein,
                                        "food_list": test_food_list_protein,
                                        "error": error_with_protein
                                    }
                                    protein_added = True
                                    protein_adjustment_food = "pollo"
                                    
                            except Exception as e:
                                logger.warning(f"Errore nel test con pollo aggiunto: {str(e)}")
                
                # CASO 2: Eccesso proteico - prova a rimuovere una fonte proteica
                elif protein_deficit < -5:  # Eccesso significativo (>5g)
                    # Identifica fonti proteiche rimuovibili (categoria proteine_animali o >15g proteine/100g)
                    nutrition_data = foods_nutrition_with_oil if oil_added else foods_nutrition_original
                    
                    protein_sources = []
                    for food in final_food_list:
                        if food in nutrition_data:
                            food_data = nutrition_data[food]
                            is_protein_source = (
                                food_data.get("categoria") == "proteine_animali" or
                                food_data.get("proteine_g", 0) > 15
                            )
                            if is_protein_source:
                                protein_sources.append(food)
                    
                    # Testa rimuovendo ogni fonte proteica e scegli la migliore
                    for protein_food in protein_sources:
                        test_food_list_no_protein = [f for f in final_food_list if f != protein_food]
                        
                        if len(test_food_list_no_protein) >= 2:  # Mantieni almeno 2 alimenti
                            try:
                                foods_nutrition_no_protein = get_food_nutrition_per_100g(test_food_list_no_protein)
                                optimized_portions_no_protein = optimize_portions(target_nutrients, foods_nutrition_no_protein)
                                actual_nutrients_no_protein = calculate_actual_nutrients(optimized_portions_no_protein, foods_nutrition_no_protein)
                                
                                # Calcola errore senza questa proteina
                                error_no_protein = sum([
                                    abs(actual_nutrients_no_protein["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                    abs(actual_nutrients_no_protein["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                    abs(actual_nutrients_no_protein["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                    abs(actual_nutrients_no_protein["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                                ]) / 4
                                
                                # Se rimuovere questa proteina migliora significativamente
                                if error_no_protein < best_solution["error"] - 0.03:
                                    best_solution = {
                                        "portions": optimized_portions_no_protein,
                                        "actual_nutrients": actual_nutrients_no_protein,
                                        "food_list": test_food_list_no_protein,
                                        "error": error_no_protein
                                    }
                                    protein_removed = True
                                    protein_adjustment_food = protein_food
                                    
                            except Exception as e:
                                logger.warning(f"Errore nel test rimuovendo {protein_food}: {str(e)}")
                
                # Applica la migliore soluzione trovata
                final_portions = best_solution["portions"]
                final_actual_nutrients = best_solution["actual_nutrients"]
                final_food_list = best_solution["food_list"]
        
        # 8.3. Step aggiuntivo: ottimizzazione carboidrati per pranzo/cena
        carb_added = False
        carb_substituted = False
        carb_adjustment_food = None
        carb_substitution_type = None
        
        if is_lunch_or_dinner:
            # Calcola errore sui carboidrati attuale
            carb_target = target_nutrients["carboidrati_g"]
            carb_actual = final_actual_nutrients["carboidrati_g"]
            carb_deficit = carb_target - carb_actual
            carb_error_pct = abs(carb_deficit) / carb_target * 100 if carb_target > 0 else 0
            
            # Se l'errore sui carboidrati è "molto brutto" (>20%), prova strategie alternative
            if carb_error_pct > 20:
                best_carb_solution = {
                    "portions": final_portions,
                    "actual_nutrients": final_actual_nutrients,
                    "food_list": final_food_list,
                    "error": sum([
                        abs(final_actual_nutrients["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                        abs(final_actual_nutrients["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                        abs(final_actual_nutrients["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                        abs(final_actual_nutrients["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                    ]) / 4
                }
                
                # STRATEGIA 1: Aggiungere pane se necessario per deficit di carboidrati
                if carb_deficit > 10:  # Deficit significativo (>10g)
                    bread_variants = ["pane", "pane_bianco", "pane_integrale", "pane bianco", "pane integrale"]
                    bread_already_present = any(any(variant in food.lower() for variant in bread_variants) for food in final_food_list)
                    
                    if not bread_already_present:
                        test_food_list_bread = final_food_list + ["pane"]
                        bread_found, _ = db.check_foods_in_db(["pane"])
                        
                        if bread_found:
                            try:
                                foods_nutrition_bread = get_food_nutrition_per_100g(test_food_list_bread)
                                optimized_portions_bread = optimize_portions(target_nutrients, foods_nutrition_bread)
                                actual_nutrients_bread = calculate_actual_nutrients(optimized_portions_bread, foods_nutrition_bread)
                                
                                error_with_bread = sum([
                                    abs(actual_nutrients_bread["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                    abs(actual_nutrients_bread["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                    abs(actual_nutrients_bread["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                    abs(actual_nutrients_bread["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                                ]) / 4
                                
                                if error_with_bread < best_carb_solution["error"] - 0.03:
                                    best_carb_solution = {
                                        "portions": optimized_portions_bread,
                                        "actual_nutrients": actual_nutrients_bread,
                                        "food_list": test_food_list_bread,
                                        "error": error_with_bread
                                    }
                                    carb_added = True
                                    carb_adjustment_food = "pane"
                                    
                            except Exception as e:
                                logger.warning(f"Errore nel test con pane aggiunto: {str(e)}")
                
                # STRATEGIA 2: Sostituzioni di carboidrati
                substitution_tests = [
                    # Sostituire pasta con riso
                    {"from": ["pasta", "pasta_normale", "pasta normale"], "to": "riso", "type": "pasta→riso"},
                    # Sostituire riso con pasta
                    {"from": ["riso", "riso_bianco", "riso bianco"], "to": "pasta", "type": "riso→pasta"},
                    # Sostituire patate con pane
                    {"from": ["patate", "patata", "patate_lesse", "patate lesse"], "to": "pane", "type": "patate→pane"},
                    # Sostituire pane con patate
                    {"from": ["pane", "pane_bianco", "pane_integrale", "pane bianco", "pane integrale"], "to": "patate", "type": "pane→patate"}
                ]
                
                for substitution in substitution_tests:
                    # Trova l'alimento da sostituire nella lista corrente
                    food_to_replace = None
                    for food in final_food_list:
                        if any(variant in food.lower() for variant in substitution["from"]):
                            food_to_replace = food
                            break
                    
                    if food_to_replace:
                        # Controlla se l'alimento di sostituzione non è già presente
                        substitute_already_present = any(substitution["to"] in food.lower() for food in final_food_list)
                        
                        if not substitute_already_present:
                            # Crea la nuova lista sostituendo l'alimento
                            test_food_list_sub = [substitution["to"] if food == food_to_replace else food for food in final_food_list]
                            
                            # Verifica che l'alimento sostituto sia nel database
                            substitute_found, _ = db.check_foods_in_db([substitution["to"]])
                            
                            if substitute_found:
                                try:
                                    foods_nutrition_sub = get_food_nutrition_per_100g(test_food_list_sub)
                                    optimized_portions_sub = optimize_portions(target_nutrients, foods_nutrition_sub)
                                    actual_nutrients_sub = calculate_actual_nutrients(optimized_portions_sub, foods_nutrition_sub)
                                    
                                    error_with_sub = sum([
                                        abs(actual_nutrients_sub["kcal"] - target_nutrients["kcal"]) / max(target_nutrients["kcal"], 1),
                                        abs(actual_nutrients_sub["proteine_g"] - target_nutrients["proteine_g"]) / max(target_nutrients["proteine_g"], 1),
                                        abs(actual_nutrients_sub["carboidrati_g"] - target_nutrients["carboidrati_g"]) / max(target_nutrients["carboidrati_g"], 1),
                                        abs(actual_nutrients_sub["grassi_g"] - target_nutrients["grassi_g"]) / max(target_nutrients["grassi_g"], 1)
                                    ]) / 4
                                    
                                    if error_with_sub < best_carb_solution["error"] - 0.03:
                                        best_carb_solution = {
                                            "portions": optimized_portions_sub,
                                            "actual_nutrients": actual_nutrients_sub,
                                            "food_list": test_food_list_sub,
                                            "error": error_with_sub
                                        }
                                        carb_substituted = True
                                        carb_adjustment_food = food_to_replace
                                        carb_substitution_type = substitution["type"]
                                        
                                except Exception as e:
                                    logger.warning(f"Errore nel test sostituzione {substitution['type']}: {str(e)}")
                
                # Applica la migliore soluzione per i carboidrati trovata
                final_portions = best_carb_solution["portions"]
                final_actual_nutrients = best_carb_solution["actual_nutrients"]
                final_food_list = best_carb_solution["food_list"]
        
        # 9. Arrotonda le porzioni alla decina più vicina
        optimized_portions_rounded = {
            food: float(10 * np.floor(grams / 10 + 0.5)) for food, grams in final_portions.items()
        }
        
        # 10. Calcola i contributi individuali di ogni alimento per le porzioni arrotondate
        individual_contributions = {}
        
        # Usa i dati nutrizionali corretti (considerando olio e aggiustamenti proteici)
        nutrition_data = get_food_nutrition_per_100g(final_food_list)
            
        for food, grams in optimized_portions_rounded.items():
            if food in nutrition_data:
                nutrition = nutrition_data[food]
                
                individual_contributions[food] = {
                    "portion_g": grams,
                    "kcal": float(round(nutrition['energia_kcal'] * grams / 100, 1)),
                    "proteine_g": float(round(nutrition['proteine_g'] * grams / 100, 1)),
                    "carboidrati_g": float(round(nutrition['carboidrati_g'] * grams / 100, 1)),
                    "grassi_g": float(round(nutrition['grassi_g'] * grams / 100, 1)),
                    "categoria": nutrition['categoria']
                }
        
        # 11. Ricalcola i nutrienti effettivi dalle porzioni arrotondate per coerenza
        final_actual_nutrients_rounded = calculate_actual_nutrients(optimized_portions_rounded, nutrition_data)
        
        # 12. Calcola gli errori percentuali
        errors = {}
        for nutrient in ["kcal", "proteine_g", "carboidrati_g", "grassi_g"]:
            target = target_nutrients[nutrient]
            actual = final_actual_nutrients_rounded[nutrient]
            if target > 0:
                error_pct = abs(actual - target) / target * 100
                errors[f"{nutrient}_error_pct"] = float(round(error_pct, 1))
            else:
                errors[f"{nutrient}_error_pct"] = 0.0
        
        # 13. Gestisci gli alimenti esclusi dall'utente
        excluded_foods = load_user_excluded_foods(user_id)
        excluded_replacements = {}
        found_excluded_foods = []
        
        if excluded_foods:
            # Controlla e sostituisce gli alimenti esclusi
            updated_portions, found_excluded_foods, excluded_replacements = check_and_replace_excluded_foods_final(
                optimized_portions_rounded, excluded_foods, meal_name
            )
            
            # Se ci sono state sostituzioni, ricalcola i nutrienti e i contributi
            if excluded_replacements:
                optimized_portions_rounded = updated_portions
                
                # Ricalcola i dati nutrizionali per la nuova lista di alimenti
                final_food_list_updated = list(optimized_portions_rounded.keys())
                nutrition_data_updated = get_food_nutrition_per_100g(final_food_list_updated)
                
                # Ricalcola i nutrienti effettivi
                final_actual_nutrients_rounded = calculate_actual_nutrients(optimized_portions_rounded, nutrition_data_updated)
                
                # Ricalcola i contributi individuali
                individual_contributions = {}
                for food, grams in optimized_portions_rounded.items():
                    if food in nutrition_data_updated:
                        nutrition = nutrition_data_updated[food]
                        individual_contributions[food] = {
                            "portion_g": grams,
                            "kcal": float(round(nutrition['energia_kcal'] * grams / 100, 1)),
                            "proteine_g": float(round(nutrition['proteine_g'] * grams / 100, 1)),
                            "carboidrati_g": float(round(nutrition['carboidrati_g'] * grams / 100, 1)),
                            "grassi_g": float(round(nutrition['grassi_g'] * grams / 100, 1)),
                            "categoria": nutrition['categoria']
                        }
                
                # Ricalcola gli errori percentuali
                errors = {}
                for nutrient in ["kcal", "proteine_g", "carboidrati_g", "grassi_g"]:
                    target = target_nutrients[nutrient]
                    actual = final_actual_nutrients_rounded[nutrient]
                    if target > 0:
                        error_pct = abs(actual - target) / target * 100
                        errors[f"{nutrient}_error_pct"] = float(round(error_pct, 1))
                    else:
                        errors[f"{nutrient}_error_pct"] = 0.0
        
        # 14. Calcola i sostituti per ogni alimento (con filtro esclusioni integrato)
        food_substitutes = calculate_food_substitutes(optimized_portions_rounded, meal_name, user_id)
        
        # 15. Prepara il messaggio di summary con tutte le ottimizzazioni
        final_food_count = len(optimized_portions_rounded)
        summary_parts = [f"Ottimizzazione completata per {meal_name} con {final_food_count} alimenti"]
        
        if oil_added:
            summary_parts.append(f"olio aggiunto automaticamente (miglioramento: {improvement:.1%})")
        
        if fat_added:
            summary_parts.append(f"{fat_adjustment_food} aggiunte per deficit di grassi")
        
        if protein_added_breakfast:
            summary_parts.append(f"{protein_adjustment_food_breakfast} aggiunte per deficit proteico")
        
        if protein_added:
            summary_parts.append(f"{protein_adjustment_food} aggiunto per deficit proteico")
        elif protein_removed:
            summary_parts.append(f"{protein_adjustment_food} rimosso per eccesso proteico")
        
        if carb_added:
            summary_parts.append(f"{carb_adjustment_food} aggiunto per migliorare i carboidrati")
        elif carb_substituted:
            summary_parts.append(f"sostituzione {carb_substitution_type} per migliorare i carboidrati")
        
        if excluded_replacements:
            excluded_count = len(excluded_replacements)
            if excluded_count == 1:
                excluded_names = list(excluded_replacements.keys())[0]
                replacement_name = list(excluded_replacements.values())[0]
                summary_parts.append(f"sostituito {excluded_names} (escluso) con {replacement_name}")
            else:
                summary_parts.append(f"{excluded_count} alimenti esclusi sostituiti")
        elif found_excluded_foods:
            excluded_count = len(found_excluded_foods)
            if excluded_count == 1:
                summary_parts.append(f"rimosso {found_excluded_foods[0]} (escluso dall'utente)")
            else:
                summary_parts.append(f"{excluded_count} alimenti esclusi rimossi")
        
        summary_parts.append("Porzioni arrotondate alla decina più vicina")
        
        optimization_summary = ". ".join(summary_parts) + "."
        
        return {
            "success": True,
            "portions": optimized_portions_rounded,
            "target_nutrients": target_nutrients,
            "actual_nutrients": final_actual_nutrients_rounded,
            "errors": errors,
            "optimization_summary": optimization_summary,
            "macro_single_foods": individual_contributions,
            "substitutes": food_substitutes
        }
        
    except Exception as e:
        logger.error(f"Errore nell'ottimizzazione del pasto: {str(e)}")
        return {
            "success": False,
            "error_message": f"Errore nell'ottimizzazione: {str(e)}",
            "portions": {},
            "target_nutrients": {},
            "actual_nutrients": {},
            "errors": {},
            "optimization_summary": "",
            "macro_single_foods": {},
            "substitutes": {}
        }


def load_substitutes_data() -> Dict[str, Any]:
    """
    Carica i dati dei sostituti alimentari dal file alimenti_sostitutivi.json.
    
    Returns:
        Dict contenente i dati dei sostituti
        
    Raises:
        FileNotFoundError: Se il file non esiste
        ValueError: Se il file non è un JSON valido
    """
    substitutes_file = "Dati_processed/alimenti_sostitutivi.json"
    
    if not os.path.exists(substitutes_file):
        raise FileNotFoundError(f"File sostituti non trovato: {substitutes_file}")
    
    try:
        with open(substitutes_file, 'r', encoding='utf-8') as f:
            substitutes_data = json.load(f)
        return substitutes_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Errore nella lettura del file sostituti: {str(e)}")


def calculate_food_substitutes(optimized_portions: Dict[str, float], meal_name: str, user_id: str = None) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Calcola i sostituti per ogni alimento con le grammature corrette.
    
    Per colazione e spuntini:
    - Il pane e pane integrale vengono sostituiti solo con crackers o pan bauletto
    - Le uova e albume vengono sostituiti solo con parmigiano o albume d'uovo
    
    Args:
        optimized_portions: Dizionario con alimento -> grammi ottimizzati
        meal_name: Nome del pasto
        user_id: ID dell'utente per caricare gli alimenti esclusi 
                (opzionale, usa get_user_id() se None)
        
    Returns:
        Dict con struttura: {
            "alimento": {
                "substitute1": {"grams": X, "similarity_score": Y},
                "substitute2": {"grams": X, "similarity_score": Y}
            }
        }
    """
    try:
        substitutes_data = load_substitutes_data()
        substitutes_db = substitutes_data.get("substitutes", {})
        
        # Carica gli alimenti esclusi dall'utente
        excluded_foods = []
        try:
            # Se user_id non è fornito, tenta di ottenerlo automaticamente
            if not user_id:
                user_id = get_user_id()
            
            # Carica gli alimenti esclusi usando l'user_id ottenuto
            excluded_foods = load_user_excluded_foods(user_id)
        except Exception as e:
            # Se non riusciamo a ottenere user_id o caricare excluded_foods, procediamo senza esclusioni
            print(f"   ⚠️  Impossibile caricare excluded_foods: {str(e)}")
            excluded_foods = []
        
        result = {}
        
        # Determina se è colazione o spuntino
        meal_name_lower = meal_name.lower()
        is_colazione_or_spuntino = any(keyword in meal_name_lower for keyword in [
            "colazione", "breakfast",
            "spuntino", "merenda", "snack",
            "spuntino_pomeridiano", "spuntino_mattutino", 
            "spuntino_serale", "spuntino_pomeriggio", 
            "spuntino_mattina", "spuntino_sera"
        ])
        
        for food, portion_grams in optimized_portions.items():
            food_substitutes = {}
            
            # Usa la mappatura degli alias dal database per trovare il nome principale
            # Normalizza il nome dell'alimento usando la stessa logica di NutriDB
            normalized_food_name = db.alias.get(food.lower().replace("_", " "))
            if not normalized_food_name:
                normalized_food_name = food
            
            # Logica speciale per pane/pane integrale durante colazione/spuntini
            if is_colazione_or_spuntino and normalized_food_name in ["pane_bianco", "pane_integrale"]:
                # Crea sostituti personalizzati per crackers e pan bauletto
                # Devo cercare questi alimenti nel database dei sostituti per calcolare le equivalenze
                
                # Cerca nel database le conversioni per pane -> crackers e pane -> pan_bauletto
                pane_substitutes = substitutes_db.get(normalized_food_name, {})
                
                # Lista dei sostituti ammessi per colazione/spuntini
                allowed_substitutes = ["cracker", "pan_bauletto", "crackers", "pan bauletto"]
                
                for substitute_name, substitute_data in pane_substitutes.items():
                    # Verifica se il sostituto è tra quelli ammessi
                    if any(allowed in substitute_name.lower() for allowed in allowed_substitutes):
                        # Se abbiamo cibi esclusi, verifica che il sostituto non sia escluso
                        if excluded_foods:
                            substitute_canonical = db.alias.get(substitute_name.lower().replace("_", " "))
                            if not substitute_canonical:
                                substitute_canonical = substitute_name
                            
                            if substitute_canonical in excluded_foods:
                                continue  # Salta questo sostituto se è escluso
                        
                        # Calcola i grammi del sostituto basati sulla porzione ottimizzata
                        substitute_grams = (portion_grams / 100.0) * substitute_data['grams']
                        
                        # Arrotonda i grammi del sostituto alla decina più vicina
                        substitute_grams_rounded = float(10 * np.floor(substitute_grams / 10 + 0.5))
                        
                        food_substitutes[substitute_name] = {
                            "grams": substitute_grams_rounded,
                            "similarity_score": float(substitute_data['similarity_score'])
                        }
                
                # Se non abbiamo trovato crackers o pan_bauletto nei sostituti esistenti,
                # calcoliamo manualmente basandoci sui rapporti calorici tipici
                if not food_substitutes:
                    # Rapporti approssimativi basati su valori calorici medi
                    # Pane bianco ~270 kcal/100g, Crackers ~430 kcal/100g, Pan bauletto ~285 kcal/100g
                    if normalized_food_name == "pane_bianco":
                        # Verifica se cracker è escluso
                        if not excluded_foods or "cracker" not in excluded_foods:
                            food_substitutes["cracker"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.63) / 10 + 0.5)),  # 270/430
                                "similarity_score": 90.0
                            }
                        # Verifica se pan_bauletto è escluso
                        if not excluded_foods or "pan_bauletto" not in excluded_foods:
                            food_substitutes["pan_bauletto"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.95) / 10 + 0.5)),  # 270/285
                                "similarity_score": 95.0
                            }
                    # Pane integrale ~235 kcal/100g
                    elif normalized_food_name == "pane_integrale":
                        # Verifica se cracker è escluso
                        if not excluded_foods or "cracker" not in excluded_foods:
                            food_substitutes["cracker"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.55) / 10 + 0.5)),  # 235/430
                                "similarity_score": 90.0
                            }
                        # Verifica se pan_bauletto è escluso
                        if not excluded_foods or "pan_bauletto" not in excluded_foods:
                            food_substitutes["pan_bauletto"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.82) / 10 + 0.5)),  # 235/285
                                "similarity_score": 95.0
                            }
            
            # Logica speciale per uova/albume durante colazione/spuntini
            elif is_colazione_or_spuntino and normalized_food_name in ["uova", "albume_uova"]:
                # Crea sostituti personalizzati per parmigiano e albume d'uovo
                # Cerca nel database le conversioni per uova -> parmigiano e uova -> albume
                
                uova_substitutes = substitutes_db.get(normalized_food_name, {})
                
                # Lista dei sostituti ammessi per colazione/spuntini
                allowed_substitutes = ["parmigiano", "parmigiano_reggiano", "grana_padano", "albume_uova", "albume"]
                
                for substitute_name, substitute_data in uova_substitutes.items():
                    # Verifica se il sostituto è tra quelli ammessi
                    if any(allowed in substitute_name.lower() for allowed in allowed_substitutes):
                        # Se abbiamo cibi esclusi, verifica che il sostituto non sia escluso
                        if excluded_foods:
                            substitute_canonical = db.alias.get(substitute_name.lower().replace("_", " "))
                            if not substitute_canonical:
                                substitute_canonical = substitute_name
                            
                            if substitute_canonical in excluded_foods:
                                continue  # Salta questo sostituto se è escluso
                        
                        # Calcola i grammi del sostituto basati sulla porzione ottimizzata
                        substitute_grams = (portion_grams / 100.0) * substitute_data['grams']
                        
                        # Arrotonda i grammi del sostituto alla decina più vicina
                        substitute_grams_rounded = float(10 * np.floor(substitute_grams / 10 + 0.5))
                        
                        food_substitutes[substitute_name] = {
                            "grams": substitute_grams_rounded,
                            "similarity_score": float(substitute_data['similarity_score'])
                        }
                
                # Se non abbiamo trovato parmigiano o albume nei sostituti esistenti,
                # calcoliamo manualmente basandoci sui rapporti calorici tipici
                if not food_substitutes:
                    # Rapporti approssimativi basati su valori calorici medi
                    # Uova ~155 kcal/100g, Parmigiano ~390 kcal/100g, Albume ~52 kcal/100g
                    if normalized_food_name == "uova":
                        # Verifica se parmigiano_reggiano è escluso
                        if not excluded_foods or "parmigiano_reggiano" not in excluded_foods:
                            food_substitutes["parmigiano_reggiano"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.40) / 10 + 0.5)),  # 155/390
                                "similarity_score": 85.0
                            }
                        # Verifica se albume_uova è escluso
                        if not excluded_foods or "albume_uova" not in excluded_foods:
                            food_substitutes["albume_uova"] = {
                                "grams": float(10 * np.floor((portion_grams * 3.0) / 10 + 0.5)),  # 155/52
                                "similarity_score": 90.0
                            }
                    # Albume d'uova ~52 kcal/100g
                    elif normalized_food_name == "albume_uova":
                        # Verifica se parmigiano_reggiano è escluso
                        if not excluded_foods or "parmigiano_reggiano" not in excluded_foods:
                            food_substitutes["parmigiano_reggiano"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.13) / 10 + 0.5)),  # 52/390
                                "similarity_score": 80.0
                            }
                        # Verifica se uova è escluso (per sostituire albume con uova intere)
                        if not excluded_foods or "uova" not in excluded_foods:
                            food_substitutes["uova"] = {
                                "grams": float(10 * np.floor((portion_grams * 0.34) / 10 + 0.5)),  # 52/155
                                "similarity_score": 95.0
                            }
            
            else:
                # Logica normale per tutti gli altri casi
                # Cerca i sostituti usando il nome principale mappato
                if normalized_food_name in substitutes_db:
                    available_substitutes = substitutes_db[normalized_food_name]
                    
                    # Se abbiamo cibi esclusi, filtriamo prima i sostituti
                    if excluded_foods:
                        filtered_substitutes = {}
                        for substitute_name, substitute_data in available_substitutes.items():
                            # Mappa il sostituto al nome canonico
                            substitute_canonical = db.alias.get(substitute_name.lower().replace("_", " "))
                            if not substitute_canonical:
                                substitute_canonical = substitute_name
                            
                            # Verifica che il sostituto non sia tra gli esclusi
                            if substitute_canonical not in excluded_foods:
                                filtered_substitutes[substitute_name] = substitute_data
                        
                        available_substitutes = filtered_substitutes
                    
                    # Ordina i sostituti per similarity_score (decrescente) e prendi i primi 2
                    sorted_substitutes = sorted(
                        available_substitutes.items(),
                        key=lambda x: x[1]['similarity_score'],
                        reverse=True
                    )[:2]
                    
                    for substitute_name, substitute_data in sorted_substitutes:
                        # Calcola i grammi del sostituto basati sulla porzione ottimizzata
                        # La formula è: grammi_sostituto = (porzione_originale / 100) * grammi_equivalenti_per_100g
                        substitute_grams = (portion_grams / 100.0) * substitute_data['grams']
                        
                        # Arrotonda i grammi del sostituto alla decina più vicina
                        substitute_grams_rounded = float(10 * np.floor(substitute_grams / 10 + 0.5))
                        
                        food_substitutes[substitute_name] = {
                            "grams": substitute_grams_rounded,
                            "similarity_score": float(substitute_data['similarity_score'])
                        }
            
            # Aggiungi i sostituti solo se ne abbiamo trovati
            if food_substitutes:
                result[food] = food_substitutes
        
        return result
        
    except Exception as e:
        logger.warning(f"Errore nel calcolo dei sostituti: {str(e)}")
        return {}


