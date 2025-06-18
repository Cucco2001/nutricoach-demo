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

# Import dello stile custom
from frontend.style import load_css

# Import per la gestione delle immagini
from utils.image_utils import get_image_html

import threading
import queue

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="NutrAICoach - Il tuo assistente nutrizionale personale",
    page_icon="🥗",
    layout="wide"
)

# === INIZIALIZZAZIONE MODULARE DELL'APPLICAZIONE ===
# Tutte le inizializzazioni sono ora centralizzate nel modulo frontend
initialize_app()

# Inizializzazione delle variabili globali per la comunicazione tra thread
deepseek_results_queue, deepseek_lock, file_access_lock = initialize_global_variables()

# NOTA: Tutte le funzioni di chat (create_assistant, create_new_thread, check_and_cancel_run, 
# chat_with_assistant, chat_interface) sono state spostate nei moduli chat/


def main():
    # Carica lo stile CSS custom
    load_css()
    
    # Rimuovi il titolo principale di Streamlit, lo gestiremo con HTML custom
    # st.title("NutriCoach - Il tuo assistente nutrizionale personale 🥗")
    
    # === GESTIONE LOGIN/REGISTRAZIONE MODULARE ===
    # Usa il nuovo sistema modulare per gestire l'autenticazione
    is_authenticated = handle_login_registration(st.session_state.user_data_manager)
    
    # Se l'utente è autenticato, mostra l'interfaccia principale
    if is_authenticated:
        # Header personalizzato dell'app con logo base64
        logo_html = get_image_html("sito_web/logo.png", height=50, alt="NutrAICoach")
        st.markdown(
            f'''
            <div class="app-header">
                <div class="app-header-content">
                    {logo_html}
                    <h1 class="app-title">NutrAICoach</h1>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
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