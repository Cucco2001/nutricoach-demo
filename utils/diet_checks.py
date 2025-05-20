import json
from typing import Dict, List, Tuple

def load_food_database() -> Dict:
    with open('Dati_processed/banca_alimenti_crea_60alimenti.json', 'r') as f:
        return json.load(f)

def check_ultraprocessed_ratio(daily_diet: List[Tuple[str, float]], max_ratio: float = 0.20) -> Tuple[bool, float]:
    """
    Check if the ratio of ultra-processed foods (NOVA group 4) in the daily diet is within acceptable limits.
    
    Args:
        daily_diet: List of tuples containing (food_name, grams)
        max_ratio: Maximum acceptable ratio of ultra-processed foods (default: 0.20 or 20%)
    
    Returns:
        Tuple containing:
        - bool: True if the ratio is acceptable, False otherwise
        - float: The actual ratio of ultra-processed foods
    """
    food_db = load_food_database()
    
    total_grams = 0
    ultraprocessed_grams = 0
    
    for food_name, grams in daily_diet:
        if food_name not in food_db:
            raise ValueError(f"Food '{food_name}' not found in database")
        
        total_grams += grams
        if food_db[food_name]['nova_group'] == 4:
            ultraprocessed_grams += grams
    
    if total_grams == 0:
        return True, 0.0
    
    ratio = ultraprocessed_grams / total_grams
    return ratio <= max_ratio, ratio

def format_ultraprocessed_check_result(daily_diet: List[Tuple[str, float]]) -> str:
    """
    Format the results of the ultra-processed foods check in a human-readable way.
    
    Args:
        daily_diet: List of tuples containing (food_name, grams)
    
    Returns:
        str: Formatted message with the check results
    """
    is_acceptable, ratio = check_ultraprocessed_ratio(daily_diet)
    percentage = ratio * 100
    
    if is_acceptable:
        status = "ACCETTABILE"
    else:
        status = "NON ACCETTABILE"
    
    message = f"""
Controllo alimenti ultra-processati:
- Percentuale cibi ultra-processati: {percentage:.1f}%
- Stato: {status}
"""
    return message.strip()

def validate_diet_plan(diet_plan: Dict[str, List[Tuple[str, float]]]) -> Tuple[bool, str]:
    """
    Validate the entire diet plan, including the ultra-processed foods check.
    
    Args:
        diet_plan: Dictionary with meal IDs as keys and lists of (food_name, grams) tuples as values
    
    Returns:
        Tuple containing:
        - bool: True if the diet plan is valid, False otherwise
        - str: Message explaining the validation results
    """
    validation_messages = []
    is_valid = True
    
    # Check each meal in the diet plan
    for meal_id, meal_foods in diet_plan.items():
        try:
            is_acceptable, ratio = check_ultraprocessed_ratio(meal_foods)
            percentage = ratio * 100
            
            meal_message = f"\nPasto {meal_id}:"
            meal_message += f"\n- Percentuale cibi ultra-processati: {percentage:.1f}%"
            meal_message += f"\n- Stato: {'ACCETTABILE' if is_acceptable else 'NON ACCETTABILE'}"
            
            validation_messages.append(meal_message)
            
            if not is_acceptable:
                is_valid = False
                
        except ValueError as e:
            validation_messages.append(f"\nErrore nel pasto {meal_id}: {str(e)}")
            is_valid = False
    
    # Create the final message
    if is_valid:
        message = "✓ Validazione completata con successo!"
    else:
        message = "✗ La dieta contiene troppi alimenti ultra-processati in alcuni pasti."
    
    message += "\n\nDettaglio per pasto:"
    message += "".join(validation_messages)
    
    return is_valid, message

def check_ultraprocessed_diet(diet_plan: dict) -> dict:
    """
    Valida solo la percentuale di alimenti ultra-processati (NOVA 4) nel diet plan.
    Args:
        diet_plan: dict {meal_id: [(food_name, grams), ...], ...}
    Returns:
        dict: {"is_valid": bool, "message": str}
    """
    from utils.diet_checks import validate_diet_plan
    is_valid, message = validate_diet_plan(diet_plan)
    return {"is_valid": is_valid, "message": message} 