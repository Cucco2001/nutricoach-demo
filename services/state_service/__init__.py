"""
Servizio per l'astrazione della gestione dello stato dell'applicazione.

Questo modulo fornisce un'interfaccia astratta per la gestione dello stato
che permette di disaccoppiare la logica di business dall'implementazione
specifica del frontend (Streamlit, Flask, FastAPI, etc.).
"""

from .app_state_manager import AppStateManager, UserInfo, app_state

__all__ = [
    'AppStateManager',
    'UserInfo', 
    'app_state'
] 