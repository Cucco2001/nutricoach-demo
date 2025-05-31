"""
Modulo per la gestione della chat con l'assistente AI.

Fornisce funzionalità per creare assistenti, gestire thread di conversazione
e mantenere le chat con l'agente NutriCoach.
"""

from .chat_manager import ChatManager
from .assistant_manager import AssistantManager

# Esportazioni principali
__all__ = [
    'ChatManager',
    'AssistantManager'
] 