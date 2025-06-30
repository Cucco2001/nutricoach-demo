import streamlit as st

# Configurazione della pagina Streamlit - DEVE essere la prima chiamata Streamlit
st.set_page_config(
    page_title="NutrAICoach - Il tuo assistente nutrizionale personale",
    page_icon="🥗",
    layout="wide"
)

import os
import time
import json
import pandas as pd
from dotenv import load_dotenv

# Carica le variabili d'ambiente PRIMA di importare i moduli che ne hanno bisogno
load_dotenv()

from openai import OpenAI
from agent import available_tools, system_prompt
from agent_tools.user_data_manager import UserDataManager
from datetime import datetime
from agent_tools.nutridb_tool import (
    get_macros, get_LARN_protein, get_standard_portion, 
    get_weight_from_volume, get_LARN_fibre, 
    get_LARN_lipidi_percentuali, get_LARN_vitamine, 
    compute_Harris_Benedict_Equation, get_protein_multiplier,
    calculate_sport_expenditure, calculate_weight_goal_calories, 
    analyze_bmi_and_goals, check_vitamins, get_food_substitutes, check_ultraprocessed_foods
)
from agent_tools.user_data_tool import (
    get_user_preferences, get_agent_qa, get_nutritional_info
)
# Import dal nuovi moduli frontend
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.handle_nutrition_questions import handle_nutrition_questions
from frontend.handle_initial_info import handle_user_info_form, handle_user_info_display
from frontend.buttons import handle_restart_button
from frontend.Piano_nutrizionale import handle_user_data

# Import dell'inizializzazione modulare
from frontend import initialize_app, initialize_global_variables

# Import del login modulare
from frontend import handle_login_registration, show_logout_button

# Import del nuovo servizio DeepSeek modulare
from services.deep_seek_service import DeepSeekManager


# Import del nuovo servizio Preferences modulare
from services.preferences_service import PreferencesManager

# Import dei moduli agent
from agent.tool_handler import handle_tool_calls
from agent.prompts import get_initial_prompt

# Import dei nuovi moduli chat - includendo l'interfaccia modulare
from chat import ChatManager, AssistantManager, chat_interface

# Import del sistema di stili adattivi
from frontend.adaptive_style import setup_responsive_app

# Import per la gestione delle immagini
from utils.image_utils import get_image_html

# Import del sistema privacy
from utils.privacy_handler import check_privacy_acceptance, accept_privacy_terms, get_privacy_disclaimer_text

import threading
import queue

# === INIZIALIZZAZIONE MODULARE DELL'APPLICAZIONE ===
# Tutte le inizializzazioni sono ora centralizzate nel modulo frontend
initialize_app()

# Inizializzazione delle variabili globali per la comunicazione tra thread
deepseek_results_queue, deepseek_lock, file_access_lock = initialize_global_variables()

# NOTA: Tutte le funzioni di chat (create_assistant, create_new_thread, check_and_cancel_run, 
# chat_with_assistant, chat_interface) sono state spostate nei moduli chat/


def main():
    # Protezione contro errori di inizializzazione della sessione Streamlit
    try:
        # Test di accesso al session_state
        _ = st.session_state
    except Exception as e:
        st.error("🔄 Rilevato problema di inizializzazione. Ricarica automatica in corso...")
        import time
        time.sleep(1)
        st.rerun()
        return
    
    # Configura l'app con stili adattivi
    setup_responsive_app()
    
    # Se l'utente ha appena completato il form iniziale su mobile, chiudi la sidebar.
    if st.session_state.get('just_completed_initial_info', False):
        if st.session_state.get('device_type') == 'mobile':
            from streamlit_js_eval import streamlit_js_eval
            
            # Esegui JS per trovare e cliccare il bottone di chiusura della sidebar.
            # Viene usato un timeout per dare a Streamlit il tempo di renderizzare la sidebar.
            js_code = """
            setTimeout(() => {
                const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
                if (sidebar) {
                    const closeButton = sidebar.querySelector('button');
                    if (closeButton) {
                        closeButton.click();
                    }
                }
            }, 300);
            """
            streamlit_js_eval(js_expressions=js_code, key="close_sidebar_js")
        
        # Rimuovi il flag per evitare che venga eseguito di nuovo.
        del st.session_state.just_completed_initial_info

    # === PRIVACY & DISCLAIMER CHECK ===
    # Controlla se l'utente ha accettato privacy e disclaimer
    if not check_privacy_acceptance():
        st.markdown("# 🥗 NutrAiCoach")
        st.markdown(get_privacy_disclaimer_text())
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✅ Accetto e Continuo", type="primary", use_container_width=True):
                accept_privacy_terms()
                st.rerun()
        st.stop()

    # === GESTIONE LOGIN/REGISTRAZIONE MODULARE ===
    # Usa il nuovo sistema modulare per gestire l'autenticazione
    is_authenticated = handle_login_registration(st.session_state.user_data_manager)
    
    # Se l'utente è autenticato, mostra l'interfaccia principale
    if is_authenticated:
        # Sidebar per le funzionalità utente
        with st.sidebar:
            st.header("Menu")
            
            # Controlla se l'agente sta generando
            is_agent_generating = getattr(st.session_state, 'agent_generating', False)
            
            if is_agent_generating:
                # Mostra un messaggio informativo e blocca la navigazione
                st.info("🤖 L'assistente sta elaborando la risposta, attendi completamento per accedere ad altri tab")
                # Mantieni la selezione corrente senza permettere cambiamenti
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = "Chat"
                page = st.session_state.current_page
                st.write(f"**Sezione corrente:** {page}")
            else:
                # Navigazione normale quando l'agente non sta generando
                page = st.radio(
                    "Seleziona una sezione",
                    ["Chat", "Preferenze", "Piano Nutrizionale"]
                )
                # Salva la selezione corrente
                st.session_state.current_page = page
            
            # Usa il nuovo modulo per gestire il logout
            show_logout_button()
        
        if page == "Chat":
            # Usa l'interfaccia chat modulare
            chat_interface()
        elif page == "Preferenze":
            st.session_state.preferences_manager.handle_user_preferences(st.session_state.user_info["id"])
        elif page == "Piano Nutrizionale":
            handle_user_data()


if __name__ == "__main__":
    main() 