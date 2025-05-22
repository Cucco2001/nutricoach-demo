from typing import Dict, List, Optional, Union
from user_data_manager import UserDataManager

# Singleton instance of UserDataManager
_user_data_manager = UserDataManager()

def get_user_preferences(user_id: str) -> Dict:
    """
    Ottiene le preferenze dell'utente.
    
    Args:
        user_id: ID dell'utente
    
    Returns:
        Dict con le preferenze dell'utente
    """
    try:
        prefs = _user_data_manager.get_user_preferences(user_id)
        if prefs:
            return {
                "excluded_foods": list(prefs.excluded_foods),
                "preferred_foods": list(prefs.preferred_foods),
                "meal_times": prefs.meal_times,
                "portion_sizes": prefs.portion_sizes,
                "cooking_methods": list(prefs.cooking_methods)
            }
        return {"error": "Nessuna preferenza trovata per questo utente"}
    except Exception as e:
        return {"error": str(e)}

def get_progress_history(user_id: str) -> Dict:
    """
    Ottiene la storia dei progressi dell'utente.
    
    Args:
        user_id: ID dell'utente
    
    Returns:
        Dict con la storia dei progressi
    """
    try:
        history = _user_data_manager.get_progress_history(user_id)
        if history:
            return {
                "progress": [
                    {
                        "date": entry.date,
                        "weight": entry.weight,
                        "measurements": entry.measurements
                    }
                    for entry in history
                ]
            }
        return {"error": "Nessun dato di progresso trovato per questo utente"}
    except Exception as e:
        return {"error": str(e)}

def get_meal_feedback(user_id: str, meal_id: str) -> Dict:
    """
    Ottiene il feedback dell'utente per un pasto specifico.
    
    Args:
        user_id: ID dell'utente
        meal_id: ID del pasto
    
    Returns:
        Dict con il feedback dell'utente
    """
    try:
        feedback = _user_data_manager.get_meal_feedback(user_id, meal_id)
        if feedback:
            return {
                "satisfaction_level": feedback.satisfaction_level,
                "notes": feedback.notes,
                "timestamp": feedback.timestamp
            }
        return {"error": "Nessun feedback trovato per questo pasto"}
    except Exception as e:
        return {"error": str(e)}

def get_agent_qa(user_id: str) -> Dict:
    """
    Ottiene la storia delle domande e risposte dell'agente.
    
    Args:
        user_id: ID dell'utente
    
    Returns:
        Dict con la storia delle domande e risposte
    """
    try:
        qa_history = _user_data_manager.get_agent_qa(user_id)
        if qa_history:
            return {
                "qa_history": [
                    {
                        "question": qa.question,
                        "answer": qa.answer,
                        "timestamp": qa.timestamp
                    }
                    for qa in qa_history
                ]
            }
        return {"error": "Nessuna interazione question/answer trovata per questo utente"}
    except Exception as e:
        return {"error": str(e)}

def get_nutritional_info(user_id: str) -> Dict:
    """
    Ottiene le informazioni nutrizionali dell'utente.
    
    Args:
        user_id: ID dell'utente
    
    Returns:
        Dict con le informazioni nutrizionali
    """
    try:
        nutritional_info = _user_data_manager.get_nutritional_info(user_id)
        if nutritional_info:
            return {
                "età": nutritional_info.età,
                "sesso": nutritional_info.sesso,
                "peso": nutritional_info.peso,
                "altezza": nutritional_info.altezza,
                "attività": nutritional_info.attività,
                "obiettivo": nutritional_info.obiettivo,
                "nutrition_answers": nutritional_info.nutrition_answers
            }
        return {"error": "Nessuna informazione nutrizionale trovata per questo utente"}
    except Exception as e:
        return {"error": str(e)} 