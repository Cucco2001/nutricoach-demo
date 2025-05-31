"""
Modulo frontend per il sistema NutriCoach.

Questo modulo contiene tutti i componenti frontend specifici per l'interfaccia
utente di Streamlit, incluse le domande nutrizionali e la gestione degli sport.
"""

from .nutrition_questions import NUTRITION_QUESTIONS
from .sports_frontend import load_sports_data, get_sports_by_category, on_sport_category_change
from .Piano_nutrizionale import PianoNutrizionale, handle_user_data

__all__ = [
    'NUTRITION_QUESTIONS',
    'load_sports_data', 
    'get_sports_by_category',
    'on_sport_category_change',
    'PianoNutrizionale',
    'handle_user_data'
] 