import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Union, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class User:
    username: str
    password_hash: str
    user_id: str
    created_at: float

@dataclass
class MealFeedback:
    satisfaction_level: int
    notes: Optional[str]
    timestamp: float

@dataclass
class ProgressEntry:
    date: str
    weight: float
    measurements: Dict[str, float]

@dataclass
class UserPreferences:
    excluded_foods: Set[str]
    preferred_foods: Set[str]
    meal_times: Dict[str, str]
    portion_sizes: Dict[str, str]
    cooking_methods: Set[str]

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float

@dataclass
class AgentQA:
    question: str
    answer: str
    timestamp: float

@dataclass
class UserNutritionalInfo:
    età: int
    sesso: str
    peso: float
    altezza: int
    attività: str
    obiettivo: str
    nutrition_answers: Dict[str, Union[str, Dict]]
    agent_qa: List[AgentQA] = None  # Make agent_qa optional with default None

    def __post_init__(self):
        if self.agent_qa is None:
            self.agent_qa = []  # Initialize empty list if None

class UserDataManager:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._users: Dict[str, User] = {}  # username -> User
        self._meal_feedback: Dict[str, Dict[str, MealFeedback]] = {}
        self._progress_data: Dict[str, List[ProgressEntry]] = {}
        self._user_preferences: Dict[str, UserPreferences] = {}
        self._chat_history: Dict[str, List[ChatMessage]] = {}
        self._nutritional_info: Dict[str, UserNutritionalInfo] = {}
        self._load_users()

    def _hash_password(self, password: str) -> str:
        """Crea un hash sicuro della password"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self) -> None:
        """Carica la lista degli utenti dal file"""
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                self._users = {
                    username: User(**user_data)
                    for username, user_data in users_data.items()
                }

    def _save_users(self) -> None:
        """Salva la lista degli utenti su file"""
        users_file = self.data_dir / "users.json"
        users_data = {
            username: asdict(user)
            for username, user in self._users.items()
        }
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)

    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Registra un nuovo utente
        
        Args:
            username: Nome utente
            password: Password
            
        Returns:
            Tuple[bool, str]: (successo, messaggio)
        """
        if username in self._users:
            return False, "Username già in uso"
        
        if len(password) < 8:
            return False, "La password deve essere di almeno 8 caratteri"
        
        user_id = f"user_{int(time.time())}"
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            user_id=user_id,
            created_at=time.time()
        )
        
        self._users[username] = user
        self._save_users()
        return True, user_id

    def login_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Autentica un utente
        
        Args:
            username: Nome utente
            password: Password
            
        Returns:
            Tuple[bool, str]: (successo, user_id)
        """
        if username not in self._users:
            return False, "Utente non trovato"
        
        user = self._users[username]
        if user.password_hash != self._hash_password(password):
            return False, "Password non corretta"
        
        # Carica i dati dell'utente
        self._load_user_data(user.user_id)
        return True, user.user_id

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Recupera un utente dal suo ID"""
        for user in self._users.values():
            if user.user_id == user_id:
                return user
        return None

    def collect_meal_feedback(self, user_id: str, meal_id: str, satisfaction_level: int, notes: Optional[str] = None) -> None:
        """
        Raccoglie feedback sui pasti per migliorare le raccomandazioni future
        
        Args:
            user_id: ID dell'utente
            meal_id: ID del pasto
            satisfaction_level: Livello di soddisfazione (1-5)
            notes: Note opzionali sul pasto
        """
        if not 1 <= satisfaction_level <= 5:
            raise ValueError("Il livello di soddisfazione deve essere tra 1 e 5")

        feedback = MealFeedback(
            satisfaction_level=satisfaction_level,
            notes=notes,
            timestamp=time.time()
        )
        
        if user_id not in self._meal_feedback:
            self._meal_feedback[user_id] = {}
        
        self._meal_feedback[user_id][meal_id] = feedback
        self._save_user_data(user_id)

    def track_progress(self, user_id: str, weight: float, date: str, measurements: Optional[Dict[str, float]] = None) -> None:
        """
        Traccia il progresso dell'utente nel tempo
        
        Args:
            user_id: ID dell'utente
            weight: Peso in kg
            date: Data della misurazione (formato YYYY-MM-DD)
            measurements: Dizionario opzionale con altre misurazioni
        """
        if weight <= 0:
            raise ValueError("Il peso deve essere positivo")

        entry = ProgressEntry(
            date=date,
            weight=weight,
            measurements=measurements or {}
        )

        if user_id not in self._progress_data:
            self._progress_data[user_id] = []
        
        self._progress_data[user_id].append(entry)
        self._save_user_data(user_id)

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Union[Set[str], Dict[str, str]]]) -> None:
        """
        Aggiorna le preferenze alimentari dell'utente
        
        Args:
            user_id: ID dell'utente
            preferences: Dizionario con le nuove preferenze
        """
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserPreferences(
                excluded_foods=set(),
                preferred_foods=set(),
                meal_times={},
                portion_sizes={},
                cooking_methods=set()
            )

        current_prefs = self._user_preferences[user_id]
        
        for category, items in preferences.items():
            if hasattr(current_prefs, category):
                if isinstance(getattr(current_prefs, category), set):
                    getattr(current_prefs, category).update(items)
                else:
                    getattr(current_prefs, category).update(items)
            else:
                raise ValueError(f"Categoria preferenze non valida: {category}")

        self._save_user_data(user_id)

    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Recupera le preferenze dell'utente"""
        return self._user_preferences.get(user_id)

    def get_progress_history(self, user_id: str) -> List[ProgressEntry]:
        """Recupera la storia dei progressi dell'utente"""
        return self._progress_data.get(user_id, [])

    def delete_progress_entry(self, user_id: str, date: str) -> bool:
        """
        Elimina una voce di progresso per data specifica
        
        Args:
            user_id: ID dell'utente
            date: Data della voce da eliminare (formato YYYY-MM-DD)
            
        Returns:
            bool: True se l'eliminazione è avvenuta con successo, False se la voce non è stata trovata
        """
        if user_id not in self._progress_data:
            return False
        
        # Trova l'indice della voce da eliminare
        for i, entry in enumerate(self._progress_data[user_id]):
            if entry.date == date:
                del self._progress_data[user_id][i]
                self._save_user_data(user_id)
                return True
        
        return False

    def get_meal_feedback(self, user_id: str, meal_id: str) -> Optional[MealFeedback]:
        """Recupera il feedback per un pasto specifico"""
        return self._meal_feedback.get(user_id, {}).get(meal_id)

    def save_chat_message(self, user_id: str, role: str, content: str) -> None:
        """
        Salva un messaggio della chat nella history dell'utente
        
        Args:
            user_id: ID dell'utente
            role: Ruolo del messaggio ('user' o 'assistant')
            content: Contenuto del messaggio
        """
        if user_id not in self._chat_history:
            self._chat_history[user_id] = []
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=time.time()
        )
        
        self._chat_history[user_id].append(message)
        self._save_user_data(user_id)

    def get_chat_history(self, user_id: str) -> List[ChatMessage]:
        """
        Recupera la history della chat dell'utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Lista di messaggi della chat
        """
        return self._chat_history.get(user_id, [])

    def clear_chat_history(self, user_id: str) -> None:
        """
        Cancella la history della chat dell'utente
        
        Args:
            user_id: ID dell'utente
        """
        if user_id in self._chat_history:
            self._chat_history[user_id] = []
            self._save_user_data(user_id)

    def save_agent_qa(self, user_id: str, question: str, answer: str) -> None:
        """
        Salva una domanda e risposta dell'agente
        
        Args:
            user_id: ID dell'utente
            question: Domanda dell'agente
            answer: Risposta dell'utente
        """
        if user_id not in self._nutritional_info:
            return
        
        if not hasattr(self._nutritional_info[user_id], 'agent_qa'):
            self._nutritional_info[user_id].agent_qa = []
        
        qa = AgentQA(
            question=question,
            answer=answer,
            timestamp=time.time()
        )
        
        self._nutritional_info[user_id].agent_qa.append(qa)
        self._save_user_data(user_id)

    def get_agent_qa(self, user_id: str) -> List[AgentQA]:
        """
        Recupera le domande e risposte dell'agente per un utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Lista di domande e risposte
        """
        if user_id not in self._nutritional_info:
            return []
        return getattr(self._nutritional_info[user_id], 'agent_qa', [])

    def save_nutritional_info(self, user_id: str, info: Dict) -> None:
        """
        Salva le informazioni nutrizionali dell'utente
        
        Args:
            user_id: ID dell'utente
            info: Dizionario con le informazioni nutrizionali
        """
        # Mantieni le domande e risposte dell'agente esistenti
        existing_qa = []
        if user_id in self._nutritional_info:
            existing_qa = getattr(self._nutritional_info[user_id], 'agent_qa', [])
        
        nutritional_info = UserNutritionalInfo(
            età=info["età"],
            sesso=info["sesso"],
            peso=info["peso"],
            altezza=info["altezza"],
            attività=info["attività"],
            obiettivo=info["obiettivo"],
            nutrition_answers=info.get("nutrition_answers", {}),
            agent_qa=existing_qa  # Mantieni le domande e risposte esistenti
        )
        
        self._nutritional_info[user_id] = nutritional_info
        self._save_user_data(user_id)

    def get_nutritional_info(self, user_id: str) -> Optional[UserNutritionalInfo]:
        """
        Recupera le informazioni nutrizionali dell'utente
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            UserNutritionalInfo o None se non trovato
        """
        return self._nutritional_info.get(user_id)

    def _save_user_data(self, user_id: str) -> None:
        """Salva i dati dell'utente su file"""
        user_file = self.data_dir / f"{user_id}.json"
        
        data = {
            "meal_feedback": {
                meal_id: asdict(feedback)
                for meal_id, feedback in self._meal_feedback.get(user_id, {}).items()
            },
            "progress_data": [
                asdict(entry) for entry in self._progress_data.get(user_id, [])
            ],
            "user_preferences": asdict(self._user_preferences.get(user_id)) if user_id in self._user_preferences else None,
            "chat_history": [
                asdict(message) for message in self._chat_history.get(user_id, [])
            ],
            "nutritional_info": asdict(self._nutritional_info.get(user_id)) if user_id in self._nutritional_info else None
        }
        
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_user_data(self, user_id: str) -> None:
        """Carica i dati dell'utente da file"""
        user_file = self.data_dir / f"{user_id}.json"
        
        if not user_file.exists():
            return

        with open(user_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Carica feedback pasti
        self._meal_feedback[user_id] = {
            meal_id: MealFeedback(**feedback_data)
            for meal_id, feedback_data in data.get("meal_feedback", {}).items()
        }

        # Carica dati progresso
        self._progress_data[user_id] = [
            ProgressEntry(**entry_data)
            for entry_data in data.get("progress_data", [])
        ]

        # Carica preferenze
        if data.get("user_preferences"):
            prefs_data = data["user_preferences"]
            # Converti le liste in set dove necessario
            prefs_data["excluded_foods"] = set(prefs_data["excluded_foods"])
            prefs_data["preferred_foods"] = set(prefs_data["preferred_foods"])
            prefs_data["cooking_methods"] = set(prefs_data["cooking_methods"])
            self._user_preferences[user_id] = UserPreferences(**prefs_data)

        # Carica history chat
        self._chat_history[user_id] = [
            ChatMessage(**message_data)
            for message_data in data.get("chat_history", [])
        ]

        # Carica informazioni nutrizionali
        if data.get("nutritional_info"):
            nutritional_data = data["nutritional_info"]
            # Converti le domande e risposte dell'agente
            if "agent_qa" in nutritional_data:
                nutritional_data["agent_qa"] = [
                    AgentQA(**qa_data)
                    for qa_data in nutritional_data["agent_qa"]
                ]
            self._nutritional_info[user_id] = UserNutritionalInfo(**nutritional_data) 