from typing import Dict, List, Optional, Union
from .user_data_manager import UserDataManager

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
            # No need to convert to list since they are already lists
            return {
                "excluded_foods": prefs.get("excluded_foods", []),
                "preferred_foods": prefs.get("preferred_foods", []),
                "user_notes": prefs.get("user_notes", [])
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