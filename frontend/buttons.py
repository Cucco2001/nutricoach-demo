"""
Modulo per la gestione dei bottoni dell'interfaccia utente.

Gestisce il comportamento e la logica dei bottoni interattivi,
inclusi reset, riavvii e altre azioni utente.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.tutorial import reset_tutorial


class ButtonHandler:
    """Gestisce la logica dei bottoni dell'interfaccia"""
    
    def __init__(self, user_data_manager, deepseek_manager, create_new_thread_func):
        """
        Inizializza il gestore dei bottoni.
        
        Args:
            user_data_manager: Gestore dei dati utente
            deepseek_manager: Gestore del servizio DeepSeek
            create_new_thread_func: Funzione per creare un nuovo thread
        """
        self.user_data_manager = user_data_manager
        self.deepseek_manager = deepseek_manager
        self.create_new_thread_func = create_new_thread_func
    
    def handle_restart_button(self):
        """
        Gestisce il bottone "Ricomincia".
        
        Resetta tutte le informazioni dell'utente e riavvia il processo.
        """
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ricomincia"):
                self._reset_user_session()
                st.rerun()
    
    def _reset_user_session(self):
        """
        Resetta completamente la sessione utente.
        
        Cancella tutti i dati, preferenze, chat history e riporta
        l'utente al punto di partenza iniziale.
        """
        user_id = st.session_state.user_info["id"]
        username = st.session_state.user_info["username"]
        
        # Resetta il tutorial
        reset_tutorial(user_id)
        
        # Resetta le informazioni di sessione
        st.session_state.user_info = {
            "id": user_id, 
            "username": username
        }
        st.session_state.current_question = 0
        st.session_state.nutrition_answers = {}
        st.session_state.messages = []
        
        # Reset completo DeepSeek usando il nuovo servizio
        self.deepseek_manager.clear_user_data(user_id)
        
        # Cancella la chat history e le domande/risposte dell'agente
        self.user_data_manager.clear_chat_history(user_id)
        self.user_data_manager.clear_agent_qa(user_id)
        
        # Resetta le informazioni nutrizionali ai valori di default
        self.user_data_manager.save_nutritional_info(
            user_id,
            {
                "età": 30,
                "sesso": "Maschio", 
                "peso": 70,
                "altezza": 170,
                "attività": "Sedentario",
                "obiettivo": "Mantenimento",
                "nutrition_answers": {},
                "agent_qa": []
            }
        )
        
        # Resetta le preferenze utente
        self.user_data_manager.clear_user_preferences(user_id)
        
        # Cancella anche le variabili di sessione delle preferenze
        if 'excluded_foods_list' in st.session_state:
            del st.session_state.excluded_foods_list
        if 'preferred_foods_list' in st.session_state:
            del st.session_state.preferred_foods_list
        if 'preferences_prompt' in st.session_state:
            del st.session_state.preferences_prompt
        if 'prompt_to_add_at_next_message' in st.session_state:
            del st.session_state.prompt_to_add_at_next_message
        
        # Resetta il token tracker se esiste
        if 'token_tracker' in st.session_state:
            from services.token_cost_service import TokenCostTracker
            st.session_state.token_tracker = TokenCostTracker(model="gpt-4")
        
        # Crea un nuovo thread
        self.create_new_thread_func()


def handle_restart_button(user_data_manager, deepseek_manager, create_new_thread_func):
    """
    Funzione di convenienza per gestire il bottone di riavvio.
    
    Args:
        user_data_manager: Gestore dei dati utente
        deepseek_manager: Gestore del servizio DeepSeek
        create_new_thread_func: Funzione per creare un nuovo thread
    """
    handler = ButtonHandler(user_data_manager, deepseek_manager, create_new_thread_func)
    handler.handle_restart_button() 