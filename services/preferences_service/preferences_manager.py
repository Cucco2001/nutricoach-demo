"""
Manager principale per il servizio di gestione delle preferenze.

Questo modulo fornisce un'interfaccia unificata per la gestione delle preferenze
alimentari dell'utente, coordinando la logica dei dati e l'interfaccia utente.
"""

from typing import Tuple
from .food_preferences import FoodPreferences
from .preferences_ui import PreferencesUI


class PreferencesManager:
    """
    Manager principale per la gestione delle preferenze alimentari.
    
    Coordina la logica dei dati (FoodPreferences) e l'interfaccia utente (PreferencesUI)
    per fornire un'API unificata per la gestione delle preferenze dell'utente.
    """
    
    def __init__(self, user_data_manager):
        """
        Inizializza il manager delle preferenze.
        
        Args:
            user_data_manager: Gestore dei dati utente per la persistenza
        """
        self.food_preferences = FoodPreferences(user_data_manager)
        self.preferences_ui = PreferencesUI(self.food_preferences)
    
    def handle_user_preferences(self, user_id: str):
        """
        Gestisce l'interfaccia completa delle preferenze utente.
        
        Questo metodo sostituisce la funzione handle_preferences() originale di app.py
        
        Args:
            user_id: ID dell'utente
        """
        self.preferences_ui.display_preferences_interface(user_id)
    
    def get_preferences_summary(self, user_id: str):
        """
        Ottiene un riassunto delle preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
        """
        self.preferences_ui.display_preferences_summary(user_id)
    
    def get_compact_preferences(self, user_id: str):
        """
        Mostra le preferenze in formato compatto.
        
        Args:
            user_id: ID dell'utente
        """
        self.preferences_ui.display_compact_preferences(user_id)
    
    def get_preferences_for_agent(self, user_id: str) -> str:
        """
        Formatta le preferenze per l'agente nutrizionale.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            str: Preferenze formattate per l'agente
        """
        return self.preferences_ui.display_preferences_for_agent(user_id) or ""
    
    def initialize_user_preferences(self, user_id: str):
        """
        Inizializza le preferenze dell'utente nella sessione.
        
        Args:
            user_id: ID dell'utente
        """
        self.food_preferences.initialize_session_preferences(user_id)
    
    def add_excluded_food(self, food_name: str) -> bool:
        """
        Aggiunge un alimento alla lista degli esclusi.
        
        Args:
            food_name: Nome dell'alimento da escludere
            
        Returns:
            bool: True se aggiunto con successo
        """
        return self.food_preferences.add_excluded_food(food_name)
    
    def add_preferred_food(self, food_name: str) -> bool:
        """
        Aggiunge un alimento alla lista dei preferiti.
        
        Args:
            food_name: Nome dell'alimento preferito
            
        Returns:
            bool: True se aggiunto con successo
        """
        return self.food_preferences.add_preferred_food(food_name)
    
    def remove_excluded_food(self, index: int) -> bool:
        """
        Rimuove un alimento dalla lista degli esclusi.
        
        Args:
            index: Indice dell'alimento da rimuovere
            
        Returns:
            bool: True se rimosso con successo
        """
        return self.food_preferences.remove_excluded_food(index)
    
    def remove_preferred_food(self, index: int) -> bool:
        """
        Rimuove un alimento dalla lista dei preferiti.
        
        Args:
            index: Indice dell'alimento da rimuovere
            
        Returns:
            bool: True se rimosso con successo
        """
        return self.food_preferences.remove_preferred_food(index)
    
    def save_preferences(self, user_id: str, user_notes: str = "") -> bool:
        """
        Salva tutte le preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
            user_notes: Note aggiuntive dell'utente (deprecato, mantenuto per compatibilità)
            
        Returns:
            bool: True se salvato con successo
        """
        return self.food_preferences.save_preferences(user_id, user_notes)
    
    def get_excluded_foods(self) -> list:
        """
        Ottiene la lista degli alimenti esclusi.
        
        Returns:
            list: Lista degli alimenti esclusi
        """
        return self.food_preferences.get_excluded_foods()
    
    def get_preferred_foods(self) -> list:
        """
        Ottiene la lista degli alimenti preferiti.
        
        Returns:
            list: Lista degli alimenti preferiti
        """
        return self.food_preferences.get_preferred_foods()
    
    def get_user_notes(self, user_id: str) -> str:
        """
        Ottiene le note utente.
        DEPRECATO: Le note utente sono state rimosse.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            str: Stringa vuota (le note sono state rimosse)
        """
        return ""
    
    def clear_all_preferences(self, user_id: str):
        """
        Cancella tutte le preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
        """
        self.food_preferences.clear_all_preferences(user_id)
    
    def validate_food_name(self, food_name: str) -> Tuple[bool, str]:
        """
        Valida il nome di un alimento.
        
        Args:
            food_name: Nome dell'alimento da validare
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        return self.food_preferences.validate_food_name(food_name)
    
    def load_user_preferences(self, user_id: str) -> dict:
        """
        Carica le preferenze dell'utente dal sistema di persistenza.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Dizionario con le preferenze dell'utente
        """
        return self.food_preferences.load_user_preferences(user_id) 