"""
Tool per il calcolo delle calorie e macronutrienti da un elenco di alimenti.

Questo tool calcola le calorie totali e i macronutrienti (proteine, carboidrati, grassi)
partendo da un elenco di alimenti con le relative quantità in grammi.
Funziona all'opposto di optimize_meal_portions.
"""

import os
import json
from typing import Dict, List, Any, Union
import logging

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


def calculate_kcal_from_foods(foods_with_grams: Union[List[Dict[str, Union[str, float]]], Dict[str, float]], 
                            user_id: str = None) -> Dict[str, Any]:
    """
    Calcola le calorie totali e i macronutrienti da un elenco di alimenti con le relative quantità.
    
    Questo tool fa l'opposto di optimize_meal_portions: invece di ottimizzare le porzioni
    per raggiungere dei target nutrizionali, calcola i valori nutrizionali effettivi
    di un pasto già definito con le sue porzioni.
    
    Args:
        foods_with_grams: Elenco di alimenti con grammature. Può essere:
                         - Lista di dict: [{"food": "pollo", "grams": 120}, {"food": "riso", "grams": 80}]
                         - Dict: {"pollo": 120, "riso": 80}
        user_id: ID dell'utente (opzionale, per compatibilità futura)
        
    Returns:
        Dict contenente:
        - success: bool se il calcolo è riuscito
        - total_nutrients: dict con totali nutrizionali (kcal, proteine_g, carboidrati_g, grassi_g)
        - foods_breakdown: dict con il contributo nutrizionale di ogni alimento
        - foods_not_found: lista degli alimenti non trovati nel database
        - error_message: messaggio di errore se fallisce (solo in caso di errore)
        
    Examples:
        >>> # Formato lista di dict
        >>> foods = [
        ...     {"food": "pollo_petto", "grams": 120},
        ...     {"food": "riso_integrale", "grams": 80},
        ...     {"food": "olio_oliva", "grams": 10}
        ... ]
        >>> result = calculate_kcal_from_foods(foods)
        >>> print(f"Calorie totali: {result['total_nutrients']['kcal']}")
        
        >>> # Formato dict
        >>> foods = {"pollo_petto": 120, "riso_integrale": 80, "olio_oliva": 10}
        >>> result = calculate_kcal_from_foods(foods)
        >>> print(f"Proteine totali: {result['total_nutrients']['proteine_g']}g")
    """
    try:
        # 1. Normalizza l'input in formato dict
        if isinstance(foods_with_grams, list):
            # Converti da formato lista a dict
            foods_dict = {}
            for item in foods_with_grams:
                if isinstance(item, dict) and "food" in item and "grams" in item:
                    foods_dict[item["food"]] = float(item["grams"])
                else:
                    return {
                        "success": False,
                        "error_message": f"Formato non valido per l'elemento: {item}. Atteso dict con 'food' e 'grams'",
                        "total_nutrients": {},
                        "foods_breakdown": {},
                        "foods_not_found": []
                    }
        elif isinstance(foods_with_grams, dict):
            # Già nel formato corretto
            foods_dict = {food: float(grams) for food, grams in foods_with_grams.items()}
        else:
            return {
                "success": False,
                "error_message": f"Formato input non supportato: {type(foods_with_grams)}. Atteso lista di dict o dict",
                "total_nutrients": {},
                "foods_breakdown": {},
                "foods_not_found": []
            }
        
        # 2. Verifica che ci siano alimenti da processare
        if not foods_dict:
            return {
                "success": False,
                "error_message": "Nessun alimento fornito",
                "total_nutrients": {},
                "foods_breakdown": {},
                "foods_not_found": []
            }
        
        # 3. Estrai la lista dei nomi degli alimenti
        food_names = list(foods_dict.keys())
        
        # 4. Verifica che tutti gli alimenti siano nel database
        all_found, foods_not_found = db.check_foods_in_db(food_names)
        
        # 5. Calcola i nutrienti per gli alimenti trovati
        foods_breakdown = {}
        total_nutrients = {
            "kcal": 0.0,
            "proteine_g": 0.0,
            "carboidrati_g": 0.0,
            "grassi_g": 0.0
        }
        
        for food_name, grams in foods_dict.items():
            if food_name not in foods_not_found:
                try:
                    # Ottieni i macronutrienti per 100g dell'alimento
                    macros_per_100g = db.get_macros(food_name, 100)
                    
                    # Verifica che i macronutrienti siano validi
                    if macros_per_100g is None:
                        logger.warning(f"Macronutrienti nulli per {food_name}")
                        if food_name not in foods_not_found:
                            foods_not_found.append(food_name)
                        continue
                    
                    # Calcola i nutrienti per la quantità specificata
                    food_nutrients = {
                        "kcal": float(macros_per_100g.get("energia_kcal", 0)) * grams / 100,
                        "proteine_g": float(macros_per_100g.get("proteine_g", 0)) * grams / 100,
                        "carboidrati_g": float(macros_per_100g.get("carboidrati_g", 0)) * grams / 100,
                        "grassi_g": float(macros_per_100g.get("grassi_g", 0)) * grams / 100
                    }
                    
                    # Verifica che i nutrienti calcolati siano validi
                    if any(value < 0 for value in food_nutrients.values()):
                        logger.warning(f"Valori nutrizionali negativi per {food_name}: {food_nutrients}")
                        if food_name not in foods_not_found:
                            foods_not_found.append(food_name)
                        continue
                    
                    # Aggiungi al breakdown solo se tutto è valido
                    foods_breakdown[food_name] = {
                        "grams": grams,
                        "nutrients": food_nutrients
                    }
                    
                    # Aggiungi ai totali
                    for nutrient in total_nutrients:
                        total_nutrients[nutrient] += food_nutrients[nutrient]
                        
                except Exception as e:
                    logger.warning(f"Errore nel calcolo nutrienti per {food_name}: {str(e)}")
                    # Aggiungi l'alimento alla lista di quelli non trovati se c'è un errore
                    if food_name not in foods_not_found:
                        foods_not_found.append(food_name)
        
        # 6. Arrotonda i risultati totali a 1 decimale
        for nutrient in total_nutrients:
            total_nutrients[nutrient] = round(total_nutrients[nutrient], 1)
        
        # 7. Arrotonda i risultati del breakdown a 1 decimale
        for food_data in foods_breakdown.values():
            for nutrient in food_data["nutrients"]:
                food_data["nutrients"][nutrient] = round(food_data["nutrients"][nutrient], 1)
        
        # 8. Determina il successo
        success = len(foods_breakdown) > 0
        
        # 9. Componi il messaggio di errore se necessario
        error_message = None
        if foods_not_found:
            error_message = f"Alimenti non trovati nel database: {', '.join(foods_not_found)}"
            if not success:
                error_message = f"Tutti gli alimenti non sono stati trovati nel database: {', '.join(foods_not_found)}"
        
        return {
            "success": success,
            "total_nutrients": total_nutrients,
            "foods_breakdown": foods_breakdown,
            "foods_not_found": foods_not_found,
            "error_message": error_message
        }
        
    except Exception as e:
        logger.error(f"Errore nel calcolo delle calorie dagli alimenti: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "total_nutrients": {},
            "foods_breakdown": {},
            "foods_not_found": []
        }


