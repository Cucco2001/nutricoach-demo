"""
Modulo per la gestione dell'agente nutrizionale.

Questo modulo contiene tutti i componenti relativi all'agente AI:
- Configurazione dell'agente (nutraicoach_agent.py)
- Gestione dei tool calls
- Prompt e template
- Script di esecuzione
"""

from .tool_handler import ToolHandler
from .prompts import get_initial_prompt, system_prompt, available_tools

__all__ = [
    'ToolHandler',
    'get_initial_prompt',
    'system_prompt',
    'available_tools'
] 