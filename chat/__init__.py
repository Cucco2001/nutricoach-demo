"""
Modulo per la gestione della chat con l'assistente AI.

Fornisce funzionalità per creare assistenti, gestire thread di conversazione,
mantenere le chat con l'agente NutrAICoach e gestire l'interfaccia utente.
"""

from .chat_manager import ChatManager
from .assistant_manager import AssistantManager
from .chat_interface import chat_interface

# Esportazioni principali
__all__ = [
    'ChatManager',
    'AssistantManager',
    'chat_interface'
] 