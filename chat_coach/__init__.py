"""
Chat Coach Module

Modulo per la gestione del coach nutrizionale.
Fornisce funzionalità di consulenza nutrizionale interattiva
con supporto per immagini e analisi dei pasti.
"""

from .coach_interface import coach_interface
from .coach_manager import CoachManager
from .coach_prompts import get_coach_system_prompt
from .coach_tools import optimize_meal_portions, current_meal_query_tool

__all__ = [
    'coach_interface',
    'CoachManager', 
    'get_coach_system_prompt',
    'optimize_meal_portions',
    'current_meal_query_tool'
] 