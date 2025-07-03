"""
Modulo per la gestione delle conversazioni chat.

Gestisce i thread OpenAI, le run dell'assistente e il flusso completo 
delle conversazioni con retry logic e gestione degli errori.
"""

import streamlit as st
import time
from agent.tool_handler import handle_tool_calls
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from agent.prompts import get_initial_prompt

# Import del nuovo state manager
from services.state_service import app_state


class ChatManager:
    """Gestisce le conversazioni chat con l'assistente"""
    
    def __init__(self, openai_client, user_data_manager):
        """
        Inizializza il gestore della chat.
        
        Args:
            openai_client: Client OpenAI configurato
            user_data_manager: Gestore dei dati utente
        """
        self.openai_client = openai_client
        self.user_data_manager = user_data_manager
    
    def create_new_thread(self):
        """
        Crea un nuovo thread per la conversazione, mantenendo la chat history e le risposte nutrizionali dell'utente.
        
        Carica dal file utente:
        - Chat history (messaggi precedenti)
        - Nutritional info (età, sesso, peso, altezza, attività, obiettivo, nutrition_answers, agent_qa)
        
        Returns:
            str: ID del thread creato o None in caso di errore
        """
        try:
            thread = self.openai_client.beta.threads.create()
            app_state.set_thread_id(thread.id)
            app_state.set_current_run_id(None)
            
            # Mantieni la chat history e le risposte nutrizionali presenti nel file utente
            user_info = app_state.get_user_info()
            if user_info and user_info.id:
                user_id = user_info.id
                
                # Recupera le informazioni nutrizionali salvate dall'utente
                # Include: età, sesso, peso, altezza, attività, obiettivo, nutrition_answers, agent_qa
                nutritional_info = self.user_data_manager.get_nutritional_info(user_id)
                if nutritional_info and nutritional_info.nutrition_answers:
                    # Carica le risposte nutrizionali esistenti
                    app_state.set_nutrition_answers(nutritional_info.nutrition_answers)
                    app_state.set_current_question(len(NUTRITION_QUESTIONS))
                else:
                    # Se non ci sono risposte salvate, inizializza valori di default
                    app_state.set_current_question(app_state.get_current_question() or 0)
                    app_state.set_nutrition_answers(app_state.get_nutrition_answers() or {})
                
                # Recupera la chat history dell'utente
                chat_history = self.user_data_manager.get_chat_history(user_id)
                if chat_history:
                    # Se c'è una chat history e l'utente ha completato le domande nutrizionali,
                    # aggiungi l'initial prompt come primo messaggio
                    if nutritional_info and nutritional_info.nutrition_answers:
                        # Genera l'initial prompt con le informazioni dell'utente
                        initial_prompt = get_initial_prompt(
                            user_info=user_info.__dict__ if user_info else {},
                            nutrition_answers=app_state.get_nutrition_answers(),
                            user_preferences=user_info.preferences if user_info and user_info.preferences else {}
                        )
                        
                        # Aggiungi l'initial prompt come primo messaggio
                        try:
                            self.openai_client.beta.threads.messages.create(
                                thread_id=thread.id,
                                role="assistant",
                                content=initial_prompt
                            )
                        except Exception as e:
                            st.warning(f"Impossibile aggiungere initial prompt al thread: {str(e)}")
                    
                    # Carica i messaggi esistenti nella session state
                    app_state.set_messages([
                        {"role": msg.role, "content": msg.content}
                        for msg in chat_history
                    ])
                    
                    # Inserisci i messaggi esistenti nel nuovo thread OpenAI
                    for msg in chat_history:
                        try:
                            self.openai_client.beta.threads.messages.create(
                                thread_id=thread.id,
                                role=msg.role,
                                content=msg.content
                            )
                        except Exception as e:
                            st.warning(f"Impossibile aggiungere messaggio al thread: {str(e)}")
                else:
                    # Se non c'è history, inizializza array vuoto
                    app_state.set_messages([])
            else:
                # Se non c'è un utente loggato, inizializza array vuoto
                app_state.set_messages([])
                app_state.set_current_question(0)
                app_state.set_nutrition_answers({})
            
            # # Salva le informazioni del thread
            # if user_id:
            #     self.user_data_manager.save_chat_history(
            #         user_id,
            #         thread_id=thread.id,
            #         messages=app_state.get_messages()
            #     )
            
            return thread.id
        except Exception as e:
            st.error(f"Errore nella creazione del thread: {str(e)}")
            return None
    
    def clear_conversation(self):
        """Pulisce la conversazione corrente"""
        app_state.clear_messages()
        app_state.set_current_question(0)
        app_state.set_nutrition_answers({})
    
    def check_and_cancel_run(self):
        """Controlla e annulla eventuali run in corso"""
        current_run_id = app_state.get_current_run_id()
        thread_id = app_state.get_thread_id()
        
        if current_run_id and thread_id:
            try:
                # Controlla lo stato del run
                run_status = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=current_run_id
                )
                
                # Se il run è ancora in corso, prova ad annullarlo
                if run_status.status in ["queued", "in_progress", "cancelling"]:
                    self.openai_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=current_run_id
                    )
                    
                # Pulisci il run ID corrente
                app_state.set_current_run_id(None)
                
            except Exception as e:
                print(f"Errore durante l'annullamento del run: {e}")
                app_state.set_current_run_id(None)
    
    def chat_with_assistant(self, user_message):
        """
        Invia un messaggio all'assistente e gestisce la risposta.
        
        Args:
            user_message: Messaggio dell'utente
            
        Returns:
            str: Risposta dell'assistente
        """
        thread_id = app_state.get_thread_id()
        
        # Se non esiste un thread, crealo automaticamente
        if not thread_id:
            st.info("🔄 Creazione nuovo thread di conversazione...")
            thread_id = self.create_new_thread()
            if not thread_id:
                st.error("❌ Impossibile creare un thread di conversazione")
                return None
        
        # Controlla se c'è un prompt delle preferenze da aggiungere
        preferences_prompt = app_state.get_preferences_prompt()
        prompt_to_add = app_state.get_prompt_to_add_at_next_message()
        
        if prompt_to_add and preferences_prompt:
            # Aggiungi il prompt delle preferenze al messaggio
            user_message = f"{preferences_prompt}\n\n{user_message}"
            # Pulisci i flag
            app_state.delete_prompt_to_add_at_next_message()
            app_state.delete_preferences_prompt()
        
        # Invia il messaggio dell'utente
        self.openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Ottieni l'assistente dall'app_state
        assistant_manager = app_state.get_assistant_manager()
        if not assistant_manager:
            st.error("Errore: Assistente non disponibile")
            return None
        
        assistant = assistant_manager.get_assistant()
        
        # Crea ed esegui il run
        run = self.openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id
        )
        app_state.set_current_run_id(run.id)
        
        # Aspetta che il run sia completato (con gestione dei tool calls)
        while True:
            run_status = self.openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                # Gestisci le chiamate ai tool
                tool_outputs = handle_tool_calls(run_status)
                
                # Invia i risultati dei tool se disponibili
                if tool_outputs:
                    self.openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            elif run_status.status in ["failed", "cancelled", "expired"]:
                app_state.set_current_run_id(None)
                return f"❌ Errore nella generazione della risposta: {run_status.status}"
            else:
                # Aspetta un momento prima di controllare di nuovo
                time.sleep(1)
        
        # Pulisci il run ID
        app_state.set_current_run_id(None)
        
        # Ottieni i messaggi dal thread
        messages = self.openai_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc"
        )
        
        # Trova l'ultimo messaggio dell'assistente
        for message in reversed(messages.data):
            if message.role == "assistant":
                response_content = ""
                for content_part in message.content:
                    if hasattr(content_part, 'text'):
                        response_content += content_part.text.value
                
                return response_content
        
        return "❌ Nessuna risposta ricevuta dall'assistente"


def create_new_thread(openai_client, user_data_manager):
    """
    Funzione di convenienza per creare un nuovo thread.
    
    Args:
        openai_client: Client OpenAI configurato
        user_data_manager: Gestore dei dati utente
        
    Returns:
        str: ID del thread creato
    """
    manager = ChatManager(openai_client, user_data_manager)
    return manager.create_new_thread()


def check_and_cancel_run(openai_client):
    """
    Funzione di convenienza per verificare e cancellare run attive.
    
    Args:
        openai_client: Client OpenAI configurato
    """
    manager = ChatManager(openai_client, None)
    manager.check_and_cancel_run()


def chat_with_assistant(user_input, openai_client, user_data_manager):
    """
    Funzione di convenienza per gestire la chat con l'assistente.
    
    Args:
        user_input: Messaggio dell'utente
        openai_client: Client OpenAI configurato
        user_data_manager: Gestore dei dati utente
        
    Returns:
        str: Risposta dell'assistente
    """
    manager = ChatManager(openai_client, user_data_manager)
    return manager.chat_with_assistant(user_input) 