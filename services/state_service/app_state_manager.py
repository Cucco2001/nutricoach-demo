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
            
            # Sports State
            'sports_data': None,
            'sports_by_category': None,
            'sports_list': [],
            
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
        messages = self.get('messages', [])
        # Assicurati che restituisca sempre una lista
        return messages if messages is not None else []
    
    def set_messages(self, messages: list) -> None:
        """Imposta i messaggi della chat"""
        self.set('messages', messages)
    
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

    # === METODI PER TUTORIAL ===
    
    def is_tutorial_completed(self, user_id: str) -> bool:
        """Verifica se il tutorial è stato completato per un utente"""
        tutorial_key = f"tutorial_completed_{user_id}"
        return self.get(tutorial_key, False)
    
    def set_tutorial_completed(self, user_id: str, completed: bool = True) -> None:
        """Imposta lo stato di completamento del tutorial per un utente"""
        tutorial_key = f"tutorial_completed_{user_id}"
        self.set(tutorial_key, completed)
    
    def is_tutorial_section_visited(self, user_id: str, section: str) -> bool:
        """Verifica se una sezione del tutorial è stata visitata"""
        section_key = f"tutorial_{section}_visited_{user_id}"
        return self.get(section_key, False)
    
    def set_tutorial_section_visited(self, user_id: str, section: str, visited: bool = True) -> None:
        """Imposta lo stato di visita di una sezione del tutorial"""
        section_key = f"tutorial_{section}_visited_{user_id}"
        self.set(section_key, visited)
    
    def are_all_tutorial_sections_visited(self, user_id: str) -> bool:
        """Verifica se tutte le sezioni del tutorial sono state visitate"""
        sections = ['chat', 'preferences', 'plan']
        return all(self.is_tutorial_section_visited(user_id, section) for section in sections)
    
    def reset_tutorial(self, user_id: str) -> None:
        """Resetta lo stato del tutorial per un utente"""
        tutorial_keys = [
            f"tutorial_completed_{user_id}",
            f"tutorial_chat_visited_{user_id}",
            f"tutorial_preferences_visited_{user_id}",
            f"tutorial_plan_visited_{user_id}"
        ]
        for key in tutorial_keys:
            self.delete(key)

    # === METODI PER SPORTS ===
    
    def get_sports_data(self) -> Optional[Dict]:
        """Ottiene i dati degli sport"""
        return self.get('sports_data')
    
    def set_sports_data(self, sports_data: Dict, sports_by_category: Dict) -> None:
        """Imposta i dati degli sport"""
        self.set('sports_data', sports_data)
        self.set('sports_by_category', sports_by_category)
    
    def get_sports_by_category(self) -> Optional[Dict]:
        """Ottiene gli sport organizzati per categoria"""
        return self.get('sports_by_category')
    
    def get_sports_list(self) -> list:
        """Ottiene la lista degli sport dell'utente"""
        return self.get('sports_list', [])
    
    def set_sports_list(self, sports_list: list) -> None:
        """Imposta la lista degli sport dell'utente"""
        self.set('sports_list', sports_list)
    
    def add_sport_to_list(self, sport_data: Dict) -> None:
        """Aggiunge uno sport alla lista dell'utente"""
        sports_list = self.get_sports_list()
        sports_list.append(sport_data)
        self.set_sports_list(sports_list)
    
    def update_sport_in_list(self, index: int, sport_data: Dict) -> bool:
        """Aggiorna uno sport nella lista dell'utente"""
        sports_list = self.get_sports_list()
        if 0 <= index < len(sports_list):
            sports_list[index] = sport_data
            self.set_sports_list(sports_list)
            return True
        return False
    
    def remove_sport_from_list(self, index: int) -> bool:
        """Rimuove uno sport dalla lista dell'utente"""
        sports_list = self.get_sports_list()
        if 0 <= index < len(sports_list):
            sports_list.pop(index)
            self.set_sports_list(sports_list)
            return True
        return False

    # === METODI PER SERVICES ===
    
    def get_user_data_manager(self):
        """Ottiene il manager dei dati utente"""
        return self.get('user_data_manager')
    
    def set_user_data_manager(self, manager) -> None:
        """Imposta il manager dei dati utente"""
        self.set('user_data_manager', manager)
    
    def get_deepseek_manager(self):
        """Ottiene il manager DeepSeek"""
        return self.get('deepseek_manager')
    
    def set_deepseek_manager(self, manager) -> None:
        """Imposta il manager DeepSeek"""
        self.set('deepseek_manager', manager)
    
    def get_chat_manager(self):
        """Ottiene il manager della chat"""
        return self.get('chat_manager')
    
    def set_chat_manager(self, manager) -> None:
        """Imposta il manager della chat"""
        self.set('chat_manager', manager)
    
    def get_preferences_manager(self):
        """Ottiene il manager delle preferenze"""
        return self.get('preferences_manager')
    
    def set_preferences_manager(self, manager) -> None:
        """Imposta il manager delle preferenze"""
        self.set('preferences_manager', manager)
    
    def get_supabase_service(self):
        """Ottiene il servizio Supabase"""
        return self.get('supabase_service')
    
    def set_supabase_service(self, service) -> None:
        """Imposta il servizio Supabase"""
        self.set('supabase_service', service)
    
    def get_openai_client(self):
        """Ottiene il client OpenAI"""
        return self.get('openai_client')
    
    def set_openai_client(self, client) -> None:
        """Imposta il client OpenAI"""
        self.set('openai_client', client)
    
    def get_assistant_manager(self):
        """Ottiene il manager dell'assistente"""
        return self.get('assistant_manager')
    
    def set_assistant_manager(self, manager) -> None:
        """Imposta il manager dell'assistente"""
        self.set('assistant_manager', manager)
    
    def get_token_tracker(self):
        """Ottiene il tracker dei token"""
        return self.get('token_tracker')
    
    def set_token_tracker(self, tracker) -> None:
        """Imposta il tracker dei token"""
        self.set('token_tracker', tracker)

    # === METODI PER THREAD E RUNS ===
    
    def get_thread_id(self) -> Optional[str]:
        """Ottiene l'ID del thread corrente"""
        return self.get('thread_id')
    
    def set_thread_id(self, thread_id: str) -> None:
        """Imposta l'ID del thread corrente"""
        self.set('thread_id', thread_id)
    
    def get_current_run_id(self) -> Optional[str]:
        """Ottiene l'ID del run corrente"""
        return self.get('current_run_id')
    
    def set_current_run_id(self, run_id: str) -> None:
        """Imposta l'ID del run corrente"""
        self.set('current_run_id', run_id)
    
    def get_pending_user_input(self) -> Optional[str]:
        """Ottiene l'input utente pendente"""
        return self.get('pending_user_input')
    
    def set_pending_user_input(self, user_input: str) -> None:
        """Imposta l'input utente pendente"""
        self.set('pending_user_input', user_input)

    # === METODI PER FLAGS TEMPORANEI ===
    
    def is_registration_successful(self) -> bool:
        """Verifica se la registrazione è stata completata con successo"""
        return self.get('registration_successful', False)
    
    def set_registration_successful(self, successful: bool = True) -> None:
        """Imposta il flag di registrazione completata"""
        self.set('registration_successful', successful)
    
    def is_just_completed_initial_info(self) -> bool:
        """Verifica se l'utente ha appena completato le info iniziali"""
        return self.get('just_completed_initial_info', False)
    
    def set_just_completed_initial_info(self, completed: bool = True) -> None:
        """Imposta il flag di completamento info iniziali"""
        self.set('just_completed_initial_info', completed)

    # === METODI PER TOKEN TRACKING E INTERAZIONI ===
    
    def get_interaction_count(self) -> int:
        """Ottiene il conteggio delle interazioni"""
        return self.get('interaction_count', 0)
    
    def set_interaction_count(self, count: int) -> None:
        """Imposta il conteggio delle interazioni"""
        self.set('interaction_count', count)
    
    def increment_interaction_count(self) -> int:
        """Incrementa il conteggio delle interazioni e restituisce il nuovo valore"""
        current = self.get_interaction_count()
        new_count = current + 1
        self.set_interaction_count(new_count)
        return new_count
    
    def get_last_extraction_count(self) -> int:
        """Ottiene il conteggio dell'ultima estrazione"""
        return self.get('last_extraction_count', 0)
    
    def set_last_extraction_count(self, count: int) -> None:
        """Imposta il conteggio dell'ultima estrazione"""
        self.set('last_extraction_count', count)

    # === METODI PER DEEPSEEK LEGACY ===
    
    def get_deepseek_client(self):
        """Ottiene il client DeepSeek legacy"""
        return self.get('deepseek_client')
    
    def set_deepseek_client(self, client) -> None:
        """Imposta il client DeepSeek legacy"""
        self.set('deepseek_client', client)
    
    def get_deepseek_queue(self):
        """Ottiene la coda DeepSeek"""
        return self.get('deepseek_queue')
    
    def set_deepseek_queue(self, queue) -> None:
        """Imposta la coda DeepSeek"""
        self.set('deepseek_queue', queue)
    
    def get_deepseek_results(self) -> dict:
        """Ottiene i risultati DeepSeek"""
        return self.get('deepseek_results', {})
    
    def set_deepseek_results(self, results: dict) -> None:
        """Imposta i risultati DeepSeek"""
        self.set('deepseek_results', results)

    # === METODI PER VARIABILI TEMPORANEE ===
    
    def get_diet_plan(self):
        """Ottiene il piano dietetico"""
        return self.get('diet_plan')
    
    def set_diet_plan(self, diet_plan) -> None:
        """Imposta il piano dietetico"""
        self.set('diet_plan', diet_plan)
    
    def get_agent_response_ready(self) -> bool:
        """Verifica se la risposta dell'agente è pronta"""
        return self.get('agent_response_ready', False)
    
    def set_agent_response_ready(self, ready: bool) -> None:
        """Imposta se la risposta dell'agente è pronta"""
        self.set('agent_response_ready', ready)
    
    def get_agent_response_text(self) -> str:
        """Ottiene il testo della risposta dell'agente"""
        return self.get('agent_response_text')
    
    def set_agent_response_text(self, text: str) -> None:
        """Imposta il testo della risposta dell'agente"""
        self.set('agent_response_text', text)
    
    def get_agent_user_input(self) -> str:
        """Ottiene l'input utente per l'agente"""
        return self.get('agent_user_input')
    
    def set_agent_user_input(self, user_input: str) -> None:
        """Imposta l'input utente per l'agente"""
        self.set('agent_user_input', user_input)
    
    def get_agent_thread_id(self) -> str:
        """Ottiene l'ID del thread dell'agente"""
        return self.get('agent_thread_id')
    
    def set_agent_thread_id(self, thread_id: str) -> None:
        """Imposta l'ID del thread dell'agente"""
        self.set('agent_thread_id', thread_id)

    # === METODI PER VARIABILI TEMPORANEE DEEPSEEK ===
    
    def get_deepseek_processing_shown(self, user_id: str) -> bool:
        """Verifica se il processing DeepSeek è già stato mostrato per l'utente"""
        return self.get(f'deepseek_processing_shown_{user_id}', False)
    
    def set_deepseek_processing_shown(self, user_id: str, shown: bool) -> None:
        """Imposta se il processing DeepSeek è stato mostrato per l'utente"""
        self.set(f'deepseek_processing_shown_{user_id}', shown)
    
    def get_last_extraction_start(self, user_id: str) -> float:
        """Ottiene il timestamp dell'ultima estrazione per l'utente"""
        return self.get(f'last_extraction_start_{user_id}', 0)
    
    def set_last_extraction_start(self, user_id: str, timestamp: float) -> None:
        """Imposta il timestamp dell'ultima estrazione per l'utente"""
        self.set(f'last_extraction_start_{user_id}', timestamp)
    
    def clear_deepseek_processing_shown(self, user_id: str) -> None:
        """Cancella il flag di processing mostrato per l'utente"""
        key = f'deepseek_processing_shown_{user_id}'
        if key in self._state:
            del self._state[key]

    # === METODI PER DEVICE DETECTION ===
    
    def get_device_type(self) -> str:
        """Ottiene il tipo di dispositivo"""
        return self.get('device_type', 'desktop')
    
    def set_device_type(self, device_type: str) -> None:
        """Imposta il tipo di dispositivo"""
        self.set('device_type', device_type)
    
    def get_force_device_type(self) -> str:
        """Ottiene il tipo di dispositivo forzato"""
        return self.get('force_device_type')
    
    def set_force_device_type(self, device_type: str) -> None:
        """Imposta il tipo di dispositivo forzato"""
        self.set('force_device_type', device_type)
    
    def is_device_choice_made(self) -> bool:
        """Verifica se la scelta del dispositivo è stata fatta"""
        return self.get('device_choice_made', False)
    
    def set_device_choice_made(self, made: bool) -> None:
        """Imposta se la scelta del dispositivo è stata fatta"""
        self.set('device_choice_made', made)

    # === METODI PER GESTIONE SPORT SPECIFICI ===
    
    def get_specific_sport(self, index: int) -> Optional[str]:
        """Ottiene la selezione specifica di sport per un indice"""
        return self.get(f'specific_sport_{index}')
    
    def set_specific_sport(self, index: int, sport: str) -> None:
        """Imposta la selezione specifica di sport per un indice"""
        self.set(f'specific_sport_{index}', sport)
    
    def delete_specific_sport(self, index: int) -> None:
        """Rimuove la selezione specifica di sport per un indice"""
        self.delete(f'specific_sport_{index}')
    
    def get_sport_type(self, index: int) -> Optional[str]:
        """Ottiene il tipo di sport per un indice"""
        return self.get(f'sport_type_{index}')
    
    def set_sport_type(self, index: int, sport_type: str) -> None:
        """Imposta il tipo di sport per un indice"""
        self.set(f'sport_type_{index}', sport_type)
    
    # === METODI PER GESTIONE PROMPT PREFERENZE ===
    
    def get_preferences_prompt(self) -> Optional[str]:
        """Ottiene il prompt delle preferenze"""
        return self.get('preferences_prompt')
    
    def set_preferences_prompt(self, prompt: str) -> None:
        """Imposta il prompt delle preferenze"""
        self.set('preferences_prompt', prompt)
    
    def delete_preferences_prompt(self) -> None:
        """Rimuove il prompt delle preferenze"""
        self.delete('preferences_prompt')
    
    def get_prompt_to_add_at_next_message(self) -> Optional[str]:
        """Ottiene il prompt da aggiungere al prossimo messaggio"""
        return self.get('prompt_to_add_at_next_message')
    
    def set_prompt_to_add_at_next_message(self, prompt: str) -> None:
        """Imposta il prompt da aggiungere al prossimo messaggio"""
        self.set('prompt_to_add_at_next_message', prompt)
    
    def delete_prompt_to_add_at_next_message(self) -> None:
        """Rimuove il prompt da aggiungere al prossimo messaggio"""
        self.delete('prompt_to_add_at_next_message')

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