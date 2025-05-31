"""
Servizio DeepSeek per l'estrazione automatica di dati nutrizionali.

Questo modulo fornisce un'interfaccia completa per l'integrazione con DeepSeek AI
per l'estrazione automatica e asincrona di dati nutrizionali dalle conversazioni
del sistema NutriCoach.
"""

from .deepseek_client import DeepSeekClient
from .extraction_service import NutritionalDataExtractor
from .notification_manager import NotificationManager
from .deepseek_manager import DeepSeekManager

__all__ = [
    'DeepSeekClient',
    'NutritionalDataExtractor', 
    'NotificationManager',
    'DeepSeekManager'
] 