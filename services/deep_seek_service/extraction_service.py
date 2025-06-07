import json
import os
import threading
import time
from typing import Dict, Any, List, Optional
from .deepseek_client import DeepSeekClient
from .caloric_data_completer import CaloricDataCompleter



class NutritionalDataExtractor:
    """
    Servizio per l'estrazione di dati nutrizionali dalle conversazioni usando DeepSeek.
    """
    
    def __init__(self):
        self.deepseek_client = DeepSeekClient()
        self.caloric_data_completer = CaloricDataCompleter()
        self.pending_requests = []
        self.file_access_lock = threading.Lock()
        
    def is_available(self) -> bool:
        """Verifica se il servizio di estrazione è disponibile."""
        return self.deepseek_client.is_available()
        
    def extract_data_async(
        self, 
        user_id: str, 
        conversation_history: List[Any], 
        user_info: Dict[str, Any],
        interaction_count: int
    ) -> None:
        """
        Avvia l'estrazione asincrona dei dati nutrizionali.
        
        Args:
            user_id: ID dell'utente
            conversation_history: Storia delle conversazioni
            user_info: Informazioni dell'utente
            interaction_count: Numero di interazioni
        """
        if not self.is_available():
            print("[EXTRACTION_SERVICE] DeepSeek non disponibile, estrazione saltata")
            return
            
        # Il controllo della frequenza è gestito dal DeepSeek Manager
        # Quando arriviamo qui, l'estrazione è già stata approvata
        print(f"[EXTRACTION_SERVICE] Avviando estrazione per utente {user_id} (interazione {interaction_count})")
        
        def extract_in_background():
            try:
                # Chiama DeepSeek per l'estrazione
                extracted_data = self.deepseek_client.extract_nutritional_data(
                    conversation_history, 
                    user_info
                )
                
                if extracted_data:
                    # Carica i dati completi dell'utente dal file per il completer
                    complete_user_data = self._load_complete_user_data(user_id)
                    if complete_user_data:
                        # Completa i dati calorici mancanti usando i dati completi
                        completed_data = self.caloric_data_completer.complete_caloric_data(
                            user_id, complete_user_data, extracted_data
                        )
                    else:
                        # Se non ci sono dati completi, usa quelli passati (fallback)
                        completed_data = self.caloric_data_completer.complete_caloric_data(
                            user_id, user_info, extracted_data
                        )
                    
                    success = self._save_extracted_data(user_id, completed_data)
                    if success:
                        print(f"[EXTRACTION_SERVICE] Dati estratti e salvati per utente {user_id}")
                    else:
                        print(f"[EXTRACTION_SERVICE] Errore nel salvataggio dati per utente {user_id}")
                else:
                    print(f"[EXTRACTION_SERVICE] Nessun dato estratto per utente {user_id}")
                    
            except Exception as e:
                print(f"[EXTRACTION_SERVICE] Errore nell'estrazione per utente {user_id}: {str(e)}")
        
        # Avvia in background thread
        extraction_thread = threading.Thread(
            target=extract_in_background,
            daemon=True,
            name=f"DeepSeekExtraction-{user_id}"
        )
        extraction_thread.start()
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Recupera i risultati delle estrazioni completate.
        
        Returns:
            Lista dei risultati disponibili
        """
        results = []
        
        try:
            # Controlla la cartella user_data per i file con nutritional_info_extracted
            user_data_dir = "user_data"
            if os.path.exists(user_data_dir):
                for filename in os.listdir(user_data_dir):
                    if filename.endswith('.json'):
                        user_id = filename[:-5]  # Rimuovi .json
                        
                        with open(f"{user_data_dir}/{filename}", 'r', encoding='utf-8') as f:
                            user_data = json.load(f)
                            
                        if "nutritional_info_extracted" in user_data:
                            results.append({
                                "user_id": user_id,
                                "data": user_data["nutritional_info_extracted"]
                            })
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel recupero risultati: {str(e)}")
            
        return results
    
    def _load_complete_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carica i dati completi dell'utente dal file per il CaloricDataCompleter.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dati completi dell'utente o None se non trovati
        """
        try:
            user_file_path = f"user_data/{user_id}.json"
            
            if os.path.exists(user_file_path):
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    print(f"[EXTRACTION_SERVICE] Dati completi caricati per utente {user_id}")
                    return user_data
            else:
                print(f"[EXTRACTION_SERVICE] File utente non trovato per {user_id}")
                return None
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel caricamento dati utente {user_id}: {str(e)}")
            return None
    
    def _save_extracted_data(self, user_id: str, extracted_data: Dict[str, Any]) -> bool:
        """
        Salva i dati estratti nel file dell'utente.
        
        Args:
            user_id: ID dell'utente
            extracted_data: Dati estratti da DeepSeek
            
        Returns:
            True se il salvataggio è riuscito
        """
        try:
            user_file_path = f"user_data/{user_id}.json"
            
            # Crea la cartella se non esiste
            os.makedirs("user_data", exist_ok=True)
            
            with self.file_access_lock:
                # Carica dati esistenti o crea nuovo file
                if os.path.exists(user_file_path):
                    with open(user_file_path, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                else:
                    user_data = {}
                
                # Merge intelligente dei dati
                if "nutritional_info_extracted" in user_data:
                    existing_data = user_data["nutritional_info_extracted"]
                    merged = self._merge_extracted_data(existing_data, extracted_data, user_id)
                    if merged:
                        user_data["nutritional_info_extracted"] = existing_data
                        print(f"[EXTRACTION_SERVICE] Dati merged per utente {user_id}")
                    else:
                        print(f"[EXTRACTION_SERVICE] Nessun merge necessario per utente {user_id}")
                else:
                    user_data["nutritional_info_extracted"] = extracted_data
                    print(f"[EXTRACTION_SERVICE] Primi dati estratti per utente {user_id}")
                
                # Salva il file aggiornato
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, indent=2, ensure_ascii=False)
                    
                return True
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel salvataggio per utente {user_id}: {str(e)}")
            return False
    
    def _merge_extracted_data(
        self, 
        existing_data: Dict[str, Any], 
        new_data: Dict[str, Any], 
        user_id: str
    ) -> bool:
        """
        Merge intelligente dei dati estratti.
        
        Args:
            existing_data: Dati esistenti (modificati in place)
            new_data: Nuovi dati da DeepSeek
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        changes_made = False
        
        # Merge intelligente per sezioni strutturate (preserva i campi esistenti)
        for key in ["caloric_needs", "macros_total", "daily_macros"]:
            if key in new_data and new_data[key]:
                if key not in existing_data:
                    existing_data[key] = {}
                
                # Merge a livello di campo, non di sezione intera
                section_changes = self._merge_section_fields(
                    existing_data[key], 
                    new_data[key], 
                    f"{key} per utente {user_id}"
                )
                
                if section_changes:
                    changes_made = True
        
        # Merge specializzato per registered_meals
        if "registered_meals" in new_data and new_data["registered_meals"]:
            if "registered_meals" not in existing_data:
                existing_data["registered_meals"] = []
            
            meal_changes = self._merge_registered_meals(
                existing_data["registered_meals"], 
                new_data["registered_meals"], 
                user_id
            )
            
            if meal_changes:
                changes_made = True
        
        return changes_made
    
    def _merge_section_fields(
        self, 
        existing_section: Dict[str, Any], 
        new_section: Dict[str, Any], 
        section_name: str
    ) -> bool:
        """
        Merge intelligente a livello di campo preservando i valori esistenti.
        
        Args:
            existing_section: Sezione esistente (modificata in place)
            new_section: Nuova sezione da DeepSeek
            section_name: Nome della sezione per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        changes_made = False
        
        for field_name, field_value in new_section.items():
            if field_name not in existing_section and field_value is not None:
                # Aggiungi solo campi nuovi con valore non nullo
                existing_section[field_name] = field_value
                changes_made = True
                print(f"[EXTRACTION_SERVICE] Aggiunto nuovo campo {field_name} in {section_name}")
            elif field_name in existing_section:
                # Campo già presente - mantieni il valore esistente
                print(f"[EXTRACTION_SERVICE] Campo {field_name} già presente in {section_name}, mantenuto valore esistente")
        
        return changes_made
    
    def _merge_registered_meals(
        self, 
        existing_meals: List[Dict[str, Any]], 
        new_meals: List[Dict[str, Any]], 
        user_id: str
    ) -> bool:
        """
        Merge intelligente dei pasti registrati.
        Sostituisce i pasti esistenti dello stesso tipo invece di duplicarli.
        
        Args:
            existing_meals: Lista pasti esistenti (modificata in place)
            new_meals: Nuovi pasti da DeepSeek
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        if not new_meals:
            return False
            
        changes_made = False
        
        for new_meal in new_meals:
            meal_type = new_meal.get("nome_pasto", "").lower()
            if not meal_type:
                continue
                
            print(f"[EXTRACTION_SERVICE] Processando nuovo pasto: {meal_type}")
            
            # Trova tutti i pasti esistenti dello stesso tipo
            meals_to_remove = []
            for i, existing_meal in enumerate(existing_meals):
                existing_type = existing_meal.get("nome_pasto", "").lower()
                
                # Normalizza i nomi dei pasti per il confronto
                normalized_existing = self._normalize_meal_name(existing_type)
                normalized_new = self._normalize_meal_name(meal_type)
                
                if normalized_existing == normalized_new:
                    meals_to_remove.append(i)
                    print(f"[EXTRACTION_SERVICE] Trovato pasto esistente da sostituire: {existing_type}")
            
            # Rimuovi i pasti dello stesso tipo (in ordine inverso per non alterare gli indici)
            for i in reversed(meals_to_remove):
                del existing_meals[i]
                changes_made = True
                print(f"[EXTRACTION_SERVICE] Rimosso pasto duplicato per utente {user_id}")
            
            # Aggiungi il nuovo pasto
            existing_meals.append(new_meal)
            changes_made = True
            print(f"[EXTRACTION_SERVICE] Aggiunto nuovo pasto {meal_type} per utente {user_id}")
        
        return changes_made
    
    def _normalize_meal_name(self, meal_name: str) -> str:
        """
        Normalizza il nome di un pasto per il confronto.
        Mantiene la distinzione tra spuntino mattutino e pomeridiano.
        
        Args:
            meal_name: Nome del pasto
            
        Returns:
            Nome normalizzato
        """
        if not meal_name:
            return ""
            
        name = meal_name.lower().strip().replace("_", " ")
        
        # Mapping per normalizzare i nomi dei pasti MANTENENDO la distinzione mattutino/pomeridiano
        meal_mappings = {
            # Colazione
            "colazione": "colazione",
            "breakfast": "colazione",
            "prima colazione": "colazione",
            "prima_colazione": "colazione",
            
            # Spuntino Mattutino
            "spuntino mattutino": "spuntino_mattutino",
            "spuntino_mattutino": "spuntino_mattutino",
            "spuntino del mattino": "spuntino_mattutino",
            "spuntino di mattina": "spuntino_mattutino",
            "merenda mattutina": "spuntino_mattutino",
            "merenda del mattino": "spuntino_mattutino",
            "snack mattutino": "spuntino_mattutino",
            "snack del mattino": "spuntino_mattutino",
            "break mattutino": "spuntino_mattutino",
            
            # Spuntino Pomeridiano  
            "spuntino pomeridiano": "spuntino_pomeridiano",
            "spuntino_pomeridiano": "spuntino_pomeridiano",
            "spuntino del pomeriggio": "spuntino_pomeridiano",
            "spuntino di pomeriggio": "spuntino_pomeridiano",
            "merenda": "spuntino_pomeridiano",  # "merenda" generica = pomeridiana
            "merenda pomeridiana": "spuntino_pomeridiano",
            "merenda del pomeriggio": "spuntino_pomeridiano",
            "snack pomeridiano": "spuntino_pomeridiano",
            "snack del pomeriggio": "spuntino_pomeridiano",
            
            # Spuntino generico - mantieni per ora, ma DeepSeek dovrebbe essere più specifico
            "spuntino": "spuntino",
            "snack": "spuntino",
            
            # Pranzo
            "pranzo": "pranzo",
            "lunch": "pranzo",
            "pasto principale": "pranzo",
            
            # Cena
            "cena": "cena",
            "dinner": "cena",
            "secondo pasto": "cena",
        }
        
        # Restituisci il mapping o il nome normalizzato se non trovato
        normalized = meal_mappings.get(name, name.replace(" ", "_"))
        
        print(f"[EXTRACTION_SERVICE] Normalized '{meal_name}' → '{normalized}'")
        return normalized
    
    def clear_user_extracted_data(self, user_id: str) -> bool:
        """
        Cancella i dati estratti per un utente specifico.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            True se la cancellazione è riuscita
        """
        try:
            user_file_path = f"user_data/{user_id}.json"
            if os.path.exists(user_file_path):
                with self.file_access_lock:
                    with open(user_file_path, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    # Rimuovi completamente la sezione nutritional_info_extracted
                    if "nutritional_info_extracted" in user_data:
                        del user_data["nutritional_info_extracted"]
                        
                    with open(user_file_path, 'w', encoding='utf-8') as f:
                        json.dump(user_data, f, indent=2, ensure_ascii=False)
                        
                    print(f"[EXTRACTION_SERVICE] Dati DeepSeek cancellati per utente {user_id}")
                    return True
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nella cancellazione dati per utente {user_id}: {str(e)}")
            return False 