"""
AppStateManager - Gestisce lo stato interno dell'applicazione.

Questo modulo sostituisce gradualmente st.session_state per permettere
in futuro l'uso di frontend diversi (React, Vue, ecc.).
"""

from typing import Any, Dict, Optional
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserInfo:
    """Informazioni utente autenticato"""
    id: str
    username: str
    email: str = ""
    età: Optional[int] = None
    sesso: Optional[str] = None
    peso: Optional[float] = None
    altezza: Optional[int] = None
    attività: Optional[str] = None
    obiettivo: Optional[str] = None
    preferences: Optional[Dict] = None


class AppStateManager:
    """
    Manager per lo stato interno dell'applicazione.
    
    Sostituisce gradualmente st.session_state per disaccoppiare
    la logica di business dal frontend Streamlit.
    """
    
    _instance: Optional['AppStateManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._state: Dict[str, Any] = {}
            self._initialized = True
            self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Inizializza i valori di default dello stato"""
        self._state.update({
            # UI State
            'current_page': 'Chat',
            'agent_generating': False,
            'device_type': 'desktop',
            'just_completed_initial_info': False,
            
            # User State
            'user_info': None,
            'is_authenticated': False,
            
            # Chat State
            'messages': [],
            'current_question': 0,
            'nutrition_answers': {},
            
            # Navigation State
            'current_run_id': None,
            'agent_response_ready': False,
            'agent_response_text': None,
            'pending_user_input': None,
            
            # Tutorial State
            'tutorial_completed': False,
            
            # Misc
            'diet_plan': None,
        })
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene un valore dallo stato"""
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Imposta un valore nello stato"""
        self._state[key] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """Aggiorna multipli valori dello stato"""
        self._state.update(data)
    
    def delete(self, key: str) -> None:
        """Rimuove una chiave dallo stato"""
        if key in self._state:
            del self._state[key]
    
    def exists(self, key: str) -> bool:
        """Verifica se una chiave esiste nello stato"""
        return key in self._state
    
    def clear(self) -> None:
        """Resetta tutto lo stato ai valori di default"""
        self._state.clear()
        self._initialize_defaults()
    
    # === METODI CONVENIENCE PER STATI SPECIFICI ===
    
    def get_current_page(self) -> str:
        """Ottiene la pagina corrente"""
        return self.get('current_page', 'Chat')
    
    def set_current_page(self, page: str) -> None:
        """Imposta la pagina corrente"""
        self.set('current_page', page)
    
    def is_agent_generating(self) -> bool:
        """Verifica se l'agente sta generando"""
        return self.get('agent_generating', False)
    
    def set_agent_generating(self, generating: bool) -> None:
        """Imposta lo stato di generazione dell'agente"""
        self.set('agent_generating', generating)
    
    def get_user_info(self) -> Optional[UserInfo]:
        """Ottiene le informazioni utente"""
        user_data = self.get('user_info')
        if user_data and isinstance(user_data, dict):
            return UserInfo(**user_data)
        return user_data
    
    def set_user_info(self, user_info: Optional[UserInfo]) -> None:
        """Imposta le informazioni utente"""
        if user_info is None:
            self.set('user_info', None)
            self.set('is_authenticated', False)
        else:
            if isinstance(user_info, UserInfo):
                self.set('user_info', user_info.__dict__)
            else:
                self.set('user_info', user_info)
            self.set('is_authenticated', True)
    
    def is_user_authenticated(self) -> bool:
        """Verifica se l'utente è autenticato"""
        return self.get('is_authenticated', False) and self.get('user_info') is not None
    
    def get_messages(self) -> list:
        """Ottiene i messaggi della chat"""
        return self.get('messages', [])
    
    def add_message(self, role: str, content: str) -> None:
        """Aggiunge un messaggio alla chat"""
        messages = self.get_messages()
        messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        self.set('messages', messages)
    
    def clear_messages(self) -> None:
        """Pulisce i messaggi della chat"""
        self.set('messages', [])
    
    def get_current_question(self) -> int:
        """Ottiene la domanda corrente del questionario"""
        return self.get('current_question', 0)
    
    def set_current_question(self, question: int) -> None:
        """Imposta la domanda corrente del questionario"""
        self.set('current_question', question)
    
    def get_nutrition_answers(self) -> Dict:
        """Ottiene le risposte del questionario nutrizionale"""
        return self.get('nutrition_answers', {})
    
    def set_nutrition_answers(self, answers: Dict) -> None:
        """Imposta le risposte del questionario nutrizionale"""
        self.set('nutrition_answers', answers)
    
    def add_nutrition_answer(self, question_id: str, answer: Any) -> None:
        """Aggiunge una risposta al questionario nutrizionale"""
        answers = self.get_nutrition_answers()
        answers[question_id] = answer
        self.set('nutrition_answers', answers)
    
    # === METODI PER PREFERENZE ALIMENTARI ===
    
    def get_excluded_foods(self) -> list:
        """Ottiene la lista degli alimenti esclusi"""
        return self.get('excluded_foods_list', [])
    
    def set_excluded_foods(self, foods: list) -> None:
        """Imposta la lista degli alimenti esclusi"""
        self.set('excluded_foods_list', foods)
    
    def add_excluded_food(self, food_name: str) -> None:
        """Aggiunge un alimento alla lista degli esclusi"""
        excluded = self.get_excluded_foods()
        if food_name not in excluded:
            excluded.append(food_name)
            self.set_excluded_foods(excluded)
    
    def remove_excluded_food(self, index: int) -> bool:
        """Rimuove un alimento dalla lista degli esclusi"""
        excluded = self.get_excluded_foods()
        if 0 <= index < len(excluded):
            excluded.pop(index)
            self.set_excluded_foods(excluded)
            return True
        return False
    
    def get_preferred_foods(self) -> list:
        """Ottiene la lista degli alimenti preferiti"""
        return self.get('preferred_foods_list', [])
    
    def set_preferred_foods(self, foods: list) -> None:
        """Imposta la lista degli alimenti preferiti"""
        self.set('preferred_foods_list', foods)
    
    def add_preferred_food(self, food_name: str) -> None:
        """Aggiunge un alimento alla lista dei preferiti"""
        preferred = self.get_preferred_foods()
        if food_name not in preferred:
            preferred.append(food_name)
            self.set_preferred_foods(preferred)
    
    def remove_preferred_food(self, index: int) -> bool:
        """Rimuove un alimento dalla lista dei preferiti"""
        preferred = self.get_preferred_foods()
        if 0 <= index < len(preferred):
            preferred.pop(index)
            self.set_preferred_foods(preferred)
            return True
        return False
    
    def initialize_food_preferences(self, user_preferences: Dict) -> None:
        """Inizializza le preferenze alimentari dai dati utente"""
        if 'excluded_foods_list' not in self._state:
            self.set_excluded_foods(user_preferences.get("excluded_foods", []))
        if 'preferred_foods_list' not in self._state:
            self.set_preferred_foods(user_preferences.get("preferred_foods", []))

    # === METODI DEBUG ===
    
    def get_all_state(self) -> Dict[str, Any]:
        """Ottiene tutto lo stato (per debug)"""
        return self._state.copy()
    
    def print_state(self) -> None:
        """Stampa lo stato attuale (per debug)"""
        print("=== APP STATE ===")
        for key, value in self._state.items():
            print(f"{key}: {value}")
        print("================")


# Istanza singleton globale
app_state = AppStateManager() 