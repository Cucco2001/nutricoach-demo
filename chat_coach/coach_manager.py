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
from .coach_prompts import get_coach_system_prompt, COACH_TOOLS_DEFINITIONS
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
            
            # Chiamata a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=COACH_TOOLS_DEFINITIONS,
                tool_choice="auto",
                max_tokens=4000,
                temperature=0.7
            )
            
            # Estrai la risposta
            message = response.choices[0].message
            
            # Traccia i token
            self.token_tracker.track_message("assistant", message.content or "")
            
            # Gestisci tool calls
            if message.tool_calls:
                tool_results = []
                for tool_call in message.tool_calls:
                    result = self._execute_tool_call(tool_call)
                    tool_results.append(result)
                
                # Aggiungi il messaggio con tool calls
                messages.append(message)
                
                # Aggiungi i risultati dei tool
                for i, tool_call in enumerate(message.tool_calls):
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_results[i], ensure_ascii=False),
                        "tool_call_id": tool_call.id
                    })
                
                # Seconda chiamata per la risposta finale
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.7
                )
                
                final_message = final_response.choices[0].message
                
                # Traccia i token della seconda chiamata
                self.token_tracker.track_message("assistant", final_message.content or "")
                
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
        
        Args:
            user_info: Informazioni dell'utente
            
        Returns:
            Messaggio di benvenuto del coach
        """
        try:
            # Crea un nuovo thread se non esiste
            if 'coach_thread_id' not in st.session_state:
                # Per ora usiamo un ID semplice, in futuro potremmo usare OpenAI Assistants API
                import time
                st.session_state.coach_thread_id = f"coach_thread_{int(time.time())}"
            
            # Messaggio di benvenuto personalizzato
            welcome_message = f"""🌟 **Ciao! Sono il tuo Coach Nutrizionale personale!** Dimmi pure cosa hai in mente! 😊"""
            
            return welcome_message
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione conversazione coach: {str(e)}")
            return "Ciao! Sono il tuo Coach Nutrizionale. Come posso aiutarti oggi?"
    
    def chat_with_coach(self, user_message: str, thread_id: str, images: List[str] = None) -> str:
        """
        Gestisce una conversazione con il coach nutrizionale.
        
        Args:
            user_message: Messaggio dell'utente
            thread_id: ID del thread di conversazione
            images: Lista di immagini in base64 (opzionale)
            
        Returns:
            Risposta del coach
        """
        try:
            # Recupera la cronologia della conversazione dalla sessione
            conversation_history = []
            if hasattr(st.session_state, 'coach_messages'):
                # Converti i messaggi in formato OpenAI
                for msg in st.session_state.coach_messages:
                    if msg["role"] in ["user", "assistant"]:
                        if msg["role"] == "user":
                            # Gestisci messaggi utente con possibili immagini
                            content = [{"type": "text", "text": msg["content"]}]
                            if "images" in msg and msg["images"]:
                                for image_data in msg["images"]:
                                    content.append({
                                        "type": "image_url",
                                        "image_url": {"url": image_data}
                                    })
                            conversation_history.append({"role": "user", "content": content})
                        else:
                            conversation_history.append({"role": "assistant", "content": msg["content"]})
            
            # Prepara il messaggio corrente dell'utente
            current_message_content = [{"type": "text", "text": user_message}]
            
            # Aggiungi immagini se presenti
            if images:
                for image_data in images:
                    current_message_content.append({
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    })
            
            # Traccia il messaggio dell'utente
            self.token_tracker.track_message("user", user_message)
            
            # Usa il metodo get_response esistente
            result = self.get_response(
                user_message=user_message,
                images=images,  # Passa la lista di immagini
                conversation_history=conversation_history
            )
            
            if result.get("success"):
                return result["content"]
            else:
                return "Mi dispiace, ho avuto un problema nel processare la tua richiesta. Puoi riprovare?"
                
        except Exception as e:
            logger.error(f"Errore nella chat con il coach: {str(e)}")
            return "Mi dispiace, ho avuto un problema tecnico. Puoi riprovare?"

    def get_token_stats(self) -> Dict[str, Any]:
        """Restituisce le statistiche sui token"""
        return self.token_tracker.get_conversation_stats() 