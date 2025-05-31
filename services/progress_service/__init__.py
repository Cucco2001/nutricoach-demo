"""
Servizio per la gestione del progresso dell'utente.

Questo modulo fornisce un'interfaccia completa per il tracking e la visualizzazione
dei progressi dell'utente nel sistema NutriCoach, inclusi peso e misurazioni corporee.
"""

from .progress_tracker import ProgressTracker
from .progress_display import ProgressDisplay
from .progress_manager import ProgressManager

__all__ = [
    'ProgressTracker',
    'ProgressDisplay', 
    'ProgressManager'
] 