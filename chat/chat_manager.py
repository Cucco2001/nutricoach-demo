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
                                role="user",
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
                if run_status.status in ["queued", "in_progress", "cancelling", "active", "requires_action", "failed", "expired"]:
                    self.openai_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=current_run_id
                    )
                    
            except Exception as e:
                print(f"Errore durante l'annullamento del run: {e}")
            finally:
                # Pulisci sempre il run ID corrente
                app_state.set_current_run_id(None)
    
    def chat_with_assistant(self, user_message):
        """
        Gestisce la conversazione con l'assistente.
        
        Args:
            user_message: Messaggio dell'utente
            
        Returns:
            str: Risposta dell'assistente
        """
        try:
            thread_id = app_state.get_thread_id()
            
            # Se non esiste un thread, creane uno nuovo
            if not thread_id:
                thread_id = self.create_new_thread()
                if not thread_id:
                    st.error("❌ Impossibile creare un thread di conversazione")
                    return None
            
            # Verifica e cancella eventuali run bloccate
            self.check_and_cancel_run()
            
            # Controlla se è necessario aggiungere il prompt delle preferenze
            preferences_prompt = app_state.get_preferences_prompt()
            prompt_to_add = app_state.get_prompt_to_add_at_next_message()
            
            if prompt_to_add and preferences_prompt:
                user_message = f"{preferences_prompt}. {user_message}"
                # Resetta i flag
                app_state.delete_prompt_to_add_at_next_message()
                app_state.delete_preferences_prompt()

            # Aggiungi il messaggio dell'utente al thread
            try:
                self.openai_client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=user_message
                )
            except Exception as e:
                # Se c'è un errore nel thread, creane uno nuovo e riprova
                st.info("🔄 Errore thread, creazione nuovo thread...")
                thread_id = self.create_new_thread()
                if not thread_id:
                    return "❌ Impossibile creare nuovo thread"
                self.openai_client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=user_message
                )
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Ottieni l'assistente dall'app_state
                    assistant_manager = app_state.get_assistant_manager()
                    if not assistant_manager:
                        st.error("Errore: Assistente non disponibile")
                        return None
                    assistant = assistant_manager.get_assistant()
                    
                    # Crea una run
                    run = self.openai_client.beta.threads.runs.create(
                        thread_id=thread_id,
                        assistant_id=assistant.id
                    )
                    app_state.set_current_run_id(run.id)
                    
                    # Attendi il completamento con timeout
                    start_time = time.time()
                    timeout = 180  # 3 minuti
                    
                    while True:
                        if time.time() - start_time > timeout:
                            self.check_and_cancel_run()
                            st.info("🔄 Timeout, creazione nuovo thread...")
                            self.create_new_thread()
                            return "Mi dispiace, l'operazione è durata troppo a lungo. Per favore, riprova."
                        
                        try:
                            run_status = self.openai_client.beta.threads.runs.retrieve(
                                thread_id=thread_id,
                                run_id=run.id
                            )
                        except Exception:
                            self.check_and_cancel_run()
                            self.create_new_thread()
                            raise Exception("Errore nel recupero dello stato della run")
                        
                        if run_status.status == 'completed':
                            app_state.set_current_run_id(None)
                            break
                        elif run_status.status in ['failed', 'expired', 'cancelled']:
                            self.check_and_cancel_run()
                            st.info("🔄 Run fallita, creazione nuovo thread...")
                            self.create_new_thread()
                            raise Exception(f"Run {run_status.status}")
                        elif run_status.status == 'requires_action':
                            # Gestisci le chiamate ai tool
                            tool_outputs = handle_tool_calls(run_status)
                            if tool_outputs:
                                try:
                                    self.openai_client.beta.threads.runs.submit_tool_outputs(
                                        thread_id=thread_id,
                                        run_id=run.id,
                                        tool_outputs=tool_outputs
                                    )
                                except Exception:
                                    self.check_and_cancel_run()
                                    self.create_new_thread()
                                    raise Exception("Errore nell'invio dei risultati dei tool")
                            else:
                                self.check_and_cancel_run()
                                self.create_new_thread()
                                raise Exception("Errore nella gestione dei tool")
                        
                        # Breve pausa prima del prossimo controllo
                        time.sleep(1)
                    
                    # Ottieni la risposta
                    try:
                        messages = self.openai_client.beta.threads.messages.list(
                            thread_id=thread_id,
                            order="desc",  # Ordine decrescente per avere i più recenti per primi
                        )
                        # Trova l'ultimo messaggio dell'assistente (il primo nella lista desc)
                        for message in messages.data:
                            if message.role == "assistant":
                                response_content = ""
                                for content_part in message.content:
                                    if hasattr(content_part, 'text'):
                                        response_content += content_part.text.value
                                return response_content
                        return "❌ Nessuna risposta ricevuta dall'assistente"
                    except Exception:
                        self.check_and_cancel_run()
                        self.create_new_thread()
                        raise Exception("Errore nel recupero dei messaggi")
                    
                except Exception as e:
                    retry_count += 1
                    self.check_and_cancel_run()
                    if retry_count >= max_retries:
                        st.info("🔄 Troppi tentativi falliti, creazione nuovo thread...")
                        self.create_new_thread()
                        st.error(f"Errore dopo {max_retries} tentativi: {str(e)}")
                        return "Mi dispiace, si è verificato un errore. Riprova."
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
        except Exception as e:
            self.check_and_cancel_run()
            st.info("🔄 Errore generale, creazione nuovo thread...")
            self.create_new_thread()
            st.error(f"Errore nella conversazione: {str(e)}")
            return "Mi dispiace, si è verificato un errore inaspettato. Riprova."


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