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
        Merge semplice dei dati estratti.
        
        Logica:
        1. Sovrascrive i campi DeepSeek su quelli esistenti
        2. Controlla campi mancanti e usa completer per riempirli
        
        Args:
            existing_data: Dati esistenti (modificati in place)
            new_data: Nuovi dati da DeepSeek
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        changes_made = False
        
        # Gestione semplificata per sezioni strutturate
        for key in ["caloric_needs", "macros_total", "daily_macros"]:
            if key in new_data and new_data[key]:
                if key not in existing_data:
                    existing_data[key] = {}
                
                # 1. Sovrascrive campi DeepSeek (con merge speciale per daily_macros)
                if key == "daily_macros":
                    # Merge speciale per daily_macros per preservare dati esistenti nei pasti
                    self._merge_daily_macros_special(existing_data[key], new_data[key], user_id)
                    changes_made = True
                else:
                    # Merge normale per caloric_needs e macros_total
                    for field_name, field_value in new_data[key].items():
                        if field_value is not None:
                            existing_data[key][field_name] = field_value
                            changes_made = True
                            print(f"[EXTRACTION_SERVICE] Sovrascritto {field_name} in {key} per utente {user_id}")
                
                # 2. Completa campi mancanti per caloric_needs e daily_macros
                if key == "caloric_needs":
                    missing_fields = self._get_missing_fields(key, existing_data[key])
                    if missing_fields:
                        print(f"[EXTRACTION_SERVICE] Campi mancanti in caloric_needs: {missing_fields}")
                        completed_section = self._complete_missing_caloric_fields(user_id, existing_data[key])
                        if completed_section:
                            # Sostituisce i missing fields con quelli del completer
                            for field_name in missing_fields:
                                if field_name in completed_section and completed_section[field_name] is not None:
                                    existing_data[key][field_name] = completed_section[field_name]
                                    print(f"[EXTRACTION_SERVICE] Sostituito campo mancante {field_name} = {completed_section[field_name]}")
                            changes_made = True
                elif key == "daily_macros":
                    missing_fields = self._get_missing_fields(key, existing_data[key])
                    if missing_fields:
                        print(f"[EXTRACTION_SERVICE] Campi mancanti in daily_macros: {missing_fields}")
                        completed_section = self._complete_missing_daily_macros_fields(user_id, existing_data[key], existing_data)
                        if completed_section:
                            # Sostituisce i missing fields con quelli del completer
                            self._apply_daily_macros_completion(existing_data[key], completed_section, missing_fields)
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
        
        # Merge specializzato per weekly_diet (dieta settimanale completa)
        if "weekly_diet" in new_data and new_data["weekly_diet"]:
            # Sostituisce completamente la dieta settimanale se presente nei nuovi dati
            existing_data["weekly_diet"] = new_data["weekly_diet"]
            changes_made = True
            print(f"[EXTRACTION_SERVICE] Dieta settimanale aggiornata per utente {user_id} con {len(new_data['weekly_diet'])} giorni")
        
        return changes_made
    
    def _get_missing_fields(self, section_name: str, section_data: Dict[str, Any]) -> List[str]:
        """
        Restituisce la lista dei campi mancanti per una sezione specifica.
        
        Args:
            section_name: Nome della sezione ("caloric_needs", "macros_total", "daily_macros")
            section_data: Dati della sezione da controllare
            
        Returns:
            Lista dei campi mancanti
        """
        missing_fields = []
        
        if section_name == "caloric_needs":
            required_fields = ["bmr", "fabbisogno_base", "fabbisogno_totale", "dispendio_sportivo", "aggiustamento_obiettivo"]
            for field in required_fields:
                if field not in section_data or section_data[field] is None:
                    missing_fields.append(field)

        elif section_name == "macros_total":
            required_fields = ["proteine_g", "carboidrati_g", "grassi_g", "kcal_totali", "proteine_kcal", "grassi_kcal", "carboidrati_kcal", "proteine_percentuale", "grassi_percentuale", "carboidrati_percentuale"]
            for field in required_fields:
                if field not in section_data or section_data[field] is None:
                    missing_fields.append(field)
                    
        elif section_name == "daily_macros":
            # Controlla campo numero_pasti
            if "numero_pasti" not in section_data or section_data["numero_pasti"] is None:
                missing_fields.append("numero_pasti")
            
            # Controlla distribuzione_pasti
            if "distribuzione_pasti" not in section_data or not isinstance(section_data["distribuzione_pasti"], dict):
                missing_fields.append("distribuzione_pasti")
            else:
                # Controlla se i pasti nella distribuzione sono completi
                distribuzione = section_data["distribuzione_pasti"]
                incomplete_meals = []
                for meal_name, meal_data in distribuzione.items():
                    if isinstance(meal_data, dict):
                        # Campi richiesti per ogni pasto secondo la struttura corretta
                        required_meal_fields = ["kcal", "percentuale_kcal", "proteine_g", "carboidrati_g", "grassi_g"]
                        for meal_field in required_meal_fields:
                            if meal_field not in meal_data or meal_data[meal_field] is None:
                                incomplete_meals.append(f"{meal_name}.{meal_field}")
                    else:
                        # Se il pasto non è un dict, è completamente mancante
                        incomplete_meals.append(f"{meal_name}.struttura_completa")
                
                if incomplete_meals:
                    missing_fields.extend(incomplete_meals)
        
        return missing_fields
    
    def _complete_missing_caloric_fields(self, user_id: str, caloric_section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Usa caloric_data_completer per completare solo i campi mancanti in caloric_needs.
        
        Args:
            user_id: ID utente
            caloric_section: Sezione caloric_needs da completare
            
        Returns:
            Sezione caloric_needs completata o None se errore
        """
        try:
            # Carica i dati completi dell'utente
            complete_user_data = self._load_complete_user_data(user_id)
            if not complete_user_data:
                print(f"[EXTRACTION_SERVICE] Impossibile caricare dati utente per completamento caloric_needs")
                return None
                
            # Crea una struttura temporanea per il completer
            temp_extracted_data = {
                "caloric_needs": caloric_section.copy()
            }
            
            # Usa il completer per ottenere dati completi
            completed_data = self.caloric_data_completer.complete_caloric_data(
                user_id, 
                complete_user_data, 
                temp_extracted_data
            )
            
            # Restituisce direttamente la sezione completata
            return completed_data.get("caloric_needs", {})
            
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel completamento campi mancanti caloric_needs: {str(e)}")
            return None
    
    def _complete_missing_daily_macros_fields(
        self, 
        user_id: str, 
        daily_macros_section: Dict[str, Any],
        all_extracted_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Completa i campi mancanti in daily_macros utilizzando le percentuali standard e i totali giornalieri.
        
        Args:
            user_id: ID utente
            daily_macros_section: Sezione daily_macros da completare
            all_extracted_data: Tutti i dati estratti (per accedere a macros_total)
            
        Returns:
            Sezione daily_macros completata o None se errore
        """
        try:
            # Carica i dati completi dell'utente per determinare numero pasti
            complete_user_data = self._load_complete_user_data(user_id)
            if not complete_user_data:
                print(f"[EXTRACTION_SERVICE] Impossibile caricare dati utente per completamento daily_macros")
                return None
            
            completed_daily_macros = daily_macros_section.copy()
            
            # 1. Determina numero pasti se mancante
            if "numero_pasti" not in completed_daily_macros or completed_daily_macros["numero_pasti"] is None:
                numero_pasti = self._determine_numero_pasti(complete_user_data)
                completed_daily_macros["numero_pasti"] = numero_pasti
                print(f"[EXTRACTION_SERVICE] Numero pasti determinato: {numero_pasti}")
            
            # 2. Ottieni totali giornalieri da macros_total o caloric_needs
            totali_giornalieri = self._get_daily_totals(all_extracted_data)
            if not totali_giornalieri:
                print(f"[EXTRACTION_SERVICE] Impossibile ottenere totali giornalieri per completamento daily_macros")
                return None
            
            # 3. Crea/completa distribuzione pasti
            numero_pasti = completed_daily_macros.get("numero_pasti", 4)
            percentuali = self._get_meal_percentages(numero_pasti)
            
            if "distribuzione_pasti" not in completed_daily_macros:
                completed_daily_macros["distribuzione_pasti"] = {}
            
            distribuzione = completed_daily_macros["distribuzione_pasti"]
            
            # 4. Completa ogni pasto con le sue percentuali
            for meal_name, percentuale in percentuali.items():
                if meal_name not in distribuzione:
                    distribuzione[meal_name] = {}
                
                meal_data = distribuzione[meal_name]
                
                # Calcola e aggiungi campi mancanti per questo pasto
                self._complete_single_meal(meal_data, percentuale, totali_giornalieri)
            
            return completed_daily_macros
            
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel completamento daily_macros: {str(e)}")
            return None
    
    def _determine_numero_pasti(self, user_data: Dict[str, Any]) -> int:
        """Determina il numero di pasti ottimale per l'utente dalle sue preferenze."""
        nutritional_info = user_data.get('nutritional_info', {})
        
        # Prima priorità: preferenze esplicite dell'utente dalle nutrition_answers
        nutrition_answers = nutritional_info.get('nutrition_answers', {})
        meal_preferences = nutrition_answers.get('meal_preferences', {})
        
        if meal_preferences.get('answer') == 'Sì':
            follow_up = meal_preferences.get('follow_up', {})
            num_meals = follow_up.get('num_meals')
            
            if isinstance(num_meals, int) and 1 <= num_meals <= 6:
                print(f"[EXTRACTION_SERVICE] Numero pasti da preferenze utente: {num_meals}")
                return num_meals
        
        # Fallback: 
        return 4
    
    def _get_daily_totals(self, all_extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Ottiene i totali giornalieri da macros_total o caloric_needs."""
        totali = {}
        
        # Prova a prendere da macros_total
        if "macros_total" in all_extracted_data:
            macros_total = all_extracted_data["macros_total"]
            totali.update({
                "kcal_totali": macros_total.get("kcal_totali"),
                "proteine_g": macros_total.get("proteine_g"),
                "carboidrati_g": macros_total.get("carboidrati_g"),
                "grassi_g": macros_total.get("grassi_g")
            })
        
        # Se mancano kcal, prova da caloric_needs
        if not totali.get("kcal_totali") and "caloric_needs" in all_extracted_data:
            caloric_needs = all_extracted_data["caloric_needs"]
            totali["kcal_totali"] = caloric_needs.get("fabbisogno_totale")
        
        # Verifica che abbiamo almeno le kcal totali
        if not totali.get("kcal_totali"):
            return None
            
        return totali
    
    def _get_meal_percentages(self, numero_pasti: int) -> Dict[str, float]:
        """Restituisce le percentuali caloriche per ogni pasto basate sul numero."""
        percentuali_map = {
            1: {"pasto_unico": 100},
            2: {"colazione": 60, "cena": 40},
            3: {"colazione": 30, "pranzo": 35, "cena": 35},
            4: {"colazione": 25, "pranzo": 35, "spuntino_pomeridiano": 10, "cena": 30},
            5: {"colazione": 25, "spuntino_mattutino": 5, "pranzo": 35, "spuntino_pomeridiano": 5, "cena": 30},
            6: {"colazione": 25, "spuntino_mattutino": 5, "pranzo": 30, "spuntino_pomeridiano": 5, "cena": 25, "spuntino_serale": 10}
        }
        
        return percentuali_map.get(numero_pasti, percentuali_map[4])  # Default a 4 pasti
    
    def _complete_single_meal(
        self, 
        meal_data: Dict[str, Any], 
        percentuale: float, 
        totali_giornalieri: Dict[str, Any]
    ):
        """Completa un singolo pasto con i suoi macronutrienti, preservando valori esistenti."""
        percentuale_frazione = percentuale / 100.0
        
        # Kcal del pasto - PRESERVA se già presente
        if "kcal" not in meal_data or meal_data["kcal"] is None:
            kcal_totali = totali_giornalieri.get("kcal_totali", 0)
            meal_data["kcal"] = round(kcal_totali * percentuale_frazione)
        
        # Percentuale kcal - PRESERVA se già presente
        if "percentuale_kcal" not in meal_data or meal_data["percentuale_kcal"] is None:
            meal_data["percentuale_kcal"] = percentuale
        
        # Proteine del pasto - PRESERVA se già presente
        if "proteine_g" not in meal_data or meal_data["proteine_g"] is None:
            proteine_totali = totali_giornalieri.get("proteine_g", 0)
            if proteine_totali:
                meal_data["proteine_g"] = round(proteine_totali * percentuale_frazione)
        
        # Carboidrati del pasto - PRESERVA se già presente
        if "carboidrati_g" not in meal_data or meal_data["carboidrati_g"] is None:
            carboidrati_totali = totali_giornalieri.get("carboidrati_g", 0)
            if carboidrati_totali:
                meal_data["carboidrati_g"] = round(carboidrati_totali * percentuale_frazione)
        
        # Grassi del pasto - PRESERVA se già presente  
        if "grassi_g" not in meal_data or meal_data["grassi_g"] is None:
            grassi_totali = totali_giornalieri.get("grassi_g", 0)
            if grassi_totali:
                meal_data["grassi_g"] = round(grassi_totali * percentuale_frazione)
    
    def _apply_daily_macros_completion(
        self, 
        existing_daily_macros: Dict[str, Any],
        completed_daily_macros: Dict[str, Any],
        missing_fields: List[str]
    ):
        """Applica il completamento solo ai campi che erano effettivamente mancanti."""
        # Numero pasti
        if "numero_pasti" in missing_fields:
            existing_daily_macros["numero_pasti"] = completed_daily_macros["numero_pasti"]
            print(f"[EXTRACTION_SERVICE] Completato numero_pasti = {completed_daily_macros['numero_pasti']}")
        
        # Distribuzione pasti
        if "distribuzione_pasti" in missing_fields:
            existing_daily_macros["distribuzione_pasti"] = completed_daily_macros["distribuzione_pasti"]
            print(f"[EXTRACTION_SERVICE] Completata distribuzione_pasti completa")
        else:
            # Completa solo i campi specifici mancanti nei pasti esistenti
            if "distribuzione_pasti" not in existing_daily_macros:
                existing_daily_macros["distribuzione_pasti"] = {}
            
            completed_distribuzione = completed_daily_macros.get("distribuzione_pasti", {})
            existing_distribuzione = existing_daily_macros["distribuzione_pasti"]
            
            for missing_field in missing_fields:
                if "." in missing_field:
                    # Campo del tipo "colazione.kcal"
                    meal_name, field_name = missing_field.split(".", 1)
                    
                    if meal_name in completed_distribuzione:
                        completed_meal = completed_distribuzione[meal_name]
                        
                        # Gestione dati malformati
                        if meal_name not in existing_distribuzione or not isinstance(existing_distribuzione[meal_name], dict):
                            existing_distribuzione[meal_name] = {}
                        
                        if field_name in completed_meal:
                            existing_distribuzione[meal_name][field_name] = completed_meal[field_name]
                            print(f"[EXTRACTION_SERVICE] Completato {missing_field} = {completed_meal[field_name]}")
    
    def _merge_daily_macros_special(
        self, 
        existing_daily_macros: Dict[str, Any], 
        new_daily_macros: Dict[str, Any], 
        user_id: str
    ):
        """
        Merge speciale per daily_macros che preserva i dati esistenti nei pasti.
        
        Args:
            existing_daily_macros: Dati daily_macros esistenti
            new_daily_macros: Nuovi dati daily_macros da DeepSeek
            user_id: ID utente
        """
        # 1. Merge numero_pasti (sovrascrive se presente)
        if "numero_pasti" in new_daily_macros and new_daily_macros["numero_pasti"] is not None:
            existing_daily_macros["numero_pasti"] = new_daily_macros["numero_pasti"]
            print(f"[EXTRACTION_SERVICE] Sovrascritto numero_pasti in daily_macros per utente {user_id}")
        
        # 2. Merge distribuzione_pasti (preserva dati esistenti)
        if "distribuzione_pasti" in new_daily_macros and isinstance(new_daily_macros["distribuzione_pasti"], dict):
            if "distribuzione_pasti" not in existing_daily_macros:
                existing_daily_macros["distribuzione_pasti"] = {}
            
            existing_distribuzione = existing_daily_macros["distribuzione_pasti"]
            new_distribuzione = new_daily_macros["distribuzione_pasti"]
            
            # Per ogni pasto in DeepSeek
            for meal_name, new_meal_data in new_distribuzione.items():
                if isinstance(new_meal_data, dict):
                    # Se il pasto non esiste o è malformato, crealo/ricrealo
                    if meal_name not in existing_distribuzione or not isinstance(existing_distribuzione[meal_name], dict):
                        existing_distribuzione[meal_name] = {}
                        if meal_name in existing_distribuzione and not isinstance(existing_distribuzione[meal_name], dict):
                            print(f"[EXTRACTION_SERVICE] ATTENZIONE: Pasto malformato {meal_name} sostituito con dict valido")
                    
                    existing_meal = existing_distribuzione[meal_name]
                    
                    # Merge campi del pasto (sovrascrive sempre i campi DeepSeek)
                    for field_name, field_value in new_meal_data.items():
                        if field_value is not None:
                            existing_meal[field_name] = field_value
                            print(f"[EXTRACTION_SERVICE] Sovrascritto {meal_name}.{field_name} = {field_value} per utente {user_id}")
                else:
                    print(f"[EXTRACTION_SERVICE] ATTENZIONE: Pasto malformato in DeepSeek per {meal_name}, ignorato")
    
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
        Cancella tutti i dati estratti per un utente specifico.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            True se la cancellazione è riuscita, False altrimenti
        """
        try:
            user_file_path = f"user_data/{user_id}.json"
            
            # Se il file non esiste, considera l'operazione riuscita
            if not os.path.exists(user_file_path):
                print(f"[EXTRACTION_SERVICE] File utente {user_id} non esistente, cancellazione considerata riuscita")
                return True
            
            # Carica i dati esistenti
            user_data = self._load_complete_user_data(user_id)
            if not user_data:
                print(f"[EXTRACTION_SERVICE] Impossibile caricare dati utente {user_id} per cancellazione")
                return False
            
            # Cancella solo la sezione nutritional_info_extracted se esiste
            if "nutritional_info_extracted" in user_data:
                del user_data["nutritional_info_extracted"]
                print(f"[EXTRACTION_SERVICE] Cancellata sezione nutritional_info_extracted per utente {user_id}")
                
                # Salva i dati aggiornati (senza la sezione estratta)
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(user_data, f, indent=2, ensure_ascii=False)
                
                print(f"[EXTRACTION_SERVICE] Dati utente {user_id} aggiornati senza sezione estratta")
                return True
            else:
                print(f"[EXTRACTION_SERVICE] Nessun dato estratto da cancellare per utente {user_id}")
                return True
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nella cancellazione dati utente {user_id}: {str(e)}")
            return False
    