"""
Modulo per la gestione delle chiamate ai tool dell'agente nutrizionale.

Gestisce l'esecuzione delle funzioni richieste dall'agente AI,
inclusi tool per database nutrizionale e dati utente.
"""

import json
import streamlit as st
from agent_tools.nutridb_tool import (
    get_LARN_protein, get_LARN_fibre, 
    get_LARN_lipidi_percentuali, get_LARN_vitamine, 
    compute_Harris_Benedict_Equation, get_protein_multiplier,
    calculate_sport_expenditure, calculate_weight_goal_calories, 
    analyze_bmi_and_goals, 
    check_ultraprocessed_foods
)
from agent_tools.user_data_tool import (
    get_user_preferences, get_agent_qa, get_nutritional_info
)
from agent_tools.meal_optimization_tool import optimize_meal_portions
from agent_tools.weekly_diet_generator_tool import generate_6_additional_days


class ToolHandler:
    """Gestisce le chiamate ai tool dell'agente nutrizionale"""
    
    def __init__(self):
        """Inizializza il gestore dei tool"""
        self._setup_function_map()
    
    def _setup_function_map(self):
        """Configura la mappa delle funzioni disponibili"""
        self.function_map = {
            # Funzioni per accedere al database nutrizionale
            "get_LARN_protein": get_LARN_protein,
            "get_LARN_fibre": get_LARN_fibre,
            "get_LARN_lipidi_percentuali": get_LARN_lipidi_percentuali,
            "get_LARN_vitamine": get_LARN_vitamine,
            "compute_Harris_Benedict_Equation": compute_Harris_Benedict_Equation,
            "get_protein_multiplier": get_protein_multiplier,
            "calculate_sport_expenditure": calculate_sport_expenditure,
            "calculate_weight_goal_calories": calculate_weight_goal_calories,
            "analyze_bmi_and_goals": analyze_bmi_and_goals,
            "check_ultraprocessed_foods": check_ultraprocessed_foods,
            
            # Funzioni per accedere ai dati dell'utente
            "get_user_preferences": get_user_preferences,
            "get_agent_qa": get_agent_qa,
            "get_nutritional_info": get_nutritional_info,
            
            # Tool per ottimizzazione porzioni pasti
            "optimize_meal_portions": optimize_meal_portions,
            
            # Tool per generazione settimanale diete
            "generate_6_additional_days": generate_6_additional_days,
            
            # Per retrocompatibilità (da rimuovere in futuro)
            "nutridb_tool": lambda **args: self._legacy_nutridb_tool(**args),
            "user_data_tool": lambda **args: self._legacy_user_data_tool(**args)
        }
    
    def _legacy_nutridb_tool(self, **args):
        """Gestisce le chiamate legacy al nutridb_tool"""
        # Implementazione legacy per retrocompatibilità
        # Può essere rimossa quando non più necessaria
        st.warning("Uso di nutridb_tool legacy - aggiornare alla nuova API")
        return {"warning": "Legacy tool call"}
    
    def _legacy_user_data_tool(self, **args):
        """Gestisce le chiamate legacy al user_data_tool"""
        # Implementazione legacy per retrocompatibilità
        # Può essere rimossa quando non più necessaria
        st.warning("Uso di user_data_tool legacy - aggiornare alla nuova API")
        return {"warning": "Legacy tool call"}
    
    def handle_tool_calls(self, run_status):
        """
        Gestisce le chiamate ai tool dell'assistente.
        
        Args:
            run_status: Stato della run OpenAI che richiede azioni
            
        Returns:
            list: Lista di output dei tool per OpenAI
        """
        try:
            tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            
            for tool_call in tool_calls:
                try:
                    # Estrai i parametri della chiamata
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Esegui la funzione appropriata
                    if function_name in self.function_map:
                        result = self.function_map[function_name](**arguments)
                    else:
                        result = {"error": f"Tool {function_name} non supportato"}
                        st.error(f"Tool non supportato: {function_name}")
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result)
                    })
                    
                except Exception as e:
                    error_message = f"Errore nell'esecuzione del tool {tool_call.function.name}: {str(e)}"
                    st.error(error_message)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"error": str(e)})
                    })
            
            return tool_outputs
            
        except Exception as e:
            st.error(f"Errore nella gestione dei tool: {str(e)}")
            return None
    
    def get_available_functions(self):
        """
        Ottiene la lista delle funzioni disponibili.
        
        Returns:
            list: Lista dei nomi delle funzioni disponibili
        """
        return list(self.function_map.keys())
    
    def is_function_available(self, function_name: str) -> bool:
        """
        Verifica se una funzione è disponibile.
        
        Args:
            function_name: Nome della funzione da verificare
            
        Returns:
            bool: True se la funzione è disponibile
        """
        return function_name in self.function_map
    
    def execute_single_tool(self, function_name: str, **arguments):
        """
        Esegue un singolo tool direttamente.
        
        Args:
            function_name: Nome della funzione da eseguire
            **arguments: Argomenti per la funzione
            
        Returns:
            dict: Risultato dell'esecuzione
        """
        try:
            if function_name in self.function_map:
                return self.function_map[function_name](**arguments)
            else:
                return {"error": f"Tool {function_name} non supportato"}
        except Exception as e:
            return {"error": f"Errore nell'esecuzione: {str(e)}"}


# Funzione di utilità per mantenere compatibilità con app.py
def handle_tool_calls(run_status):
    """
    Funzione wrapper per compatibilità con app.py.
    
    Args:
        run_status: Stato della run OpenAI
        
    Returns:
        list: Output dei tool
    """
    tool_handler = ToolHandler()
    return tool_handler.handle_tool_calls(run_status) 