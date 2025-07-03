"""
Servizio per l'astrazione della gestione dello stato dell'applicazione.

Questo modulo fornisce un'interfaccia astratta per la gestione dello stato
che permette di disaccoppiare la logica di business dall'implementazione
specifica del frontend (Streamlit, Flask, FastAPI, etc.).
"""

from .app_state_manager import AppStateManager, UserInfo
import streamlit as st

def get_app_state() -> AppStateManager:
    """
    Ottiene l'istanza di AppStateManager per la sessione corrente.
    Ogni sessione Streamlit ha la sua istanza separata.
    """
    if 'app_state_manager' not in st.session_state:
        st.session_state.app_state_manager = AppStateManager()
    return st.session_state.app_state_manager

# Per compatibilità con il codice esistente
app_state = get_app_state()

__all__ = [
    'AppStateManager',
    'UserInfo', 
    'app_state',
    'get_app_state'
] 