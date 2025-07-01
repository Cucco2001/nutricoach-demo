"""
Modulo per la gestione della logica delle preferenze alimentari.

Gestisce la validazione, manipolazione e persistenza dei dati delle preferenze
alimentari dell'utente, inclusi alimenti esclusi, preferiti e note speciali.
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple
from agent_tools.user_data_manager import UserDataManager
from services.state_service import app_state


class FoodPreferences:
    """Gestisce la logica delle preferenze alimentari dell'utente"""
    
    def __init__(self, user_data_manager):
        """
        Inizializza il gestore delle preferenze alimentari.
        
        Args:
            user_data_manager: Gestore dei dati utente
        """
        self.user_data_manager = user_data_manager
    
    def load_user_preferences(self, user_id: str) -> Dict:
        """
        Carica le preferenze dell'utente dal sistema di persistenza.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dict: Dizionario con le preferenze dell'utente
        """
        return self.user_data_manager.get_user_preferences(user_id) or {}
    
    def initialize_session_preferences(self, user_id: str):
        """
        Inizializza le preferenze nello stato dell'applicazione.
        
        Args:
            user_id: ID dell'utente
        """
        user_preferences = self.load_user_preferences(user_id)
        
        # Usa il nuovo sistema di stato per inizializzare le preferenze
        app_state.initialize_food_preferences(user_preferences)
    
    def add_excluded_food(self, food_name: str) -> bool:
        """
        Aggiunge un alimento alla lista degli esclusi.
        
        Args:
            food_name: Nome dell'alimento da escludere
            
        Returns:
            bool: True se aggiunto con successo, False altrimenti
        """
        if not food_name or not food_name.strip():
            return False
            
        food_name = food_name.strip().lower().title()  # Normalizza il nome
        
        excluded_foods = app_state.get_excluded_foods()
        if food_name not in excluded_foods:
            app_state.add_excluded_food(food_name)
            return True
        return False
    
    def remove_excluded_food(self, index: int) -> bool:
        """
        Rimuove un alimento dalla lista degli esclusi.
        
        Args:
            index: Indice dell'alimento da rimuovere
            
        Returns:
            bool: True se rimosso con successo, False altrimenti
        """
        return app_state.remove_excluded_food(index)
    
    def add_preferred_food(self, food_name: str) -> bool:
        """
        Aggiunge un alimento alla lista dei preferiti.
        
        Args:
            food_name: Nome dell'alimento preferito
            
        Returns:
            bool: True se aggiunto con successo, False altrimenti
        """
        if not food_name or not food_name.strip():
            return False
            
        food_name = food_name.strip().lower().title()  # Normalizza il nome
        
        preferred_foods = app_state.get_preferred_foods()
        if food_name not in preferred_foods:
            app_state.add_preferred_food(food_name)
            return True
        return False
    
    def remove_preferred_food(self, index: int) -> bool:
        """
        Rimuove un alimento dalla lista dei preferiti.
        
        Args:
            index: Indice dell'alimento da rimuovere
            
        Returns:
            bool: True se rimosso con successo, False altrimenti
        """
        return app_state.remove_preferred_food(index)
    
    def get_excluded_foods(self) -> List[str]:
        """
        Ottiene la lista degli alimenti esclusi.
        
        Returns:
            List[str]: Lista degli alimenti esclusi
        """
        return app_state.get_excluded_foods()
    
    def get_preferred_foods(self) -> List[str]:
        """
        Ottiene la lista degli alimenti preferiti.
        
        Returns:
            List[str]: Lista degli alimenti preferiti
        """
        return app_state.get_preferred_foods()
    
    def generate_preferences_prompt(self) -> str:
        """
        Genera un prompt testuale basato sulle preferenze dell'utente.
        Il prompt è del tipo "A me piacciono xxx e non mi piacciono xxx".
        
        Returns:
            str: Il prompt generato.
        """
        preferred = self.get_preferred_foods()
        excluded = self.get_excluded_foods()
        
        parts = []
        if preferred:
            parts.append(f"A me piacciono {', '.join(preferred)}")
        if excluded:
            parts.append(f"non mi piacciono {', '.join(excluded)}")
            
        return " e ".join(parts) if parts else ""

    def save_preferences(self, user_id: str, user_notes: str = "") -> bool:
        """
        Salva tutte le preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
            user_notes: Note aggiuntive dell'utente (deprecato, mantenuto per compatibilità)
            
        Returns:
            bool: True se salvato con successo, False altrimenti
        """
        try:
            preferences = {
                "excluded_foods": self.get_excluded_foods(),
                "preferred_foods": self.get_preferred_foods(),
            }
            
            self.user_data_manager.update_user_preferences(
                user_id=user_id,
                preferences=preferences
            )
            
            # Genera e salva il prompt per il prossimo messaggio
            prompt = self.generate_preferences_prompt()
            if prompt:
                app_state.set('preferences_prompt', prompt)
                app_state.set('prompt_to_add_at_next_message', True)

            return True
        except Exception as e:
            st.error(f"Errore nel salvataggio delle preferenze: {str(e)}")
            return False
    
    def get_user_notes(self, user_id: str) -> str:
        """
        Ottiene le note utente dalle preferenze salvate.
        DEPRECATO: Le note utente sono state rimosse.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            str: Stringa vuota (le note sono state rimosse)
        """
        return ""
    
    def validate_food_name(self, food_name: str) -> Tuple[bool, str]:
        """
        Valida il nome di un alimento.
        
        Args:
            food_name: Nome dell'alimento da validare
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not food_name or not food_name.strip():
            return False, "Il nome dell'alimento non può essere vuoto"
        
        if len(food_name.strip()) < 2:
            return False, "Il nome dell'alimento deve avere almeno 2 caratteri"
        
        if len(food_name.strip()) > 100:
            return False, "Il nome dell'alimento è troppo lungo (max 100 caratteri)"
        
        return True, ""
    
    def clear_all_preferences(self, user_id: str):
        """
        Cancella tutte le preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
        """
        # Cancella dallo stato dell'applicazione
        app_state.set_excluded_foods([])
        app_state.set_preferred_foods([])
        
        # Cancella dal sistema di persistenza
        self.user_data_manager.clear_user_preferences(user_id) 