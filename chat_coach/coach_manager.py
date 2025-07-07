"""
Coach Manager per la gestione delle conversazioni con il coach nutrizionale.

Gestisce l'interazione con OpenAI GPT-4o e l'esecuzione dei tool specializzati.
"""

import json
import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from openai import OpenAI

from services.token_cost_service import TokenCostTracker
from .coach_prompts import get_coach_system_prompt, get_coach_initial_prompt, COACH_TOOLS_DEFINITIONS
from .coach_tools import current_meal_query_tool, optimize_meal_portions

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoachManager:
    """Gestisce le conversazioni con il coach nutrizionale"""
    
    def __init__(self, openai_client, user_data_manager):
        self.client = openai_client
        self.user_data_manager = user_data_manager
        self.model = "gpt-4o"
        self.token_tracker = TokenCostTracker(model=self.model)
        
    def get_response(self, user_message: str, images: List[str] = None, 
                    conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Ottiene una risposta dal coach nutrizionale.
        
        Args:
            user_message: Messaggio dell'utente
            images: Lista di immagini in base64 (opzionale)
            conversation_history: Cronologia conversazione (opzionale)
            
        Returns:
            Dict con risposta e metadati
        """
        try:
            # Prepara i messaggi
            messages = []
            
            # Aggiungi il system prompt
            system_prompt = get_coach_system_prompt()
            messages.append({"role": "system", "content": system_prompt})
            
            # Se è la prima conversazione e non c'è cronologia, inizializza con il pasto corrente
            if not conversation_history:
                try:
                    # Ottieni informazioni del pasto corrente
                    current_meal_info = current_meal_query_tool()
                    if current_meal_info.get("success"):
                        # Aggiungi un messaggio iniziale con le informazioni del pasto
                        initial_prompt = get_coach_initial_prompt(current_meal_info)
                        messages.append({"role": "user", "content": initial_prompt})
                except Exception as e:
                    logger.warning(f"Impossibile pre-caricare informazioni pasto: {str(e)}")
            
            # Aggiungi la cronologia conversazione
            if conversation_history:
                messages.extend(conversation_history)
            
            # Prepara il messaggio utente
            user_msg_content = []
            user_msg_content.append({"type": "text", "text": user_message})
            
            # Aggiungi immagini se presenti
            if images:
                for image_data in images:
                    # Gestisci sia formato data URL che base64 puro
                    if image_data.startswith("data:"):
                        image_url = image_data
                    else:
                        image_url = f"data:image/jpeg;base64,{image_data}"
                    
                    user_msg_content.append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
            
            messages.append({"role": "user", "content": user_msg_content})
            
            # Prima chiamata all'API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=COACH_TOOLS_DEFINITIONS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4000
            )
            
            message = response.choices[0].message
            
            # Traccia i token
            self.token_tracker.track_tokens(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            
            # Se ci sono tool calls, eseguili
            if message.tool_calls:
                # Aggiungi il messaggio dell'assistente con tool calls
                messages.append(message)
                
                # Esegui tutti i tool calls
                tool_results = []
                for tool_call in message.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(result)
                    
                    # Aggiungi il risultato del tool
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                
                # Seconda chiamata per la risposta finale
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=4000
                )
                
                final_message = final_response.choices[0].message
                
                # Traccia i token della seconda chiamata
                self.token_tracker.track_tokens(
                    prompt_tokens=final_response.usage.prompt_tokens,
                    completion_tokens=final_response.usage.completion_tokens
                )
                
                return {
                    "success": True,
                    "content": final_message.content,
                    "tool_calls": message.tool_calls,
                    "tool_results": tool_results
                }
            
            return {
                "success": True,
                "content": message.content,
                "tool_calls": None,
                "tool_results": None
            }
            
        except Exception as e:
            logger.error(f"Errore nel coach manager: {str(e)}")
            return {
                "success": False,
                "content": f"Errore: {str(e)}",
                "tool_calls": None,
                "tool_results": None
            }
    
    def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Esegue un tool call"""
        try:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if function_name == "current_meal_query_tool":
                result = current_meal_query_tool(**arguments)
            elif function_name == "optimize_meal_portions":
                result = optimize_meal_portions(**arguments)
            else:
                result = {"error": f"Tool {function_name} non riconosciuto"}
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'esecuzione del tool {tool_call.function.name}: {str(e)}")
            return {"error": f"Errore nell'esecuzione del tool: {str(e)}"}
    
    def initialize_coach_conversation(self, user_info: Dict[str, Any]) -> str:
        """
        Inizializza una conversazione con il coach nutrizionale.
        Pre-carica le informazioni del pasto corrente.
        
        Args:
            user_info: Informazioni dell'utente
            
        Returns:
            Messaggio di benvenuto del coach con informazioni pasto corrente
        """
        try:
            # Crea un nuovo thread se non esiste
            if 'coach_thread_id' not in st.session_state:
                import time
                st.session_state.coach_thread_id = f"coach_thread_{int(time.time())}"
            
            # Messaggio di benvenuto semplice per l'utente
            return "🌟 **Ciao! Sono il tuo Coach Nutrizionale.** Mi occuperò di seguirti nel tuo percorso nutrizionale."
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione conversazione coach: {str(e)}")
            return "🌟 **Ciao! Sono il tuo Coach Nutrizionale.** Mi occuperò di seguirti nel tuo percorso nutrizionale."
            
    def get_current_meal_info(self) -> Dict[str, Any]:
        """
        Ottiene le informazioni del pasto corrente.
        Utile per debugging o per l'interfaccia utente.
        
        Returns:
            Dict con informazioni del pasto corrente
        """
        try:
            return current_meal_query_tool()
        except Exception as e:
            logger.error(f"Errore nel recupero informazioni pasto corrente: {str(e)}")
            return {"error": f"Errore: {str(e)}", "success": False} 