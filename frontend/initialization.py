"""
Modulo per l'inizializzazione di tutte le variabili di sessione e servizi dell'applicazione.

Centralizza tutte le inizializzazioni in una singola funzione per mantenere
il codice organizzato e facilitare la manutenzione.
"""

import streamlit as st
import os
import threading
import queue
from openai import OpenAI
from dotenv import load_dotenv

# Import dei manager e servizi (evitando importazioni circolari)
from agent_tools.user_data_manager import UserDataManager
from services.deep_seek_service import DeepSeekManager
from services.preferences_service import PreferencesManager

# Import del nuovo state manager
from services.state_service import app_state

# Import del device detector
from frontend.device_detector import detect_device_type


def initialize_app():
    """
    Inizializza tutte le variabili di sessione e i servizi dell'applicazione.
    
    Questa funzione deve essere chiamata all'inizio dell'app per configurare
    tutti i componenti necessari al funzionamento.
    """
    # Protezione contro errori di inizializzazione della sessione
    try:
        # Verifica che session_state sia disponibile
        _ = st.session_state
    except Exception as e:
        # Se session_state non è disponibile, aspetta un momento e riprova
        import time
        time.sleep(0.1)
        try:
            _ = st.session_state
        except:
            # Se continua a fallire, forza un rerun
            st.rerun()
            return
    
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # === DEVICE DETECTION INIZIALE ===
    # Rileva il tipo di dispositivo solo se non è già stato fatto
    if not app_state.get('device_detection_done', False):
        detect_device_type()
    
    # === INIZIALIZZAZIONE VARIABILI BASE ===
    # Inizializza le variabili nel nostro state manager (già fatto nel constructor)
    # Manteniamo compatibilità con Streamlit per ora
    if "messages" not in st.session_state:
        st.session_state.messages = app_state.get_messages()
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "diet_plan" not in st.session_state:
        st.session_state.diet_plan = app_state.get_diet_plan()
    # Inizializza OpenAI client e sincronizza con app_state
    if "openai_client" not in st.session_state:
        # Per Streamlit Cloud, usa st.secrets, altrimenti usa variabile d'ambiente
        try:
            api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                st.session_state.openai_client = OpenAI(api_key=api_key)
            else:
                st.session_state.openai_client = OpenAI()  # Fallback per sviluppo locale
        except:
            # Fallback se st.secrets non è disponibile (sviluppo locale)
            st.session_state.openai_client = OpenAI()
        # Sincronizza con app_state
        app_state.set_openai_client(st.session_state.openai_client)
    if "current_run_id" not in st.session_state:
        st.session_state.current_run_id = None
        # Sincronizza con app_state
        app_state.set_current_run_id(st.session_state.current_run_id)
    if "current_question" not in st.session_state:
        st.session_state.current_question = app_state.get_current_question()
    if "nutrition_answers" not in st.session_state:
        st.session_state.nutrition_answers = app_state.get_nutrition_answers()
    if "user_data_manager" not in st.session_state:
        st.session_state.user_data_manager = UserDataManager()
        # Sincronizza con app_state
        app_state.set_user_data_manager(st.session_state.user_data_manager)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_user_data_manager() is None:
            app_state.set_user_data_manager(st.session_state.user_data_manager)
    
    # === INIZIALIZZAZIONE MANAGER CHAT ===
    # Import qui per evitare importazioni circolari
    from chat import ChatManager, AssistantManager
    
    if "assistant_manager" not in st.session_state:
        st.session_state.assistant_manager = AssistantManager(st.session_state.openai_client)
        st.session_state.assistant_manager.create_assistant()
        # Sincronizza con app_state
        app_state.set_assistant_manager(st.session_state.assistant_manager)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_assistant_manager() is None:
            app_state.set_assistant_manager(st.session_state.assistant_manager)
            
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager(
            st.session_state.openai_client,
            st.session_state.user_data_manager
        )
        # Sincronizza con app_state
        app_state.set_chat_manager(st.session_state.chat_manager)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_chat_manager() is None:
            app_state.set_chat_manager(st.session_state.chat_manager)

    # === INIZIALIZZAZIONE SERVIZIO DEEPSEEK ===
    if "deepseek_manager" not in st.session_state:
        st.session_state.deepseek_manager = DeepSeekManager()
        if not st.session_state.deepseek_manager.is_available():
            st.warning("⚠️ DEEPSEEK_API_KEY non trovata nel file .env. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")
        # Sincronizza con app_state
        app_state.set_deepseek_manager(st.session_state.deepseek_manager)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_deepseek_manager() is None:
            app_state.set_deepseek_manager(st.session_state.deepseek_manager)

    # === INIZIALIZZAZIONE SERVIZIO PREFERENCES ===
    if "preferences_manager" not in st.session_state:
        st.session_state.preferences_manager = PreferencesManager(
            user_data_manager=st.session_state.user_data_manager
        )
        # Sincronizza con app_state
        app_state.set_preferences_manager(st.session_state.preferences_manager)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_preferences_manager() is None:
            app_state.set_preferences_manager(st.session_state.preferences_manager)

    # === INIZIALIZZAZIONE SERVIZIO SUPABASE ===
    if "supabase_service" not in st.session_state:
        from services.supabase_service import SupabaseUserService
        st.session_state.supabase_service = SupabaseUserService()
        # Sincronizza con app_state
        app_state.set_supabase_service(st.session_state.supabase_service)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_supabase_service() is None:
            app_state.set_supabase_service(st.session_state.supabase_service)

    # === VARIABILI PER GESTIONE AGENTE IN BACKGROUND ===
    # Sincronizza con il nostro state manager - sincronizzazione bidirezionale
    if "agent_generating" not in st.session_state:
        st.session_state.agent_generating = app_state.is_agent_generating()
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        app_state.set_agent_generating(st.session_state.agent_generating)
    if "agent_response_ready" not in st.session_state:
        st.session_state.agent_response_ready = app_state.get_agent_response_ready()
    if "agent_response_text" not in st.session_state:
        st.session_state.agent_response_text = app_state.get_agent_response_text()
    if "agent_user_input" not in st.session_state:
        st.session_state.agent_user_input = app_state.get_agent_user_input()
    if "agent_thread_id" not in st.session_state:
        st.session_state.agent_thread_id = app_state.get_agent_thread_id()
    if "current_page" not in st.session_state:
        st.session_state.current_page = app_state.get_current_page()
    if "pending_user_input" not in st.session_state:
        st.session_state.pending_user_input = app_state.get_pending_user_input()
    else:
        # Sincronizza se esiste già in session_state
        app_state.set_pending_user_input(st.session_state.pending_user_input)

    # === INIZIALIZZAZIONE CLIENT DEEPSEEK LEGACY ===
    # NOTA: Questo è mantenuto per compatibilità con codice esistente
    # che potrebbe ancora usare il client DeepSeek direttamente
    if "deepseek_client" not in st.session_state:
        try:
            # Per Streamlit Cloud, usa st.secrets, altrimenti usa variabile d'ambiente
            deepseek_api_key = None
            try:
                deepseek_api_key = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
            except:
                deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
                
            if not deepseek_api_key:
                st.warning("⚠️ DEEPSEEK_API_KEY non trovata. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")
                st.session_state.deepseek_client = None
            else:
                st.session_state.deepseek_client = OpenAI(
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
            # Sincronizza con app_state
            app_state.set_deepseek_client(st.session_state.deepseek_client)
        except Exception as e:
            st.error(f"Errore nell'inizializzazione del client DeepSeek: {str(e)}")
            st.session_state.deepseek_client = None
            # Sincronizza con app_state
            app_state.set_deepseek_client(None)

    # === VARIABILI PER DEEPSEEK LEGACY ===
    if "interaction_count" not in st.session_state:
        st.session_state.interaction_count = 0
        # Sincronizza con app_state
        app_state.set_interaction_count(0)
    else:
        # Sincronizza se esiste già
        app_state.set_interaction_count(st.session_state.interaction_count)
        
    if "last_extraction_count" not in st.session_state:
        st.session_state.last_extraction_count = 0
        # Sincronizza con app_state
        app_state.set_last_extraction_count(0)
    else:
        # Sincronizza se esiste già
        app_state.set_last_extraction_count(st.session_state.last_extraction_count)
        
    if "deepseek_queue" not in st.session_state:
        st.session_state.deepseek_queue = queue.Queue()
        # Sincronizza con app_state
        app_state.set_deepseek_queue(st.session_state.deepseek_queue)
        
    if "deepseek_results" not in st.session_state:
        st.session_state.deepseek_results = {}
        # Sincronizza con app_state
        app_state.set_deepseek_results({})

    # Inizializza token tracker se non esiste
    if "token_tracker" not in st.session_state:
        from services.token_cost_service import TokenCostTracker
        st.session_state.token_tracker = TokenCostTracker(model="gpt-4")
        # Sincronizza con app_state
        app_state.set_token_tracker(st.session_state.token_tracker)
    else:
        # Se esiste già in session_state, assicurati che app_state sia sincronizzato
        if app_state.get_token_tracker() is None:
            app_state.set_token_tracker(st.session_state.token_tracker)


def initialize_global_variables():
    """
    Inizializza le variabili globali necessarie per la comunicazione tra thread.
    
    Queste variabili non possono usare session_state in quanto devono essere
    accessibili da thread diversi.
    
    Returns:
        tuple: (deepseek_results_queue, deepseek_lock, file_access_lock)
    """
    deepseek_results_queue = queue.Queue()
    deepseek_lock = threading.Lock()
    file_access_lock = threading.Lock()
    
    return deepseek_results_queue, deepseek_lock, file_access_lock 