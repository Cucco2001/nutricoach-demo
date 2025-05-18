import json
import time
from pathlib import Path
from typing import Dict, List, Set, Union, Optional
from dataclasses import dataclass, asdict

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

class UserDataManager:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._meal_feedback: Dict[str, Dict[str, MealFeedback]] = {}
        self._progress_data: Dict[str, List[ProgressEntry]] = {}
        self._user_preferences: Dict[str, UserPreferences] = {}

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

    def get_meal_feedback(self, user_id: str, meal_id: str) -> Optional[MealFeedback]:
        """Recupera il feedback per un pasto specifico"""
        return self._meal_feedback.get(user_id, {}).get(meal_id)

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
            "user_preferences": asdict(self._user_preferences.get(user_id)) if user_id in self._user_preferences else None
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