"""
Tool per l'ottimizzazione delle porzioni di un pasto.

Questo tool calcola le porzioni ottimali di alimenti specificati
per un pasto in modo da rispettare i target nutrizionali del pasto.
"""

import os
import json
from typing import Dict, List, Any, Tuple
import logging
from scipy.optimize import minimize
import numpy as np

from .nutridb import NutriDB
from .nutridb_tool import get_user_id

# Configurazione logging
logging.basicConfig(level=logging.INFO)
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
    
    print(f"🔍 DEBUG load_user_meal_targets:")
    print(f"   📁 User ID: {user_id}")
    print(f"   🍽️  Meal name richiesto: '{meal_name}'")
    print(f"   📄 File path: {user_file_path}")
    
    if not os.path.exists(user_file_path):
        raise ValueError(f"File utente {user_id} non trovato.")
    
    with open(user_file_path, 'r', encoding='utf-8') as f:
        user_data = json.load(f)
    
    print(f"   ✅ File caricato con successo")
    
    nutritional_info = user_data.get("nutritional_info_extracted", {})
    daily_macros = nutritional_info.get("daily_macros", {})
    distribuzione_pasti = daily_macros.get("distribuzione_pasti", {})
    
    print(f"   📊 Pasti disponibili nel file: {list(distribuzione_pasti.keys())}")
    
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
    print(f"   🔤 Nome meal normalizzato: '{normalized_input}'")
    
    # Cerca prima nel mapping
    canonical_meal_name = meal_mappings.get(normalized_input)
    print(f"   🎯 Nome canonico dal mapping: '{canonical_meal_name}'")
    
    # Se non trovato nel mapping, prova una ricerca più flessibile
    if not canonical_meal_name:
        # Prova con parole chiave parziali
        input_words = normalized_input.replace("_", " ").split()
        print(f"   🔍 Ricerca flessibile con parole: {input_words}")
        
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
    
    print(f"   🎯 Nome canonico finale: '{canonical_meal_name}'")
    
    # Cerca il pasto nei dati utente
    meal_data = None
    
    # Prova prima con il nome canonico trovato
    if canonical_meal_name and canonical_meal_name in distribuzione_pasti:
        meal_data = distribuzione_pasti[canonical_meal_name]
        print(f"   ✅ Trovato con nome canonico: '{canonical_meal_name}'")
    
    # Se non trovato, prova con tutte le chiavi disponibili confrontando i nomi normalizzati
    if not meal_data:
        print(f"   🔍 Nome canonico non trovato, provo ricerca diretta...")
        for available_meal_key in distribuzione_pasti.keys():
            normalized_available = normalize_meal_name(available_meal_key)
            print(f"      Confronto '{normalized_input}' con '{normalized_available}' (chiave: '{available_meal_key}')")
            
            # Confronto diretto
            if normalized_available == normalized_input:
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                print(f"   ✅ Match diretto trovato: '{available_meal_key}'")
                break
            
            # Confronto parziale (se il nome input è contenuto nella chiave disponibile o viceversa)
            if (normalized_input in normalized_available or 
                normalized_available in normalized_input or
                # Confronto parole chiave
                any(word in normalized_available for word in normalized_input.split("_"))):
                meal_data = distribuzione_pasti[available_meal_key]
                canonical_meal_name = available_meal_key
                print(f"   ✅ Match parziale trovato: '{available_meal_key}'")
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
    
    print(f"   📊 Dati meal trovati: {meal_data}")
    
    result = {
        "kcal": float(meal_data.get("kcal", 0)),
        "proteine_g": float(meal_data.get("proteine_g", 0)),
        "carboidrati_g": float(meal_data.get("carboidrati_g", 0)),
        "grassi_g": float(meal_data.get("grassi_g", 0))
    }
    
    print(f"   🎯 Target finali restituiti:")
    print(f"      Calorie: {result['kcal']}")
    print(f"      Proteine: {result['proteine_g']}g")
    print(f"      Carboidrati: {result['carboidrati_g']}g")
    print(f"      Grassi: {result['grassi_g']}g")
    
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
                
                # Converte esplicitamente a float per evitare errori di tipo
                foods_nutrition[food] = {
                    "energia_kcal": float(macros.get("energia_kcal", 0)),
                    "proteine_g": float(macros.get("proteine_g", 0)),
                    "carboidrati_g": float(macros.get("carboidrati_g", 0)),
                    "grassi_g": float(macros.get("grassi_g", 0)),
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
        "proteine_animali": {"min": 50, "max": 300},
        "latte": {"min": 100, "max": 500},
        "affettati": {"min": 50, "max": 150},
        "formaggi": {"min": 30, "max": 300},
        "latticini": {"min": 100, "max": 300},  # Per yogurt e altri latticini
        "cereali": {"min": 60, "max": 150},
        "cereali_colazione": {"min": 20, "max": 60},
        "tuberi": {"min": 80, "max": 500},  # Aumentato max per patate
        "legumi": {"min": 40, "max": 200},
        "verdure": {"min": 50, "max": 400},
        "frutta": {"min": 80, "max": 300},
        "frutta_secca": {"min": 5, "max": 50},
        "grassi_aggiunti": {"min": 5, "max": 30},
        "uova": {"min": 50, "max": 200},  # ~1-2 uova
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


def optimize_meal_portions(meal_name: str, food_list: List[str], user_id: str = None) -> Dict[str, Any]:
    """
    Ottimizza automaticamente le porzioni degli alimenti per un pasto specifico.
    
    Verifica automaticamente che tutti gli alimenti siano presenti nel database,
    calcola le quantità in grammi per rispettare i target nutrizionali 
    dell'utente per quel pasto, e infine arrotonda le quantità alla decina
    più vicina (es. 118.7g diventa 120g).
    
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
        - macro_single_foods: dict con il contributo nutrizionale di ogni alimento
        - error_message: messaggio di errore se fallisce
        - optimization_summary: messaggio di riepilogo delle modifiche apportate
        - oil_added: bool se è stato aggiunto automaticamente l'olio
        - protein_added/protein_removed: bool per aggiustamenti proteici
        - carb_added/carb_substituted: bool per aggiustamenti dei carboidrati
        - carb_substitution_type: tipo di sostituzione effettuata (es: "pasta→riso")
        
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
                "foods_not_found": foods_not_found,
                "oil_added": False
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
        
        # 8. Step aggiuntivo: ottimizzazione proteine per pranzo/cena
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
        
        # 8.5. Step aggiuntivo: ottimizzazione carboidrati per pranzo/cena
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
        
        # 13. Prepara il messaggio di summary con tutte le ottimizzazioni
        summary_parts = [f"Ottimizzazione completata per {meal_name} con {len(final_food_list)} alimenti"]
        
        if oil_added:
            summary_parts.append(f"olio aggiunto automaticamente (miglioramento: {improvement:.1%})")
        
        if protein_added:
            summary_parts.append(f"{protein_adjustment_food} aggiunto per deficit proteico")
        elif protein_removed:
            summary_parts.append(f"{protein_adjustment_food} rimosso per eccesso proteico")
        
        if carb_added:
            summary_parts.append(f"{carb_adjustment_food} aggiunto per migliorare i carboidrati")
        elif carb_substituted:
            summary_parts.append(f"sostituzione {carb_substitution_type} per migliorare i carboidrati")
        
        summary_parts.append("Porzioni arrotondate alla decina più vicina")
        
        optimization_summary = ". ".join(summary_parts) + "."
        
        return {
            "success": True,
            "portions": optimized_portions_rounded,
            "target_nutrients": target_nutrients,
            "actual_nutrients": final_actual_nutrients_rounded,
            "errors": errors,
            "meal_name": meal_name,
            "foods_included": final_food_list,
            "oil_added": oil_added,
            "protein_added": protein_added,
            "protein_removed": protein_removed,
            "protein_adjustment_food": protein_adjustment_food,
            "carb_added": carb_added,
            "carb_substituted": carb_substituted,
            "carb_adjustment_food": carb_adjustment_food,
            "carb_substitution_type": carb_substitution_type,
            "optimization_summary": optimization_summary,
            "macro_single_foods": individual_contributions
        }
        
    except Exception as e:
        logger.error(f"Errore nell'ottimizzazione del pasto: {str(e)}")
        return {
            "success": False,
            "error_message": f"Errore nell'ottimizzazione: {str(e)}",
            "portions": {},
            "target_nutrients": {},
            "actual_nutrients": {},
            "oil_added": False
        }





