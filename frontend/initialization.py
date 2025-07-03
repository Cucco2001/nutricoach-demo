"""
Modulo per l'inizializzazione di servizi dell'applicazione.

Centralizza le inizializzazioni essenziali dei servizi in app_state
mantenendo solo il minimo necessario per Streamlit.
"""

import streamlit as st
import os
import threading
import queue
from openai import OpenAI
from dotenv import load_dotenv

# Import dei manager e servizi
from agent_tools.user_data_manager import UserDataManager
from services.deep_seek_service import DeepSeekManager
from services.preferences_service import PreferencesManager
from services.token_cost_service import TokenCostTracker

# Import del nuovo state manager
from services.state_service import app_state

# Import del device detector
from frontend.device_detector import detect_device_type


def initialize_app():
    """
    Inizializza solo i servizi essenziali nell'app_state.
    Streamlit può accedere ai dati tramite app_state quando necessario.
    """
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # === DEVICE DETECTION INIZIALE ===
    if not app_state.get('device_detection_done', False):
        detect_device_type()
    
    # === INIZIALIZZAZIONE OPENAI CLIENT ===
    if app_state.get_openai_client() is None:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
            else:
                client = OpenAI()  # Fallback per sviluppo locale
        except:
            client = OpenAI()
        app_state.set_openai_client(client)
    
    # === INIZIALIZZAZIONE USER DATA MANAGER ===
    if app_state.get_user_data_manager() is None:
        user_data_manager = UserDataManager()
        app_state.set_user_data_manager(user_data_manager)
    
    # === INIZIALIZZAZIONE MANAGER CHAT ===
    from chat import ChatManager, AssistantManager
    
    if app_state.get_assistant_manager() is None:
        openai_client = app_state.get_openai_client()
        assistant_manager = AssistantManager(openai_client)
        assistant_manager.create_assistant()
        app_state.set_assistant_manager(assistant_manager)
    
    if app_state.get_chat_manager() is None:
        openai_client = app_state.get_openai_client()
        user_data_manager = app_state.get_user_data_manager()
        chat_manager = ChatManager(openai_client, user_data_manager)
        app_state.set_chat_manager(chat_manager)
    
    # === INIZIALIZZAZIONE DEEPSEEK MANAGER ===
    if app_state.get_deepseek_manager() is None:
        deepseek_manager = DeepSeekManager()
        if not deepseek_manager.is_available():
            st.warning("⚠️ DEEPSEEK_API_KEY non trovata. Il sistema di estrazione automatica sarà disabilitato.")
        app_state.set_deepseek_manager(deepseek_manager)
    
    # === INIZIALIZZAZIONE PREFERENCES MANAGER ===
    if app_state.get_preferences_manager() is None:
        user_data_manager = app_state.get_user_data_manager()
        preferences_manager = PreferencesManager(user_data_manager=user_data_manager)
        app_state.set_preferences_manager(preferences_manager)
    
    # === INIZIALIZZAZIONE SUPABASE SERVICE ===
    if app_state.get_supabase_service() is None:
        from services.supabase_service import SupabaseUserService
        supabase_service = SupabaseUserService()
        app_state.set_supabase_service(supabase_service)
    
    # === INIZIALIZZAZIONE DEEPSEEK CLIENT LEGACY ===
    if app_state.get_deepseek_client() is None:
        try:
            deepseek_api_key = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
            if deepseek_api_key:
                deepseek_client = OpenAI(
                    api_key=deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
            else:
                deepseek_client = None
        except Exception as e:
            st.error(f"Errore nell'inizializzazione del client DeepSeek: {str(e)}")
            deepseek_client = None
        app_state.set_deepseek_client(deepseek_client)
    
    # === INIZIALIZZAZIONE VARIABILI DEEPSEEK LEGACY ===
    if app_state.get_interaction_count() == 0:
        app_state.set_interaction_count(0)
    
    if app_state.get_last_extraction_count() == 0:
        app_state.set_last_extraction_count(0)
    
    if app_state.get_deepseek_queue() is None:
        app_state.set_deepseek_queue(queue.Queue())
    
    deepseek_results = app_state.get_deepseek_results()
    if not deepseek_results:
        app_state.set_deepseek_results({})
    
    # === INIZIALIZZAZIONE TOKEN TRACKER ===
    if app_state.get_token_tracker() is None:
        token_tracker = TokenCostTracker(model="gpt-4")
        app_state.set_token_tracker(token_tracker)


def initialize_global_variables():
    """
    Inizializza le variabili globali necessarie per la comunicazione tra thread.
    
    Returns:
        tuple: (deepseek_results_queue, deepseek_lock, file_access_lock)
    """
    deepseek_results_queue = queue.Queue()
    deepseek_lock = threading.Lock()
    file_access_lock = threading.Lock()
    
    return deepseek_results_queue, deepseek_lock, file_access_lock 