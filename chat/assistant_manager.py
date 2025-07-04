"""
Modulo per la gestione dell'assistente OpenAI.

Gestisce la creazione, configurazione e mantenimento dell'assistente
utilizzato per le conversazioni nutrizionali.
"""

import streamlit as st
from agent import available_tools, system_prompt

# Import del nuovo state manager
from services.state_service import app_state


class AssistantManager:
    """Gestisce l'assistente OpenAI per le conversazioni"""
    
    def __init__(self, openai_client):
        """
        Inizializza il gestore dell'assistente.
        
        Args:
            openai_client: Client OpenAI configurato
        """
        self.openai_client = openai_client
        self.assistant = None
        self.assistant_created = False
    
    def create_assistant(self):
        """
        Crea o recupera l'assistente esistente.
        
        Returns:
            Assistant OpenAI o None in caso di errore
        """
        # Prima controlla se c'è già un ID assistente salvato
        saved_assistant_id = app_state.get('assistant_id')
        
        if saved_assistant_id and self.assistant is None:
            try:
                # Prova a recuperare l'assistente esistente
                self.assistant = self.openai_client.beta.assistants.retrieve(saved_assistant_id)
                self.assistant_created = True
                print(f"✅ Assistente recuperato con ID: {self.assistant.id}")
                return self.assistant
            except Exception as e:
                print(f"⚠️ Impossibile recuperare assistente {saved_assistant_id}: {str(e)}")
                # Se non riusciamo a recuperarlo, ne creiamo uno nuovo
                app_state.delete('assistant_id')
        
        # Se non abbiamo un assistente, ne creiamo uno nuovo
        if self.assistant is None:
            try:
                self.assistant = self.openai_client.beta.assistants.create(
                    name="NutrAICoach Assistant",
                    instructions=system_prompt,
                    tools=available_tools,
                    model="gpt-4.1"
                )
                self.assistant_created = True
                # Salva l'ID per riutilizzo futuro
                app_state.set('assistant_id', self.assistant.id)
            except Exception as e:
                st.error(f"Errore nella creazione dell'assistente: {str(e)}")
                self.assistant_created = False
                return None
        return self.assistant
    
    def get_assistant(self):
        """
        Ottiene l'assistente corrente.
        
        Returns:
            Assistant OpenAI se disponibile, None altrimenti
        """
        return self.assistant
    
    def is_assistant_created(self):
        """
        Verifica se l'assistente è stato creato con successo.
        
        Returns:
            bool: True se l'assistente è stato creato, False altrimenti
        """
        return self.assistant_created


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