import streamlit as st
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from agent import available_tools, system_prompt
from agent_tools.user_data_manager import UserDataManager
from datetime import datetime
from agent_tools.nutridb_tool import (
    get_macros, get_LARN_protein, get_standard_portion, 
    get_weight_from_volume, get_fattore_cottura, get_LARN_fibre, 
    get_LARN_lipidi_percentuali, get_LARN_vitamine, 
    compute_Harris_Benedict_Equation, get_protein_multiplier,
    calculate_sport_expenditure, calculate_weight_goal_calories, 
    analyze_bmi_and_goals, check_vitamins, get_food_substitutes, check_ultraprocessed_foods
)
from agent_tools.user_data_tool import (
    get_user_preferences, get_progress_history, get_agent_qa, get_nutritional_info
)
# Import dal nuovi moduli frontend
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.handle_nutrition_questions import handle_nutrition_questions
from frontend.handle_initial_info import handle_user_info_form, handle_user_info_display
from frontend.buttons import handle_restart_button
from frontend.Piano_nutrizionale import handle_user_data

# Import del nuovo servizio DeepSeek modulare
from services.deep_seek_service import DeepSeekManager

# Import del nuovo servizio Progress modulare
from services.progress_service import ProgressManager

# Import del nuovo servizio Preferences modulare
from services.preferences_service import PreferencesManager

# Import dei moduli agent
from agent.tool_handler import handle_tool_calls
from agent.prompts import get_initial_prompt

# Import dei nuovi moduli chat
from chat import ChatManager, AssistantManager

import threading
import queue

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="NutriCoach - Il tuo assistente nutrizionale personale",
    page_icon="🥗",
    layout="wide"
)

# Inizializzazione delle variabili di sessione
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "diet_plan" not in st.session_state:
    st.session_state.diet_plan = None
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI()
if "current_run_id" not in st.session_state:
    st.session_state.current_run_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "nutrition_answers" not in st.session_state:
    st.session_state.nutrition_answers = {}
if "user_data_manager" not in st.session_state:
    st.session_state.user_data_manager = UserDataManager()

# Inizializzazione dei manager chat modulari
if "assistant_manager" not in st.session_state:
    st.session_state.assistant_manager = AssistantManager(st.session_state.openai_client)
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager(
        st.session_state.openai_client,
        st.session_state.user_data_manager
    )

# Inizializzazione del servizio DeepSeek modulare
if "deepseek_manager" not in st.session_state:
    st.session_state.deepseek_manager = DeepSeekManager()
    if not st.session_state.deepseek_manager.is_available():
        st.warning("⚠️ DEEPSEEK_API_KEY non trovata nel file .env. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")

# Inizializzazione del servizio Progress modulare
if "progress_manager" not in st.session_state:
    st.session_state.progress_manager = ProgressManager(
        user_data_manager=st.session_state.user_data_manager,
        chat_handler=lambda x: st.session_state.chat_manager.chat_with_assistant(x)
    )

# Inizializzazione del servizio Preferences modulare
if "preferences_manager" not in st.session_state:
    st.session_state.preferences_manager = PreferencesManager(
        user_data_manager=st.session_state.user_data_manager
    )

# Variabili per gestione generazione agente in background
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

# NOTA: Tutto il codice DeepSeek è stato spostato nel servizio modulare services/deep_seek_service/
# Le funzioni extract_nutritional_data_with_deepseek, save_extracted_nutritional_data, 
# check_and_extract_nutritional_data_async, extract_nutritional_data_with_deepseek_local,
# check_deepseek_results, show_deepseek_notification sono ora gestite dal DeepSeekManager

# Inizializzazione DeepSeek client per estrazione dati nutrizionali
if "deepseek_client" not in st.session_state:
    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            st.warning("⚠️ DEEPSEEK_API_KEY non trovata nel file .env. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")
            st.session_state.deepseek_client = None
        else:
            st.session_state.deepseek_client = OpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com"
            )
    except Exception as e:
        st.error(f"Errore nell'inizializzazione del client DeepSeek: {str(e)}")
        st.session_state.deepseek_client = None
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "last_extraction_count" not in st.session_state:
    st.session_state.last_extraction_count = 0
