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
            st.session_state.thread_id = thread.id
            st.session_state.current_run_id = None
            
            # Mantieni la chat history e le risposte nutrizionali presenti nel file utente
            if hasattr(st.session_state, 'user_info') and st.session_state.user_info and "id" in st.session_state.user_info:
                user_id = st.session_state.user_info["id"]
                
                # Recupera le informazioni nutrizionali salvate dall'utente
                # Include: età, sesso, peso, altezza, attività, obiettivo, nutrition_answers, agent_qa
                nutritional_info = self.user_data_manager.get_nutritional_info(user_id)
                if nutritional_info and nutritional_info.nutrition_answers:
                    # Carica le risposte nutrizionali esistenti
                    st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                    st.session_state.current_question = len(NUTRITION_QUESTIONS)
                    st.success(f"🔄 Caricate {len(nutritional_info.nutrition_answers)} risposte nutrizionali precedenti")
                else:
                    # Se non ci sono risposte salvate, inizializza valori di default
                    st.session_state.current_question = st.session_state.get('current_question', 0)
                    st.session_state.nutrition_answers = st.session_state.get('nutrition_answers', {})
                
                # Recupera la chat history dell'utente
                chat_history = self.user_data_manager.get_chat_history(user_id)
                if chat_history:
                    # Se c'è una chat history e l'utente ha completato le domande nutrizionali,
                    # aggiungi l'initial prompt come primo messaggio
                    if nutritional_info and nutritional_info.nutrition_answers:
                        # Genera l'initial prompt con le informazioni dell'utente
                        initial_prompt = get_initial_prompt(
                            user_info=st.session_state.user_info,
                            nutrition_answers=st.session_state.nutrition_answers,
                            user_preferences=st.session_state.user_info.get('preferences', {})
                        )
                        
                        # Aggiungi l'initial prompt come primo messaggio
                        try:
                            self.openai_client.beta.threads.messages.create(
                                thread_id=st.session_state.thread_id,
                                role="user",
                                content=initial_prompt
                            )
                        except Exception as e:
                            st.warning(f"Impossibile aggiungere initial prompt al thread: {str(e)}")
                    
                    # Carica i messaggi esistenti nella session state
                    st.session_state.messages = [
                        {"role": msg.role, "content": msg.content}
                        for msg in chat_history
                    ]
                    
                    # Inserisci i messaggi esistenti nel nuovo thread OpenAI
                    for msg in chat_history:
                        try:
                            self.openai_client.beta.threads.messages.create(
                                thread_id=st.session_state.thread_id,
                                role=msg.role,
                                content=msg.content
                            )
                        except Exception as e:
                            st.warning(f"Impossibile aggiungere messaggio al thread: {str(e)}")
                else:
                    # Se non c'è history, inizializza array vuoto
                    st.session_state.messages = []
            else:
                # Se non c'è un utente loggato, inizializza array vuoto
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
            
            return thread.id
        except Exception as e:
            st.error(f"Errore nella creazione del thread: {str(e)}")
            return None
    
    def check_and_cancel_run(self):
        """Verifica se c'è una run attiva e la cancella se necessario."""
        if hasattr(st.session_state, 'current_run_id') and st.session_state.current_run_id:
            try:
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=st.session_state.current_run_id
                )
                if run.status in ['active', 'requires_action', 'failed', 'expired']:
                    self.openai_client.beta.threads.runs.cancel(
                        thread_id=st.session_state.thread_id,
                        run_id=st.session_state.current_run_id
                    )
            except Exception:
                pass
            finally:
                st.session_state.current_run_id = None
    
    def chat_with_assistant(self, user_input):
        """
        Gestisce la conversazione con l'assistente.
        
        Args:
            user_input: Messaggio dell'utente
            
        Returns:
            str: Risposta dell'assistente
        """
        try:
            # Se non esiste un thread, creane uno nuovo
            if not hasattr(st.session_state, 'thread_id'):
                self.create_new_thread()
            
            # Verifica e cancella eventuali run bloccate
            self.check_and_cancel_run()
            
            # Aggiungi il messaggio dell'utente al thread
            try:
                self.openai_client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_input
                )
            except Exception as e:
                # Se c'è un errore nel thread, creane uno nuovo e riprova
                self.create_new_thread()
                self.openai_client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_input
                )
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Crea una run
                    run = self.openai_client.beta.threads.runs.create(
                        thread_id=st.session_state.thread_id,
                        assistant_id=st.session_state.assistant.id
                    )
                    st.session_state.current_run_id = run.id
                    
                    # Attendi il completamento con timeout più lungo
                    start_time = time.time()
                    timeout = 180  # aumentato a 180 secondi (3 minuti)
                    
                    with st.empty():
                        while True:
                            if time.time() - start_time > timeout:
                                self.check_and_cancel_run()
                                self.create_new_thread()  # Crea un nuovo thread dopo il timeout
                                return "Mi dispiace, l'operazione è durata troppo a lungo. Per favore, riprova."
                            
                            try:
                                run_status = self.openai_client.beta.threads.runs.retrieve(
                                    thread_id=st.session_state.thread_id,
                                    run_id=run.id
                                )
                            except Exception:
                                self.check_and_cancel_run()
                                self.create_new_thread()
                                raise Exception("Errore nel recupero dello stato della run")
                            
                            if run_status.status == 'completed':
                                st.session_state.current_run_id = None
                                break
                            elif run_status.status in ['failed', 'expired', 'cancelled']:
                                self.check_and_cancel_run()
                                self.create_new_thread()
                                raise Exception(f"Run {run_status.status}")
                            elif run_status.status == 'requires_action':
                                # Gestisci le chiamate ai tool
                                tool_outputs = handle_tool_calls(run_status)
                                if tool_outputs:
                                    try:
                                        # Invia i risultati e continua
                                        self.openai_client.beta.threads.runs.submit_tool_outputs(
                                            thread_id=st.session_state.thread_id,
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
                            thread_id=st.session_state.thread_id
                        )
                        return messages.data[0].content[0].text.value
                    except Exception:
                        self.check_and_cancel_run()
                        self.create_new_thread()
                        raise Exception("Errore nel recupero dei messaggi")
                    
                except Exception as e:
                    retry_count += 1
                    self.check_and_cancel_run()
                    if retry_count >= max_retries:
                        self.create_new_thread()  # Crea un nuovo thread dopo troppi tentativi falliti
                        st.error(f"Errore dopo {max_retries} tentativi: {str(e)}")
                        return "Mi dispiace, si è verificato un errore. Riprova."
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
        except Exception as e:
            self.check_and_cancel_run()
            self.create_new_thread()  # Crea un nuovo thread dopo un errore generale
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