def calculate_meal_macros_percentage(total_nutrients: Dict[str, float]) -> Dict[str, float]:
    """
    Calcola le percentuali dei macronutrienti rispetto alle calorie totali.
    
    Args:
        total_nutrients: Dict con i nutrienti totali (output di calculate_kcal_from_foods)
        
    Returns:
        Dict con le percentuali di proteine, carboidrati e grassi
    """
    total_kcal = total_nutrients.get("kcal", 0)
    
    if total_kcal == 0:
        return {"proteine_pct": 0.0, "carboidrati_pct": 0.0, "grassi_pct": 0.0}
    
    # Calcola le kcal da ogni macronutriente
    protein_kcal = total_nutrients.get("proteine_g", 0) * 4  # 4 kcal/g
    carbs_kcal = total_nutrients.get("carboidrati_g", 0) * 4  # 4 kcal/g
    fat_kcal = total_nutrients.get("grassi_g", 0) * 9  # 9 kcal/g
    
    # Calcola le percentuali
    return {
        "proteine_pct": round((protein_kcal / total_kcal) * 100, 1),
        "carboidrati_pct": round((carbs_kcal / total_kcal) * 100, 1),
        "grassi_pct": round((fat_kcal / total_kcal) * 100, 1)
    }


def format_nutrition_summary(total_nutrients: Dict[str, float], 
                           foods_breakdown: Dict[str, Any]) -> str:
    """
    Formatta un riepilogo nutrizionale leggibile.
    
    Args:
        total_nutrients: Nutrienti totali
        foods_breakdown: Breakdown per singolo alimento
        
    Returns:
        Stringa formattata con il riepilogo nutrizionale
    """
    summary = f"""
RIEPILOGO NUTRIZIONALE:
- Calorie totali: {total_nutrients['kcal']:.1f} kcal
- Proteine: {total_nutrients['proteine_g']:.1f}g
- Carboidrati: {total_nutrients['carboidrati_g']:.1f}g  
- Grassi: {total_nutrients['grassi_g']:.1f}g

DETTAGLIO PER ALIMENTO:
"""
    
    for food_name, food_data in foods_breakdown.items():
        grams = food_data['grams']
        nutrients = food_data['nutrients']
        summary += f"• {food_name.replace('_', ' ').title()}: {grams}g\n"
        summary += f"  → {nutrients['kcal']:.1f} kcal, P:{nutrients['proteine_g']:.1f}g, C:{nutrients['carboidrati_g']:.1f}g, G:{nutrients['grassi_g']:.1f}g\n"
    
    # Aggiungi percentuali macronutrienti
    percentages = calculate_meal_macros_percentage(total_nutrients)
    summary += f"\nDISTRIBUZIONE MACRONUTRIENTI:\n"
    summary += f"- Proteine: {percentages['proteine_pct']:.1f}%\n"
    summary += f"- Carboidrati: {percentages['carboidrati_pct']:.1f}%\n"
    summary += f"- Grassi: {percentages['grassi_pct']:.1f}%\n"
    
    return summary 