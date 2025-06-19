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


def initialize_app():
    """
    Inizializza tutte le variabili di sessione e i servizi dell'applicazione.
    
    Questa funzione deve essere chiamata all'inizio dell'app per configurare
    tutti i componenti necessari al funzionamento.
    """
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # === INIZIALIZZAZIONE VARIABILI BASE ===
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "diet_plan" not in st.session_state:
        st.session_state.diet_plan = None
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
    if "current_run_id" not in st.session_state:
        st.session_state.current_run_id = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "nutrition_answers" not in st.session_state:
        st.session_state.nutrition_answers = {}
    if "user_data_manager" not in st.session_state:
        st.session_state.user_data_manager = UserDataManager()

    # === INIZIALIZZAZIONE MANAGER CHAT ===
    # Import qui per evitare importazioni circolari
    from chat import ChatManager, AssistantManager
    
    if "assistant_manager" not in st.session_state:
        st.session_state.assistant_manager = AssistantManager(st.session_state.openai_client)
        st.session_state.assistant_manager.create_assistant()
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager(
            st.session_state.openai_client,
            st.session_state.user_data_manager
        )

    # === INIZIALIZZAZIONE SERVIZIO DEEPSEEK ===
    if "deepseek_manager" not in st.session_state:
        st.session_state.deepseek_manager = DeepSeekManager()
        if not st.session_state.deepseek_manager.is_available():
            st.warning("⚠️ DEEPSEEK_API_KEY non trovata nel file .env. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")

    # === INIZIALIZZAZIONE SERVIZIO PREFERENCES ===
    if "preferences_manager" not in st.session_state:
        st.session_state.preferences_manager = PreferencesManager(
            user_data_manager=st.session_state.user_data_manager
        )

    # === VARIABILI PER GESTIONE AGENTE IN BACKGROUND ===
    if "agent_generating" not in st.session_state:
        st.session_state.agent_generating = False
    if "agent_response_ready" not in st.session_state:
        st.session_state.agent_response_ready = False
    if "agent_response_text" not in st.session_state:
        st.session_state.agent_response_text = None
    if "agent_user_input" not in st.session_state:
        st.session_state.agent_user_input = None
    if "agent_thread_id" not in st.session_state:
        st.session_state.agent_thread_id = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Chat"
    if "pending_user_input" not in st.session_state:
        st.session_state.pending_user_input = None

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
        except Exception as e:
            st.error(f"Errore nell'inizializzazione del client DeepSeek: {str(e)}")
            st.session_state.deepseek_client = None

    # === VARIABILI PER DEEPSEEK LEGACY ===
    if "interaction_count" not in st.session_state:
        st.session_state.interaction_count = 0
    if "last_extraction_count" not in st.session_state:
        st.session_state.last_extraction_count = 0
    if "deepseek_queue" not in st.session_state:
        st.session_state.deepseek_queue = queue.Queue()
    if "deepseek_results" not in st.session_state:
        st.session_state.deepseek_results = {}


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