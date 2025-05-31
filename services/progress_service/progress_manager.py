"""
Manager principale per il servizio di progresso dell'utente.

Coordina le funzionalità di tracking e visualizzazione dei progressi,
fornendo un'interfaccia unificata per l'applicazione principale.
"""

from .progress_tracker import ProgressTracker
from .progress_display import ProgressDisplay


class ProgressManager:
    """Manager principale per il servizio di progresso"""
    
    def __init__(self, user_data_manager, chat_handler):
        """
        Inizializza il manager dei progressi.
        
        Args:
            user_data_manager: Gestore dei dati utente
            chat_handler: Funzione per gestire la chat con l'assistente
        """
        self.user_data_manager = user_data_manager
        self.chat_handler = chat_handler
        
        # Inizializza i componenti
        self.tracker = ProgressTracker(user_data_manager, chat_handler)
        self.display = ProgressDisplay(user_data_manager)
    
    def track_user_progress(self):
        """
        Gestisce il tracking dei progressi dell'utente.
        
        Questa è la funzione principale che sostituisce la funzione
        track_user_progress() originale in app.py.
        """
        self.tracker.show_tracking_form()
    
    def show_progress_history(self):
        """
        Mostra la storia dei progressi dell'utente.
        
        Questa è la funzione principale che sostituisce la funzione
        show_progress_history() originale in app.py.
        """
        self.display.show_progress_history() 