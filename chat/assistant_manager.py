"""
Modulo per la gestione dell'assistente OpenAI.

Gestisce la creazione, configurazione e mantenimento dell'assistente
utilizzato per le conversazioni nutrizionali.
"""

import streamlit as st
from agent import available_tools, system_prompt


class AssistantManager:
    """Gestisce l'assistente OpenAI per le conversazioni"""
    
    def __init__(self, openai_client):
        """
        Inizializza il gestore dell'assistente.
        
        Args:
            openai_client: Client OpenAI configurato
        """
        self.openai_client = openai_client
    
    def create_assistant(self):
        """
        Crea o recupera l'assistente dalla sessione.
        
        Returns:
            Assistant OpenAI o None in caso di errore
        """
        if "assistant" not in st.session_state:
            try:
                st.session_state.assistant = self.openai_client.beta.assistants.create(
                    name="NutrAICoach Assistant",
                    instructions=system_prompt,
                    tools=available_tools,
                    model="gpt-4.1"
                )
                st.session_state.assistant_created = True
            except Exception as e:
                st.error(f"Errore nella creazione dell'assistente: {str(e)}")
                st.session_state.assistant_created = False
                return None
        return st.session_state.assistant
    
    def get_assistant(self):
        """
        Ottiene l'assistente corrente dalla sessione.
        
        Returns:
            Assistant OpenAI se disponibile, None altrimenti
        """
        return st.session_state.get('assistant', None)
    
    def is_assistant_created(self):
        """
        Verifica se l'assistente è stato creato con successo.
        
        Returns:
            bool: True se l'assistente è stato creato, False altrimenti
        """
        return st.session_state.get('assistant_created', False)


def create_assistant(openai_client):
    """
    Funzione di convenienza per creare un assistente.
    
    Args:
        openai_client: Client OpenAI configurato
        
    Returns:
        Assistant OpenAI o None in caso di errore
    """
    manager = AssistantManager(openai_client)
    return manager.create_assistant() 