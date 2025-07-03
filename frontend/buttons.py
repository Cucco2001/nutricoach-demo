"""
Modulo per la gestione dei bottoni dell'interfaccia utente.

Gestisce il comportamento e la logica dei bottoni interattivi,
inclusi reset, riavvii e altre azioni utente.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.tutorial import reset_tutorial
from services.state_service import UserInfo


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
        from services.state_service import app_state
        user_info = app_state.get_user_info()
        user_id = user_info.id
        username = user_info.username
        
        # Resetta il tutorial
        reset_tutorial(user_id)
        # Sincronizza anche con il nuovo state manager
        app_state.reset_tutorial(user_id)
        
        # Resetta le informazioni di sessione
        # Mantieni solo ID e username nell'UserInfo
        app_state.set_user_info(UserInfo(id=user_id, username=username))
        app_state.set_current_question(0)
        app_state.set_nutrition_answers({})
        app_state.clear_messages()
        
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
        
        # Pulisci le preferenze dall'app_state
        app_state.set_excluded_foods([])
        app_state.set_preferred_foods([])
        app_state.delete_preferences_prompt()
        app_state.delete_prompt_to_add_at_next_message()
        
        # Resetta il token tracker se esiste
        token_tracker = app_state.get_token_tracker()
        if token_tracker:
            from services.token_cost_service import TokenCostTracker
            new_tracker = TokenCostTracker(model="gpt-4")
            app_state.set_token_tracker(new_tracker)
        
        # Resetta lo stato di generazione dell'agente
        app_state.set_agent_generating(False)
        
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