if "deepseek_queue" not in st.session_state:
    st.session_state.deepseek_queue = queue.Queue()
if "deepseek_results" not in st.session_state:
    st.session_state.deepseek_results = {}

# Variabili globali per la comunicazione tra thread (non possono usare session_state)
deepseek_results_queue = queue.Queue()
deepseek_lock = threading.Lock()
file_access_lock = threading.Lock()  # Lock per accesso ai file utente

# NOTA: Le funzioni create_assistant, create_new_thread, check_and_cancel_run, chat_with_assistant 
# sono state spostate nei moduli chat/assistant_manager.py e chat/chat_manager.py

def chat_interface():
    """Interfaccia principale della chat"""
    # Controlla risultati DeepSeek in background usando il nuovo servizio
    st.session_state.deepseek_manager.check_and_process_results()
    st.session_state.deepseek_manager.show_notifications()
    
    # Crea l'assistente usando il nuovo manager
    st.session_state.assistant_manager.create_assistant()
    
    # Sidebar per le informazioni dell'utente
    with st.sidebar:
        st.subheader("Le tue informazioni")
        if not st.session_state.user_info.get("età"):
            # Usa il nuovo modulo per gestire il form delle informazioni utente
            handle_user_info_form(
                user_id=st.session_state.user_info["id"],
                user_data_manager=st.session_state.user_data_manager,
                create_new_thread_func=st.session_state.chat_manager.create_new_thread
            )
        else:
            # Usa il nuovo modulo per mostrare le informazioni utente
            handle_user_info_display(st.session_state.user_info)
            
            # Usa il nuovo modulo per gestire il bottone "Ricomincia"
            handle_restart_button(
                user_data_manager=st.session_state.user_data_manager,
                deepseek_manager=st.session_state.deepseek_manager,
                create_new_thread_func=st.session_state.chat_manager.create_new_thread
            )
    
    # Area principale della chat
    if st.session_state.user_info.get("età"):
        if st.session_state.current_question < len(NUTRITION_QUESTIONS):
            # Usa il nuovo modulo per gestire le domande nutrizionali
            has_more_questions = handle_nutrition_questions(
                user_info=st.session_state.user_info,
                user_id=st.session_state.user_info["id"],
                user_data_manager=st.session_state.user_data_manager
            )
            
            # Se non ci sono più domande, passa alla chat
            if not has_more_questions:
                st.rerun()
        else:
            # Se non ci sono ancora messaggi, carica la history esistente
            if not st.session_state.messages:
                chat_history = st.session_state.user_data_manager.get_chat_history(st.session_state.user_info["id"])
                if chat_history:
                    st.session_state.messages = [
                        {"role": msg.role, "content": msg.content}
                        for msg in chat_history
                    ]
                else:
                    # Se non c'è history, invia il prompt iniziale
                    initial_prompt = get_initial_prompt(
                        user_info=st.session_state.user_info,
                        nutrition_answers=st.session_state.nutrition_answers,
                        user_preferences=st.session_state.user_info['preferences']
                    )
                    
                    # Crea un nuovo thread solo se non esiste già
                    if not hasattr(st.session_state, 'thread_id'):
                        st.session_state.chat_manager.create_new_thread()
                    
                    # Invia il prompt iniziale usando il nuovo manager
                    response = st.session_state.chat_manager.chat_with_assistant(initial_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Salva il messaggio nella history
                    st.session_state.user_data_manager.save_chat_message(
                        st.session_state.user_info["id"],
                        "assistant",
                        response
                    )
                    st.rerun()
            
            # Mostra la cronologia dei messaggi
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Mostra notifiche DeepSeek se presenti
            st.session_state.deepseek_manager.show_notifications()
            
            # Input per nuovi messaggi
            user_input = st.chat_input("Scrivi un messaggio...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                # Salva il messaggio dell'utente nella history
                st.session_state.user_data_manager.save_chat_message(
                    st.session_state.user_info["id"],
                    "user",
                    user_input
                )
                with st.spinner("L'assistente sta elaborando la risposta..."):
                    # Usa il nuovo chat manager per la conversazione
                    response = st.session_state.chat_manager.chat_with_assistant(user_input)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Salva la risposta dell'assistente nella history
                    st.session_state.user_data_manager.save_chat_message(
                        st.session_state.user_info["id"],
                        "assistant",
                        response
                    )
                    # Salva la domanda e risposta dell'agente
                    st.session_state.user_data_manager.save_agent_qa(
                        st.session_state.user_info["id"],
                        user_input,
                        response
                    )
                    
                    # Controlla se è necessario estrarre dati nutrizionali con DeepSeek usando il nuovo servizio
                    st.session_state.deepseek_manager.check_and_extract_if_needed(
                        user_id=st.session_state.user_info["id"],
                        user_data_manager=st.session_state.user_data_manager,
                        user_info=st.session_state.user_info
                    )
                    
                st.rerun()
    else:
        st.info("👈 Per iniziare, inserisci le tue informazioni nella barra laterale")

def main():
    st.title("NutriCoach - Il tuo assistente nutrizionale personale 🥗")
    
    # Gestione login/registrazione
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    if not st.session_state.user_info:
        tab1, tab2 = st.tabs(["Login", "Registrazione"])
        
        with tab1:
            with st.form("login_form"):
                st.write("Accedi al tuo account")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Accedi"):
                    success, result = st.session_state.user_data_manager.login_user(username, password)
                    if success:
                        # Carica le informazioni nutrizionali salvate
                        nutritional_info = st.session_state.user_data_manager.get_nutritional_info(result)
                        
                        # Imposta le informazioni dell'utente
                        st.session_state.user_info = {
                            "id": result,
                            "username": username
                        }
                        
                        # Se ci sono informazioni nutrizionali salvate, caricale
                        if nutritional_info:
                            # Aggiorna le informazioni dell'utente
                            st.session_state.user_info.update({
                                "età": nutritional_info.età,
                                "sesso": nutritional_info.sesso,
                                "peso": nutritional_info.peso,
                                "altezza": nutritional_info.altezza,
                                "attività": nutritional_info.attività,
                                "obiettivo": nutritional_info.obiettivo,
                                "preferences": st.session_state.user_data_manager.get_user_preferences(result)  # Aggiungi le preferenze
                            })
                            
                            # Carica le risposte nutrizionali
                            if nutritional_info.nutrition_answers:
                                st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                                st.session_state.current_question = len(NUTRITION_QUESTIONS)
                        
                        st.rerun()
                    else:
                        st.error(result)
        
        with tab2:
            with st.form("register_form"):
                st.write("Crea un nuovo account")
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Conferma password", type="password")
                
                if st.form_submit_button("Registrati"):
                    if new_password != confirm_password:
                        st.error("Le password non coincidono")
                    else:
                        success, result = st.session_state.user_data_manager.register_user(new_username, new_password)
                        if success:
                            st.success("Registrazione completata! Ora puoi accedere.")
                        else:
                            st.error(result)
    
    # Se l'utente è autenticato, mostra l'interfaccia principale
    if st.session_state.user_info:
        # Sidebar per le funzionalità utente
        with st.sidebar:
            st.header("Menu")
            page = st.radio(
                "Seleziona una sezione",
                ["Chat", "Progressi", "Preferenze", "Piano Nutrizionale"]
            )
            
            # Aggiungi pulsante logout
            if st.button("Logout"):
                st.session_state.user_info = None
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
                st.rerun()
        
        if page == "Chat":
            chat_interface()
        elif page == "Progressi":
            st.session_state.progress_manager.track_user_progress()
            st.session_state.progress_manager.show_progress_history()
        elif page == "Preferenze":
            st.session_state.preferences_manager.handle_user_preferences(st.session_state.user_info["id"])
        elif page == "Piano Nutrizionale":
            handle_user_data()

if __name__ == "__main__":
    main() 