"""
Servizio per la gestione delle preferenze utente.

Questo modulo fornisce un'interfaccia completa per la gestione delle preferenze
alimentari dell'utente nel sistema NutriCoach, inclusi alimenti esclusi, preferiti e note speciali.
"""

from .preferences_manager import PreferencesManager
from .food_preferences import FoodPreferences
from .preferences_ui import PreferencesUI

__all__ = [
    'PreferencesManager',
    'FoodPreferences',
    'PreferencesUI'
] 