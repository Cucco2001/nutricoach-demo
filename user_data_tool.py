from typing import Dict, List, Optional, Union
from user_data_manager import UserDataManager

# Singleton instance of UserDataManager
_user_data_manager = UserDataManager()

def user_data_tool(function_name: str, parameters: Dict) -> Dict:
    """
    Tool per accedere ai dati dell'utente (preferenze, progressi, feedback)
    
    Args:
        function_name: Nome della funzione da chiamare
        parameters: Parametri per la funzione
    
    Returns:
        Dict con i risultati della funzione chiamata
    """
    try:
        if function_name == "get_user_preferences":
            user_id = parameters["user_id"]
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

        elif function_name == "get_progress_history":
            user_id = parameters["user_id"]
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

        elif function_name == "get_meal_feedback":
            user_id = parameters["user_id"]
            meal_id = parameters["meal_id"]
            feedback = _user_data_manager.get_meal_feedback(user_id, meal_id)
            if feedback:
                return {
                    "satisfaction_level": feedback.satisfaction_level,
                    "notes": feedback.notes,
                    "timestamp": feedback.timestamp
                }
            return {"error": "Nessun feedback trovato per questo pasto"}
            
        elif function_name == "get_agent_qa":
            user_id = parameters["user_id"]
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
            
        elif function_name == "get_nutritional_info":
            user_id = parameters["user_id"]
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

        else:
            return {"error": f"Funzione {function_name} non supportata"}

    except Exception as e:
        return {"error": str(e)} 