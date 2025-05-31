"""
Servizio per l'estrazione e gestione dei dati nutrizionali con DeepSeek.

Questo modulo gestisce l'estrazione asincrona, il salvataggio e la sincronizzazione
dei dati nutrizionali estratti dalle conversazioni usando DeepSeek AI.
"""

import os
import json
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional
from .deepseek_client import DeepSeekClient


class NutritionalDataExtractor:
    """Servizio per l'estrazione asincrona di dati nutrizionali."""
    
    def __init__(self):
        """Inizializza il servizio di estrazione."""
        self.deepseek_client = DeepSeekClient()
        self.results_queue = queue.Queue()
        self.lock = threading.Lock()
        self.file_access_lock = threading.Lock()
        
    def is_available(self) -> bool:
        """Verifica se il servizio è disponibile."""
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
            interaction_count: Numero di interazioni correnti
        """
        if not self.is_available():
            print("[EXTRACTION_SERVICE] DeepSeek non disponibile")
            return
            
        print(f"[EXTRACTION_SERVICE] Avvio estrazione asincrona per utente {user_id}")
        
        # Crea una copia locale dei dati per il thread
        user_info_copy = dict(user_info) if user_info else {}
        
        def extract_in_background():
            """Funzione per l'estrazione in background."""
            try:
                # Estrai i dati usando DeepSeek
                extracted_data = self.deepseek_client.extract_nutritional_data(
                    conversation_history, 
                    user_info_copy
                )
                
                if extracted_data:
                    success = self._save_extracted_data(user_id, extracted_data)
                    
                    # Comunica il risultato tramite la coda
                    with self.lock:
                        self.results_queue.put({
                            "success": success,
                            "user_id": user_id,
                            "interaction_count": interaction_count
                        })
                else:
                    with self.lock:
                        self.results_queue.put({
                            "success": False,
                            "error": "Nessun dato estratto",
                            "user_id": user_id
                        })
                        
            except Exception as e:
                print(f"[EXTRACTION_SERVICE] Errore nell'estrazione: {str(e)}")
                with self.lock:
                    self.results_queue.put({
                        "success": False,
                        "error": str(e),
                        "user_id": user_id
                    })
        
        # Avvia il thread
        thread = threading.Thread(target=extract_in_background, daemon=True)
        thread.start()
        
        print(f"[EXTRACTION_SERVICE] Thread avviato per utente {user_id}")
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Recupera i risultati dell'estrazione disponibili.
        
        Returns:
            Lista dei risultati disponibili
        """
        results = []
        
        with self.lock:
            while not self.results_queue.empty():
                try:
                    result = self.results_queue.get_nowait()
                    results.append(result)
                except queue.Empty:
                    break
                    
        return results
    
    def _save_extracted_data(self, user_id: str, extracted_data: Dict[str, Any]) -> bool:
        """
        Salva i dati estratti nel file utente.
        
        Args:
            user_id: ID dell'utente
            extracted_data: Dati estratti da DeepSeek
            
        Returns:
            True se il salvataggio è andato a buon fine
        """
        try:
            with self.file_access_lock:
                print(f"[EXTRACTION_SERVICE] Inizio salvataggio per utente {user_id}")
                
                # Carica il file utente
                user_file_path = f"user_data/{user_id}.json"
                
                if not os.path.exists(user_file_path):
                    print(f"[EXTRACTION_SERVICE] File utente {user_id} non trovato")
                    return False
                
                # Operazione atomica: leggi, modifica, scrivi tutto sotto lock
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # Crea una copia di backup dei dati nutrizionali esistenti
                existing_data = user_data.get("nutritional_info_extracted", {}).copy()
                print(f"[EXTRACTION_SERVICE] Backup dati esistenti: {list(existing_data.keys())}")
                
                # Inizializza la sezione se non esiste
                if "nutritional_info_extracted" not in user_data:
                    user_data["nutritional_info_extracted"] = {}
                
                # Ripristina i dati esistenti dalla copia di backup
                user_data["nutritional_info_extracted"] = existing_data.copy()
                
                # Merge intelligente dei dati
                changes_made = self._merge_extracted_data(
                    user_data["nutritional_info_extracted"], 
                    extracted_data, 
                    user_id
                )
                
                # Aggiorna il timestamp se ci sono stati cambiamenti
                if changes_made:
                    user_data["nutritional_info_extracted"]["last_updated"] = datetime.now().isoformat()
                    print(f"[EXTRACTION_SERVICE] Timestamp aggiornato per utente {user_id}")
                
                # Verifica finale
                if not user_data["nutritional_info_extracted"]:
                    print(f"[EXTRACTION_SERVICE] ERRORE: Dati vuoti prima del salvataggio!")
                    user_data["nutritional_info_extracted"] = existing_data
                
                final_keys = list(user_data["nutritional_info_extracted"].keys())
                print(f"[EXTRACTION_SERVICE] Dati finali da salvare: {final_keys}")
                
                # Salva il file solo se ci sono stati cambiamenti
                if changes_made or not existing_data:
                    with open(user_file_path, 'w', encoding='utf-8') as f:
                        json.dump(user_data, f, indent=2, ensure_ascii=False)
                    print(f"[EXTRACTION_SERVICE] File salvato con successo per utente {user_id}")
                else:
                    print(f"[EXTRACTION_SERVICE] Nessun cambiamento, file non modificato per utente {user_id}")
                    
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
        Fa il merge dei nuovi dati con quelli esistenti.
        
        Args:
            existing_data: Dati esistenti (modificati in place)
            new_data: Nuovi dati da DeepSeek
            user_id: ID utente per logging
            
        Returns:
            True se sono stati fatti cambiamenti
        """
        changes_made = False
        
        for data_type, data_content in new_data.items():
            if data_content:  # Solo se ci sono dati
                if data_type in existing_data:
                    # Se il tipo di dato esiste già, fai un merge intelligente
                    if isinstance(data_content, dict) and isinstance(existing_data[data_type], dict):
                        # Conta le chiavi prima e dopo per vedere se ci sono cambiamenti
                        keys_before = set(existing_data[data_type].keys())
                        existing_data[data_type].update(data_content)
                        keys_after = set(existing_data[data_type].keys())
                        if keys_before != keys_after or any(k in data_content for k in keys_before):
                            changes_made = True
                            print(f"[EXTRACTION_SERVICE] Aggiornato (merge) {data_type} per utente {user_id}")
                    elif isinstance(data_content, list) and isinstance(existing_data[data_type], list):
                        # Per le liste, sostituisci solo se i nuovi dati sono più completi
                        if len(data_content) >= len(existing_data[data_type]):
                            existing_data[data_type] = data_content
                            changes_made = True
                            print(f"[EXTRACTION_SERVICE] Sostituito (lista più completa) {data_type} per utente {user_id}")
                        else:
                            print(f"[EXTRACTION_SERVICE] Mantenuto {data_type} esistente (più completo) per utente {user_id}")
                    else:
                        # Sostituisci per altri tipi
                        existing_data[data_type] = data_content
                        changes_made = True
                        print(f"[EXTRACTION_SERVICE] Sostituito {data_type} per utente {user_id}")
                else:
                    # Se il tipo di dato non esiste, aggiungilo
                    existing_data[data_type] = data_content
                    changes_made = True
                    print(f"[EXTRACTION_SERVICE] Aggiunto nuovo {data_type} per utente {user_id}")
        
        return changes_made
    
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