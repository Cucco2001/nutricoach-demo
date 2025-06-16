"""
Modulo per la gestione della logica delle preferenze alimentari.

Gestisce la validazione, manipolazione e persistenza dei dati delle preferenze
alimentari dell'utente, inclusi alimenti esclusi, preferiti e note speciali.
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple


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
        Inizializza le preferenze nella sessione corrente.
        
        Args:
            user_id: ID dell'utente
        """
        user_preferences = self.load_user_preferences(user_id)
        
        # Inizializza alimenti esclusi nella sessione se non esistono
        if 'excluded_foods_list' not in st.session_state:
            st.session_state.excluded_foods_list = user_preferences.get("excluded_foods", [])
        
        # Inizializza alimenti preferiti nella sessione se non esistono
        if 'preferred_foods_list' not in st.session_state:
            st.session_state.preferred_foods_list = user_preferences.get("preferred_foods", [])
    
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
        
        if food_name not in st.session_state.excluded_foods_list:
            st.session_state.excluded_foods_list.append(food_name)
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
        try:
            if 0 <= index < len(st.session_state.excluded_foods_list):
                st.session_state.excluded_foods_list.pop(index)
                return True
        except (IndexError, KeyError):
            pass
        return False
    
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
        
        if food_name not in st.session_state.preferred_foods_list:
            st.session_state.preferred_foods_list.append(food_name)
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
        try:
            if 0 <= index < len(st.session_state.preferred_foods_list):
                st.session_state.preferred_foods_list.pop(index)
                return True
        except (IndexError, KeyError):
            pass
        return False
    
    def get_excluded_foods(self) -> List[str]:
        """
        Ottiene la lista degli alimenti esclusi.
        
        Returns:
            List[str]: Lista degli alimenti esclusi
        """
        return st.session_state.get('excluded_foods_list', [])
    
    def get_preferred_foods(self) -> List[str]:
        """
        Ottiene la lista degli alimenti preferiti.
        
        Returns:
            List[str]: Lista degli alimenti preferiti
        """
        return st.session_state.get('preferred_foods_list', [])
    
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
        # Cancella dalla sessione
        if 'excluded_foods_list' in st.session_state:
            del st.session_state.excluded_foods_list
        if 'preferred_foods_list' in st.session_state:
            del st.session_state.preferred_foods_list
        
        # Cancella dal sistema di persistenza
        self.user_data_manager.clear_user_preferences(user_id) 