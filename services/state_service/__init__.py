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
        # Debug: stampa l'ID dell'istanza per verificare separazione
        instance_id = id(st.session_state.app_state_manager)
        print(f"🆕 [SESSION] Nuova istanza AppStateManager creata: {instance_id}")
    
    return st.session_state.app_state_manager

class AppStateProxy:
    """
    Proxy che assicura che ogni chiamata ad app_state 
    ottenga l'istanza corretta per la sessione attuale.
    """
    def __getattr__(self, name):
        return getattr(get_app_state(), name)
    
    def __setattr__(self, name, value):
        setattr(get_app_state(), name, value)

# Istanza proxy che reindirizza sempre alla sessione corrente
app_state = AppStateProxy()

__all__ = [
    'AppStateManager',
    'UserInfo', 
    'app_state',
    'get_app_state'
] 