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
        interaction_count: int,
        deepseek_manager: Any = None
    ) -> None:
        """
        Avvia l'estrazione asincrona dei dati nutrizionali.
        
        Args:
            user_id: ID dell'utente
            conversation_history: Storia delle conversazioni
            user_info: Informazioni dell'utente
            interaction_count: Numero di interazioni
            deepseek_manager: Riferimento al manager per processare la coda
        """
        if not self.is_available():
            return
            
        # Il controllo della frequenza è gestito dal DeepSeek Manager
        # Quando arriviamo qui, l'estrazione è già stata approvata
        def extract_in_background():
            try:
                # Chiama DeepSeek per l'estrazione
                deepseek_result = self.deepseek_client.extract_nutritional_data(
                    conversation_history, 
                    user_info
                )
                
                if deepseek_result and "extracted_data" in deepseek_result:
                    extracted_data = deepseek_result["extracted_data"]
                    
                    # DEBUG: Log che cosa DeepSeek ha estratto
                    print(f"[EXTRACTION_SERVICE] DEBUG per {user_id}:")
                    print(f"[EXTRACTION_SERVICE] DeepSeek extracted_data keys: {list(extracted_data.keys())}")
                    
                    # Carica i dati completi dell'utente dal file per il completer
                    complete_user_data = self._load_complete_user_data(user_id)
                    if complete_user_data:
                        # Completa i dati calorici mancanti usando i dati completi
                        completed_data = self.caloric_data_completer.complete_caloric_data(
                            user_id, complete_user_data, extracted_data
                        )
                        
                        # DEBUG: Log cosa ha restituito il completer
                        print(f"[EXTRACTION_SERVICE] Completer output keys: {list(completed_data.keys())}")
                        if 'caloric_needs' in completed_data:
                            print(f"[EXTRACTION_SERVICE] PROBLEMA: caloric_needs aggiunto dal completer!")
                            print(f"[EXTRACTION_SERVICE] caloric_needs content: {completed_data['caloric_needs']}")
                    else:
                        # Se non ci sono dati completi, usa quelli passati (fallback)
                        completed_data = self.caloric_data_completer.complete_caloric_data(
                            user_id, user_info, extracted_data
                        )
                    
                    success = self._save_extracted_data(user_id, completed_data, deepseek_result)
                    if not success:
                        print(f"[EXTRACTION_SERVICE] Errore nel salvataggio dati per utente {user_id}")
            except Exception as e:
                print(f"[EXTRACTION_SERVICE] Errore nell'estrazione per utente {user_id}: {str(e)}")
            finally:
                # IMPORTANTE: Rinomina il thread per evitare race condition
                # Prima di chiamare process_queue, il thread deve "segnalare" che ha finito
                current_thread = threading.current_thread()
                current_thread.name = f"DeepSeekFinished-{user_id}"
                
                # Processa la coda quando l'estrazione finisce
                print(f"[EXTRACTION_SERVICE] Estrazione finita per {user_id}, chiamando process_queue()")
                if deepseek_manager:
                    deepseek_manager.process_queue()
                else:
                    print(f"[EXTRACTION_SERVICE] ERRORE: deepseek_manager è None per {user_id}")
        
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
                    return user_data
            else:
                return None
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel caricamento dati utente {user_id}: {str(e)}")
            return None
    
    def _save_extracted_data(self, user_id: str, extracted_data: Dict[str, Any], deepseek_result: Dict[str, Any] = None) -> bool:
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
                else:
                    user_data["nutritional_info_extracted"] = extracted_data
                
                # Salva il file aggiornato
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, indent=2, ensure_ascii=False)
                
                # Sincronizzazione automatica con Supabase
                try:
                    from services.supabase_service import auto_sync_user_data
                    auto_sync_user_data(user_id, user_data)
                except Exception as e:
                    print(f"[EXTRACTION_SERVICE] Errore sincronizzazione Supabase per {user_id}: {str(e)}")
                
                # Salva copia locale per debugging
                self._save_debug_output(user_id, extracted_data, user_data, deepseek_result)
                    
                return True
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel salvataggio per utente {user_id}: {str(e)}")
            return False
    
    def _save_debug_output(self, user_id: str, extracted_data: Dict[str, Any], complete_user_data: Dict[str, Any], deepseek_result: Dict[str, Any] = None) -> None:
        """
        Salva un singolo file di debug completo con conversazione ed estrazione.
        
        Args:
            user_id: ID dell'utente
            extracted_data: Dati estratti da DeepSeek (solo ultima estrazione)
            complete_user_data: Dati completi dell'utente (con merge)
        """
        try:
            from datetime import datetime
            
            # Crea la directory di debug se non esiste
            debug_dir = "tests/deep_seek_out"
            os.makedirs(debug_dir, exist_ok=True)
            
         
            
            # Timestamp per il nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Salva un singolo file completo con conversazione + estrazione
            debug_file = os.path.join(debug_dir, f"{user_id}_{timestamp}_debug_completo.json")
            
            # Usa i dati DeepSeek se disponibili, altrimenti fallback
            if deepseek_result:
                conversation_history = deepseek_result.get("conversation_history", [])
                raw_response = deepseek_result.get("raw_response", "")
                extraction_keys = deepseek_result.get("extraction_keys", [])
            else:
                conversation_history = []
                raw_response = ""
                extraction_keys = []
            
            # Formatta le interazioni direttamente dai dati DeepSeek
            interazioni_data = self._format_interactions_from_deepseek(conversation_history, complete_user_data)
            
            debug_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "debug_type": "conversazione_completa_con_estrazione",
                
                # Sezione interazioni strutturate
                "interazioni": interazioni_data,
                
                # Sezione estrazione DeepSeek
                "deepseek_estrazione": {
                    "raw_response_formatted": self._format_raw_response(raw_response),
                    "dati_estratti_parsed": extracted_data,
                    "chiavi_estratte": extraction_keys,
                    "timestamp_estrazione": datetime.now().isoformat()
                },
                
                # Dati finali merged
                "dati_finali_merged": complete_user_data.get("nutritional_info_extracted", {}),
                
                # Metadati
                "metadati": {
                    "versione_debug": "4.0",
                    "descrizione": "File debug con interazioni da DeepSeek + raw response diretta"
                }
            }
            # Mantieni anche una versione "latest" per facilità di accesso
            latest_file = os.path.join(debug_dir, f"{user_id}_latest_debug_completo.json")
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel salvataggio debug per {user_id}: {str(e)}")
    
    def _load_recent_conversation_data(self, user_id: str) -> Dict[str, Any]:
        """
        Carica i dati della conversazione recente per il debug.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dati della conversazione o informazioni di fallback
        """
        try:
            # Cerca file di conversazione esistenti nella cartella debug
            debug_dir = "tests/deep_seek_out"
            conversation_files = []
            
            if os.path.exists(debug_dir):
                for filename in os.listdir(debug_dir):
                    if "conversation" in filename and filename.endswith('.json'):
                        conversation_files.append(os.path.join(debug_dir, filename))
            
            # Usa il file di conversazione più recente se disponibile
            if conversation_files:
                # Ordina per tempo di modifica (più recente primo)
                conversation_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                with open(conversation_files[0], 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                    
                return {
                    "fonte": "file_conversazione_esistente",
                    "file_utilizzato": os.path.basename(conversation_files[0]),
                    "conversazioni": conversation_data.get("conversations", []),
                    "user_info": conversation_data.get("user_info", {}),
                    "raw_deepseek_response": conversation_data.get("raw_deepseek_response", ""),
                    "extracted_keys": conversation_data.get("extracted_keys", [])
                }
            
            # Fallback: carica dati utente dal file principale
            user_data = self._load_complete_user_data(user_id)
            if user_data:
                return {
                    "fonte": "dati_utente_file",
                    "user_info": user_data,
                    "nota": "Conversazione recente non disponibile, usando dati utente salvati"
                }
            
            # Fallback finale
            return {
                "fonte": "fallback",
                "nota": "Nessun dato di conversazione disponibile",
                "user_id": user_id
            }
            
        except Exception as e:
            return {
                "fonte": "errore",
                "errore": str(e),
                "user_id": user_id
            }
    
    def _format_interactions_for_debug(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatta le interazioni in modo leggibile per il debug.
        
        Args:
            conversation_data: Dati della conversazione caricati
            
        Returns:
            Dizionario con interazioni formattate
        """
        try:
            formatted = {
                "fonte_dati": conversation_data.get("fonte", "unknown"),
                "info_utente": conversation_data.get("user_info", {}),
                "lista_interazioni": []
            }
            
            # Ottieni le conversazioni dalla struttura
            conversations = conversation_data.get("conversazioni", [])
            if not conversations:
                conversations = conversation_data.get("conversations", [])
            
            if conversations:
                for i, conv in enumerate(conversations, 1):
                    interaction = {
                        "numero_interazione": i,
                        "domanda_utente": conv.get("question", "N/A"),
                        "risposta_agente": conv.get("answer", "N/A"),
                        "timestamp": conv.get("timestamp", "N/A")
                    }
                    formatted["lista_interazioni"].append(interaction)
            else:
                # Fallback se non ci sono conversazioni strutturate
                formatted["lista_interazioni"] = [{
                    "numero_interazione": 1,
                    "domanda_utente": "Dati non disponibili",
                    "risposta_agente": "Conversazione non trovata",
                    "nota": "Impossibile recuperare la conversazione originale"
                }]
            
            return formatted
            
        except Exception as e:
            return {
                "errore": f"Errore nel formatting interazioni: {str(e)}",
                "dati_originali": conversation_data
            }
    
    def _format_interactions_from_deepseek(self, conversation_history: List[Any], complete_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatta le interazioni direttamente dai dati DeepSeek.
        
        Args:
            conversation_history: Storia conversazioni da DeepSeek
            complete_user_data: Dati completi utente per info aggiuntive
            
        Returns:
            Dizionario con interazioni formattate
        """
        try:
            formatted = {
                "fonte_dati": "deepseek_direct",
                "info_utente": complete_user_data.get("nutritional_info", {}),
                "lista_interazioni": []
            }
            
            if conversation_history:
                for i, conv in enumerate(conversation_history, 1):
                    if isinstance(conv, dict):
                        interaction = {
                            "numero_interazione": i,
                            "domanda_utente": conv.get("question", "N/A"),
                            "risposta_agente": conv.get("answer", "N/A"),
                            "timestamp": conv.get("timestamp", "N/A")
                        }
                    else:
                        # Se conv ha attributi invece di chiavi dict
                        interaction = {
                            "numero_interazione": i,
                            "domanda_utente": getattr(conv, "question", "N/A"),
                            "risposta_agente": getattr(conv, "answer", "N/A"),
                            "timestamp": getattr(conv, "timestamp", "N/A")
                        }
                    formatted["lista_interazioni"].append(interaction)
            else:
                # Fallback: prova a caricare dal file utente se possibile
                user_conversations = complete_user_data.get("nutritional_info", {}).get("agent_qa", [])
                if user_conversations:
                    for i, conv in enumerate(user_conversations, 1):
                        interaction = {
                            "numero_interazione": i,
                            "domanda_utente": conv.get("question", "N/A"),
                            "risposta_agente": conv.get("answer", "N/A"),
                            "timestamp": conv.get("timestamp", "N/A")
                        }
                        formatted["lista_interazioni"].append(interaction)
                else:
                    formatted["lista_interazioni"] = [{
                        "numero_interazione": 1,
                        "domanda_utente": "Nessuna conversazione disponibile",
                        "risposta_agente": "Dati conversazione non trovati",
                        "nota": "Impossibile recuperare conversazioni da DeepSeek o file utente"
                    }]
            
            return formatted
            
        except Exception as e:
            return {
                "errore": f"Errore nel formatting interazioni da DeepSeek: {str(e)}",
                "conversation_history": conversation_history
            }
    
    def _format_raw_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Formatta la raw response di DeepSeek per renderla più leggibile.
        
        Args:
            raw_response: Risposta grezza di DeepSeek
            
        Returns:
            Dizionario con raw response formattata e metadati
        """
        try:
            if not raw_response:
                return {
                    "status": "vuota",
                    "messaggio": "Nessuna raw response disponibile",
                    "contenuto_originale": "",
                    "contenuto_formattato": "",
                    "metadati": {
                        "lunghezza_caratteri": 0,
                        "numero_righe": 0
                    }
                }
            
            # Pulisci la risposta da eventuali markdown
            cleaned_response = raw_response.strip()
            
            # Rimuovi eventuali wrapper di markdown JSON
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Prova a parsare e ri-formattare come JSON
            formatted_json = ""
            json_valido = False
            
            try:
                parsed_json = json.loads(cleaned_response)
                formatted_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                json_valido = True
            except json.JSONDecodeError as e:
                formatted_json = f"ERRORE PARSING JSON: {str(e)}\n\nContenuto pulito:\n{cleaned_response}"
                json_valido = False
            
            # Calcola metadati
            righe_originali = raw_response.count('\n') + 1
            righe_formattate = formatted_json.count('\n') + 1
            
            return {
                "status": "disponibile",
                "json_valido": json_valido,
                "contenuto_originale": raw_response,
                "contenuto_pulito": cleaned_response,
                "contenuto_formattato": formatted_json,
                "metadati": {
                    "lunghezza_originale": len(raw_response),
                    "lunghezza_pulita": len(cleaned_response),
                    "lunghezza_formattata": len(formatted_json),
                    "righe_originali": righe_originali,
                    "righe_formattate": righe_formattate,
                    "aveva_markdown_wrapper": raw_response.strip().startswith("```"),
                    "tipo_contenuto": "JSON valido" if json_valido else "Testo/JSON malformato"
                }
            }
            
        except Exception as e:
            return {
                "status": "errore",
                "errore": f"Errore nel formatting raw response: {str(e)}",
                "contenuto_originale": raw_response if raw_response else "",
                "contenuto_formattato": "Impossibile formattare"
            }
    
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
                        if field_value is not None and not self._is_invalid_zero(field_name, field_value, key):
                            existing_data[key][field_name] = field_value
                            changes_made = True
                
                # 2. Completa campi mancanti SOLO se DeepSeek aveva intenzione di aggiornare questa sezione
                if key == "caloric_needs":
                    # CONTROLLO IMPORTANTE: Solo se DeepSeek ha estratto caloric_needs in questa interazione
                    if key in new_data and new_data[key]:
                        missing_fields = self._get_missing_fields(key, existing_data[key])
                        if missing_fields:
                            print(f"[EXTRACTION_SERVICE] Campi mancanti rilevati per {user_id}: {missing_fields}")
                            completed_section = self._complete_missing_caloric_fields(user_id, existing_data[key])
                            if completed_section:
                                # Sostituisce SOLO i missing fields con quelli del completer
                                # NON sovrascrive mai i campi già estratti correttamente da DeepSeek
                                for field_name in missing_fields:
                                    if field_name in completed_section and completed_section[field_name] is not None:
                                        # Doppio controllo: sostituisce solo se il campo è davvero mancante
                                        if field_name not in existing_data[key] or existing_data[key][field_name] is None:
                                            existing_data[key][field_name] = completed_section[field_name]
                                            print(f"[EXTRACTION_SERVICE] Completato campo mancante {field_name} = {completed_section[field_name]}")
                                        else:
                                            print(f"[EXTRACTION_SERVICE] Campo {field_name} già presente, non sovrascritto (valore: {existing_data[key][field_name]})")
                                changes_made = True
                    else:
                        print(f"[EXTRACTION_SERVICE] Saltato completamento caloric_needs: DeepSeek non ha estratto questa sezione nell'interazione corrente")
                elif key == "macros_total":
                    # CONTROLLO: Solo se DeepSeek ha estratto macros_total in questa interazione
                    if key in new_data and new_data[key]:
                        missing_fields = self._get_missing_fields(key, existing_data[key])
                        if missing_fields:
                            completed_section = self._complete_missing_macros_fields(user_id, existing_data[key])
                            if completed_section:
                                # Sostituisce i missing fields con quelli del completer
                                for field_name in missing_fields:
                                    if field_name in completed_section and completed_section[field_name] is not None:
                                        # Doppio controllo: sostituisce solo se il campo è davvero mancante
                                        if field_name not in existing_data[key] or existing_data[key][field_name] is None:
                                            existing_data[key][field_name] = completed_section[field_name]
                                            print(f"[EXTRACTION_SERVICE] Completato campo mancante macros_total.{field_name} = {completed_section[field_name]}")
                                        else:
                                            print(f"[EXTRACTION_SERVICE] Campo macros_total.{field_name} già presente, non sovrascritto")
                                changes_made = True
                    else:
                        print(f"[EXTRACTION_SERVICE] Saltato completamento macros_total: DeepSeek non ha estratto questa sezione nell'interazione corrente")
                elif key == "daily_macros":
                    # CONTROLLO: Solo se DeepSeek ha estratto daily_macros in questa interazione
                    if key in new_data and new_data[key]:
                        missing_fields = self._get_missing_fields(key, existing_data[key])
                        if missing_fields:
                            completed_section = self._complete_missing_daily_macros_fields(user_id, existing_data[key], existing_data)
                            if completed_section:
                                # Sostituisce i missing fields con quelli del completer
                                self._apply_daily_macros_completion(existing_data[key], completed_section, missing_fields)
                                changes_made = True
                    else:
                        print(f"[EXTRACTION_SERVICE] Saltato completamento daily_macros: DeepSeek non ha estratto questa sezione nell'interazione corrente")
        
        # Merge specializzato per weekly_diet_day_1
        if "weekly_diet_day_1" in new_data and new_data["weekly_diet_day_1"]:
            if "weekly_diet_day_1" not in existing_data:
                existing_data["weekly_diet_day_1"] = []
            
            meal_changes = self._merge_weekly_diet_day_1(
                existing_data["weekly_diet_day_1"], 
                new_data["weekly_diet_day_1"], 
                user_id
            )
            
            if meal_changes:
                changes_made = True
        
        # Merge specializzato per weekly_diet_days_2_7 (supporta modifiche parziali e complete)
        if "weekly_diet_days_2_7" in new_data and new_data["weekly_diet_days_2_7"]:
            if "weekly_diet_days_2_7" not in existing_data:
                existing_data["weekly_diet_days_2_7"] = {}
            
            weekly_changes = self._merge_weekly_diet_smart(
                existing_data["weekly_diet_days_2_7"], 
                new_data["weekly_diet_days_2_7"], 
                user_id
            )
            
            if weekly_changes:
                changes_made = True
                
        # Merge specializzato per weekly_diet_partial_days_2_7 (modifiche specifiche di sottocampi)
        if "weekly_diet_partial_days_2_7" in new_data and new_data["weekly_diet_partial_days_2_7"]:
            if "weekly_diet_days_2_7" not in existing_data:
                existing_data["weekly_diet_days_2_7"] = {}
                
            partial_changes = self._merge_weekly_diet_partial(
                existing_data["weekly_diet_days_2_7"],
                new_data["weekly_diet_partial_days_2_7"],
                user_id
            )
            
            if partial_changes:
                changes_made = True
        
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
            required_fields = ["bmr", "fabbisogno_base", "fabbisogno_finale", "dispendio_sportivo", "aggiustamento_obiettivo"]
            for field in required_fields:
                if field not in section_data or section_data[field] is None or self._is_invalid_zero(field, section_data.get(field, 0), section_name):
                    missing_fields.append(field)

        elif section_name == "macros_total":
            required_fields = ["proteine_g", "carboidrati_g", "grassi_g", "kcal_totali", "proteine_kcal", "grassi_kcal", "carboidrati_kcal", "proteine_percentuale", "grassi_percentuale", "carboidrati_percentuale"]
            for field in required_fields:
                if field not in section_data or section_data[field] is None or self._is_invalid_zero(field, section_data.get(field, 0), section_name):
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
            
            if isinstance(num_meals, int) and 1 <= num_meals <= 5:
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
                "kcal_finali": macros_total.get("kcal_finali"),
                "proteine_g": macros_total.get("proteine_g"),
                "carboidrati_g": macros_total.get("carboidrati_g"),
                "grassi_g": macros_total.get("grassi_g")
            })
        
        # Se mancano kcal, prova da caloric_needs
        if not totali.get("kcal_finali") and "caloric_needs" in all_extracted_data:
            caloric_needs = all_extracted_data["caloric_needs"]
            totali["kcal_finali"] = caloric_needs.get("fabbisogno_finale")
        
        # Verifica che abbiamo almeno le kcal totali
        if not totali.get("kcal_finali"):
            return None
            
        return totali
    
    def _get_meal_percentages(self, numero_pasti: int) -> Dict[str, float]:
        """Restituisce le percentuali caloriche per ogni pasto basate sul numero."""
        percentuali_map = {
            1: {"pasto_unico": 100},
            2: {"colazione": 60, "cena": 40},
            3: {"colazione": 30, "pranzo": 35, "cena": 35},
            4: {"colazione": 25, "pranzo": 35, "spuntino_pomeridiano": 10, "cena": 30},
            5: {"colazione": 25, "spuntino_mattutino": 5, "pranzo": 35, "spuntino_pomeridiano": 5, "cena": 30}
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
            kcal_finali = totali_giornalieri.get("kcal_finali", 0)
            meal_data["kcal"] = round(kcal_finali * percentuale_frazione)
        
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
        
        # Distribuzione pasti
        if "distribuzione_pasti" in missing_fields:
            existing_daily_macros["distribuzione_pasti"] = completed_daily_macros["distribuzione_pasti"]
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
        # 1. Merge numero_pasti (sovrascrive se presente e diverso da 0)
        if "numero_pasti" in new_daily_macros and new_daily_macros["numero_pasti"] is not None and new_daily_macros["numero_pasti"] != 0:
            existing_daily_macros["numero_pasti"] = new_daily_macros["numero_pasti"]
        
        # 2. Merge distribuzione_pasti (preserva dati esistenti)
        if "distribuzione_pasti" in new_daily_macros and isinstance(new_daily_macros["distribuzione_pasti"], dict):
            if "distribuzione_pasti" not in existing_daily_macros:
                existing_daily_macros["distribuzione_pasti"] = {}
            
            existing_distribuzione = existing_daily_macros["distribuzione_pasti"]
            new_distribuzione = new_daily_macros["distribuzione_pasti"]
            
            # Normalizza eventuali "spuntino" generici nei dati esistenti
            if "spuntino" in existing_distribuzione:
                spuntino_data = existing_distribuzione.pop("spuntino")
                existing_distribuzione["spuntino_pomeridiano"] = spuntino_data
            
            # Per ogni pasto in DeepSeek
            for meal_name, new_meal_data in new_distribuzione.items():
                if isinstance(new_meal_data, dict):
                    # Se il pasto non esiste o è malformato, crealo/ricrealo
                    if meal_name not in existing_distribuzione or not isinstance(existing_distribuzione[meal_name], dict):
                        existing_distribuzione[meal_name] = {}
                    
                    existing_meal = existing_distribuzione[meal_name]
                    
                    # Merge campi del pasto (sovrascrive sempre i campi DeepSeek, esclusi gli zeri)
                    for field_name, field_value in new_meal_data.items():
                        if field_value is not None and not self._is_invalid_zero(field_name, field_value, 'daily_macros'):
                            existing_meal[field_name] = field_value
            
            # Normalizza eventuali "spuntino" generici
            if "spuntino" in new_distribuzione:
                # Se c'è uno spuntino generico, assumiamo sia pomeridiano
                spuntino_data = new_distribuzione.pop("spuntino")
                new_distribuzione["spuntino_pomeridiano"] = spuntino_data
    
    def _merge_weekly_diet_day_1(
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
                

            
            # Trova tutti i pasti esistenti dello stesso tipo
            meals_to_remove = []
            for i, existing_meal in enumerate(existing_meals):
                existing_type = existing_meal.get("nome_pasto", "").lower()
                
                # Normalizza i nomi dei pasti per il confronto
                normalized_existing = self._normalize_meal_name(existing_type)
                normalized_new = self._normalize_meal_name(meal_type)
                
                if normalized_existing == normalized_new:
                    meals_to_remove.append(i)

            
            # Rimuovi i pasti dello stesso tipo (in ordine inverso per non alterare gli indici)
            for i in reversed(meals_to_remove):
                del existing_meals[i]
                changes_made = True

            
            # Aggiungi il nuovo pasto
            existing_meals.append(new_meal)
            changes_made = True

        
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
                return True
            
            # Carica i dati esistenti
            user_data = self._load_complete_user_data(user_id)
            if not user_data:
                print(f"[EXTRACTION_SERVICE] Impossibile caricare dati utente {user_id} per cancellazione")
                return False
            
            # Cancella solo la sezione nutritional_info_extracted se esiste
            if "nutritional_info_extracted" in user_data:
                del user_data["nutritional_info_extracted"]
                
                # Salva i dati aggiornati (senza la sezione estratta)
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(user_data, f, indent=2, ensure_ascii=False)
            
                return True
            else:
                return True
                
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nella cancellazione dati utente {user_id}: {str(e)}")
            return False
    
    def _merge_weekly_diet_smart(
        self, 
        existing_weekly_diet: Dict[str, Any], 
        new_weekly_diet: Dict[str, Any], 
        user_id: str
    ) -> bool:
        """
        Merge intelligente per weekly_diet_days_2_7 che preserva dati esistenti quando possibile.
        
        Args:
            existing_weekly_diet: Dati weekly_diet_days_2_7 esistenti
            new_weekly_diet: Nuovi dati weekly_diet_days_2_7 da DeepSeek  
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        if not new_weekly_diet:
            return False
            
        changes_made = False
        
        for day_key, new_day_data in new_weekly_diet.items():
            if not isinstance(new_day_data, dict):
                continue
                
            # Se il giorno non esiste, aggiungilo completamente
            if day_key not in existing_weekly_diet:
                existing_weekly_diet[day_key] = new_day_data.copy()
                changes_made = True

                continue
            
            # Il giorno esiste, merge intelligente dei pasti
            existing_day = existing_weekly_diet[day_key]
            if not isinstance(existing_day, dict):
                existing_day = {}
                existing_weekly_diet[day_key] = existing_day
            
            day_changes = self._merge_day_meals(existing_day, new_day_data, day_key, user_id)
            if day_changes:
                changes_made = True
        
        return changes_made
    
    def _merge_weekly_diet_partial(
        self, 
        existing_weekly_diet: Dict[str, Any], 
        partial_updates: Dict[str, Any], 
        user_id: str
    ) -> bool:
        """
        Merge parziale per aggiornamenti specifici della weekly_diet_days_2_7.
        
        Formato partial_updates atteso:
        {
            "day": "giorno_2",
            "meal": "pranzo", 
            "data": {
                "alimenti": {...},
                "target_nutrients": {...},
                "actual_nutrients": {...}
            }
        }
        
        O formato batch per più modifiche:
        {
            "updates": [
                {"day": "giorno_2", "meal": "pranzo", "data": {...}},
                {"day": "giorno_3", "meal": "cena", "data": {...}}
            ]
        }
        
        Args:
            existing_weekly_diet: Dati weekly_diet_days_2_7 esistenti
            partial_updates: Aggiornamenti parziali specifici
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        if not partial_updates:
            return False
            
        changes_made = False
        
        # Supporta sia formato singolo che batch
        updates_list = []
        
        if "updates" in partial_updates and isinstance(partial_updates["updates"], list):
            # Formato batch
            updates_list = partial_updates["updates"]
        elif "day" in partial_updates and "meal" in partial_updates and "data" in partial_updates:
            # Formato singolo
            updates_list = [partial_updates]
        else:
            return False
        
        for update in updates_list:
            day_key = update.get("day")
            meal_name = update.get("meal") 
            meal_data = update.get("data")
            
            if not all([day_key, meal_name, meal_data]):

                continue
            
            # Assicura che il giorno esista
            if day_key not in existing_weekly_diet:
                existing_weekly_diet[day_key] = {}

            
            # Assicura che sia un dizionario
            if not isinstance(existing_weekly_diet[day_key], dict):
                existing_weekly_diet[day_key] = {}

            
            # Aggiorna il pasto specifico
            existing_weekly_diet[day_key][meal_name] = meal_data.copy()
            changes_made = True
            
 
            # Log dettagliato degli alimenti aggiornati
            if isinstance(meal_data, dict) and "alimenti" in meal_data:
                alimenti = meal_data["alimenti"]
        return changes_made
    
    def _merge_day_meals(
        self, 
        existing_day: Dict[str, Any], 
        new_day: Dict[str, Any], 
        day_key: str, 
        user_id: str
    ) -> bool:
        """
        Merge intelligente dei pasti di un singolo giorno.
        
        Args:
            existing_day: Dati del giorno esistente
            new_day: Nuovi dati del giorno
            day_key: Chiave del giorno (es. "giorno_2")
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        changes_made = False
        
        for meal_name, new_meal_data in new_day.items():
            if not new_meal_data:
                continue
                
            # Controllo se il pasto è sostanzialmente diverso da quello esistente
            if meal_name in existing_day:
                existing_meal = existing_day[meal_name]
                
                # Confronto semplificato: se la struttura alimenti è diversa, sovrascrive
                if self._meals_are_different(existing_meal, new_meal_data):
                    existing_day[meal_name] = new_meal_data.copy()
                    changes_made = True
                    
            else:
                # Nuovo pasto, aggiungilo
                existing_day[meal_name] = new_meal_data.copy()
                changes_made = True

        
        return changes_made
    
    def _meals_are_different(self, meal1: Dict[str, Any], meal2: Dict[str, Any]) -> bool:
        """
        Confronta due pasti per determinare se sono sostanzialmente diversi.
        
        Args:
            meal1: Primo pasto
            meal2: Secondo pasto
            
        Returns:
            True se i pasti sono diversi
        """
        # Confronto basato sugli alimenti
        alimenti1 = meal1.get("alimenti", {}) if isinstance(meal1, dict) else {}
        alimenti2 = meal2.get("alimenti", {}) if isinstance(meal2, dict) else {}
        
        # Se uno dei due è vuoto e l'altro no, sono diversi
        if bool(alimenti1) != bool(alimenti2):
            return True
        
        # Confronto semplificato delle chiavi degli alimenti
        if isinstance(alimenti1, dict) and isinstance(alimenti2, dict):
            keys1 = set(alimenti1.keys())
            keys2 = set(alimenti2.keys())
            
            # Se hanno alimenti diversi, sono diversi
            if keys1 != keys2:
                return True
                
        # Se sono arrivato qui, considera simili (stesso tipo di alimenti)
        return False
    
    def _is_invalid_zero(self, field_name: str, field_value: Any, section_name: str) -> bool:
        """
        Determina se un valore 0 è invalido (errore) o legittimo.
        
        Args:
            field_name: Nome del campo
            field_value: Valore del campo
            section_name: Nome della sezione (caloric_needs, macros_total, etc.)
            
        Returns:
            True se il valore 0 è considerato invalido/errore
        """
        if field_value != 0:
            return False
            
        # Campi che NON dovrebbero mai essere 0
        never_zero_fields = {
            # caloric_needs
            'bmr', 'fabbisogno_base', 'fabbisogno_finale', 'fabbisogno_totale',
            'laf_utilizzato',
            # macros_total
            'kcal_finali', 'kcal_totali', 'proteine_g', 'carboidrati_g', 'grassi_g',
            'proteine_kcal', 'carboidrati_kcal', 'grassi_kcal',
            'proteine_percentuale', 'carboidrati_percentuale', 'grassi_percentuale',
            # distribuzione pasti
            'kcal', 'percentuale_kcal',
            # registered meals
            'kcal_finali', 'kcal_totali'
        }
        
        # Campi che possono legittimamente essere 0
        can_be_zero_fields = {
            'dispendio_sportivo',  # Può essere 0 se non fa sport
            'aggiustamento_obiettivo',  # Può essere 0 per mantenimento
            'fibre_g',  # Potrebbe teoricamente essere 0
            'quantita_g'  # Quando si usa misura_casalinga
        }
        
        # Se il campo è nella lista dei "mai zero", allora 0 è invalido
        if field_name in never_zero_fields:
            return True
            
        # Se il campo può essere zero, allora 0 è valido
        if field_name in can_be_zero_fields:
            return False
            
        # Per campi sconosciuti, assumiamo che 0 sia invalido per sicurezza
        return True
    
    def _complete_missing_macros_fields(self, user_id: str, macros_section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Usa caloric_data_completer per completare i campi mancanti in macros_total.
        
        Args:
            user_id: ID utente
            macros_section: Sezione macros_total da completare
            
        Returns:
            Sezione macros_total completata o None se errore
        """
        try:
            # Crea una copia per il completamento
            completed_macros = macros_section.copy()
            
            # Usa il metodo del completer per calcolare i campi mancanti
            self.caloric_data_completer._complete_macros_total(completed_macros)
            
            return completed_macros
            
        except Exception as e:
            print(f"[EXTRACTION_SERVICE] Errore nel completamento campi mancanti macros_total: {str(e)}")
            return None
    