"""
Manager principale del servizio DeepSeek.

Questo modulo fornisce un'interfaccia unificata per tutti i componenti
del servizio DeepSeek, gestendo l'integrazione con l'applicazione principale.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from .deepseek_client import DeepSeekClient
from .extraction_service import NutritionalDataExtractor
from .notification_manager import NotificationManager
import time
import threading
import queue
import os
import json


class DeepSeekManager:
    """Manager principale per il servizio DeepSeek."""
    
    def __init__(self):
        """Inizializza il manager DeepSeek."""
        self.extractor = NutritionalDataExtractor()
        self.notification_manager = NotificationManager()
        # Coda globale thread-safe indipendente da Streamlit
        self.queue = queue.Queue()
        # Contatori interni indipendenti da Streamlit
        self.user_interaction_counts = {}  # {user_id: total_interactions}
        self.user_last_extraction_counts = {}  # {user_id: last_processed_interactions}
    
    def _is_extraction_in_progress(self, user_id: str) -> bool:
        """Controlla se un'estrazione è già in corso per questo utente."""
        # Cerca un thread attivo con il nome specifico
        target_thread_name = f"DeepSeekExtraction-{user_id}"
        active_threads = []
        
        for thread in threading.enumerate():
            active_threads.append(f"{thread.name}({'alive' if thread.is_alive() else 'dead'})")
            if thread.name == target_thread_name and thread.is_alive():
                print(f"[DEEPSEEK_MANAGER] Thread di estrazione per l'utente {user_id} è ancora attivo.")
                return True
        
        # Debug: mostra tutti i thread attivi quando non trova quello specifico
        if target_thread_name not in [t.split('(')[0] for t in active_threads]:
            print(f"[DEEPSEEK_MANAGER] Thread {target_thread_name} non trovato. Thread attivi: {active_threads[:3]}")
        
        return False
    
    def _get_user_conversations(self, user_id: str) -> List[Any]:
        """
        Legge le conversazioni direttamente dal file utente.
        Thread-safe, non dipende da session_state.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Lista delle conversazioni agent_qa o lista vuota se errore
        """
        try:
            user_file_path = f"user_data/{user_id}.json"
            
            if not os.path.exists(user_file_path):
                print(f"[DEEPSEEK_MANAGER] File utente non trovato: {user_file_path}")
                return []
                
            with open(user_file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            conversations = user_data.get('nutritional_info', {}).get('agent_qa', [])
            print(f"[DEEPSEEK_MANAGER] Trovate {len(conversations)} conversazioni per utente {user_id}")
            return conversations
            
        except Exception as e:
            print(f"[DEEPSEEK_MANAGER] Errore nel leggere conversazioni per {user_id}: {str(e)}")
            return []

    def is_available(self) -> bool:
        """Verifica se il servizio DeepSeek è disponibile."""
        return self.extractor.is_available()
    
    def check_and_extract_if_needed(
        self, 
        user_id: str, 
        user_data_manager: Any,
        user_info: Optional[Dict[str, Any]] = None,
        extraction_interval: int = 1
    ) -> None:
        """
        Controlla se è necessario avviare un'estrazione e la avvia se appropriato.
        Completamente indipendente da Streamlit.
        
        Args:
            user_id: ID dell'utente
            user_data_manager: Manager per i dati utente (può essere None, legge dal file)
            user_info: Informazioni dell'utente
            extraction_interval: Intervallo di interazioni per l'estrazione
        """
        if not self.is_available():
            return
            
        # Incrementa SEMPRE il contatore interno delle interazioni
        if user_id not in self.user_interaction_counts:
            self.user_interaction_counts[user_id] = 0
        if user_id not in self.user_last_extraction_counts:
            self.user_last_extraction_counts[user_id] = 0
            
        self.user_interaction_counts[user_id] += 1
        
        # Controlla se sono passate abbastanza interazioni
        last_extraction_count = self.user_last_extraction_counts[user_id]
        current_interaction_count = self.user_interaction_counts[user_id]
        interactions_since_last = current_interaction_count - last_extraction_count
        
        if interactions_since_last >= extraction_interval:
            print(f"[DEEPSEEK_MANAGER] {interactions_since_last} interazioni dall'ultima estrazione per {user_id}.")
            
            # Controlla se c'è già un'estrazione in corso
            if self._is_extraction_in_progress(user_id):
                print(f"[DEEPSEEK_MANAGER] Estrazione già in corso per {user_id}, richiesta messa in coda.")
                # Metti in coda la richiesta per processarla dopo
                self.queue.put({
                    'user_id': user_id,
                    'user_info': user_info
                })
                return
            
            # Ottieni le conversazioni direttamente dal file
            conversation_history = self._get_user_conversations(user_id)
            
            if conversation_history and len(conversation_history) >= interactions_since_last:
                new_conversation_part = conversation_history[-interactions_since_last:]
                
                print(f"[DEEPSEEK_MANAGER] Avvio estrazione di {len(new_conversation_part)} nuove conversazioni.")

                # Avvia l'estrazione asincrona
                self.extractor.extract_data_async(
                    user_id=user_id,
                    conversation_history=new_conversation_part,
                    user_info=user_info or {},
                    interaction_count=current_interaction_count,
                    deepseek_manager=self
                )
                
                # Aggiorna il contatore interno dell'ultima estrazione
                self.user_last_extraction_counts[user_id] = current_interaction_count
                
                # Mostra notifica di avvio
                self.notification_manager.show_extraction_started_info()
            else:
                print(f"[DEEPSEEK_MANAGER] Non ci sono abbastanza conversazioni per {user_id}: {len(conversation_history) if conversation_history else 0}")
    
    def check_and_process_results(self) -> None:
        """Controlla i risultati dell'estrazione e processa le notifiche."""
        # Recupera i risultati disponibili
        results = self.extractor.get_results()
        
        if results:
            # Processa le notifiche
            self.notification_manager.process_extraction_results(results)
            
            # Aggiorna i contatori per i risultati di successo
            for result in results:
                if result.get("success"):
                    interaction_count = result.get("interaction_count")
                    user_id = result.get("user_id")
                    
                    if interaction_count and user_id:
                        # Aggiorna contatori interni (thread-safe)
                        self.user_last_extraction_counts[user_id] = interaction_count
                        
                        # Aggiorna session_state per compatibilità legacy (solo se disponibile)
                        try:
                            import streamlit as st
                            if hasattr(st, 'session_state'):
                                # Solo per l'utente corrente nella sessione
                                if user_id in str(st.session_state.get('user_info', {}).get('user_id', '')):
                                    st.session_state.last_extraction_count = interaction_count
                        except Exception as e:
                            # Ignora errori se non siamo in contesto Streamlit
                            print(f"[DEEPSEEK_MANAGER] Avviso: impossibile aggiornare session_state: {e}")
        
        # Controlla sempre se ci sono richieste in coda da processare
        # Questo assicura che la coda continui ad essere processata anche se
        # il thread precedente è terminato
        self.process_queue()
    
    def show_notifications(self) -> None:
        """Mostra le notifiche DeepSeek."""
        self.notification_manager.check_and_show_notifications()
    
    def process_queue(self) -> None:
        """
        Processa la coda delle richieste di estrazione pendenti.
        Chiamato quando un'estrazione finisce per avviare la prossima se presente.
        Legge direttamente dal file utente, thread-safe.
        """
        try:
            # Controlla se c'è una richiesta in coda (coda thread-safe globale)
            if not self.queue.empty():
                # Prendi la prossima richiesta
                request = self.queue.get_nowait()
                
                user_id = request['user_id']
                user_info = request['user_info']
                
                print(f"[DEEPSEEK_MANAGER] Processando richiesta in coda per utente {user_id}")
                
                # Verifica che non ci sia già un'estrazione in corso
                if not self._is_extraction_in_progress(user_id):
                    # Determina cosa processare leggendo direttamente dal file utente
                    conversation_history = self._get_user_conversations(user_id)
                    
                    if conversation_history:
                        # Usa i contatori interni (completamente indipendenti da Streamlit)
                        if user_id not in self.user_interaction_counts:
                            self.user_interaction_counts[user_id] = len(conversation_history)
                        if user_id not in self.user_last_extraction_counts:
                            self.user_last_extraction_counts[user_id] = 0
                            
                        last_extraction_count = self.user_last_extraction_counts[user_id]
                        current_interaction_count = self.user_interaction_counts[user_id]
                        interactions_since_last = current_interaction_count - last_extraction_count
                        
                        if interactions_since_last > 0 and len(conversation_history) >= interactions_since_last:
                            new_conversation_part = conversation_history[-interactions_since_last:]
                            
                            print(f"[DEEPSEEK_MANAGER] Avvio estrazione dalla coda di {len(new_conversation_part)} conversazioni.")
                            
                            # Avvia l'estrazione
                            self.extractor.extract_data_async(
                                user_id=user_id,
                                conversation_history=new_conversation_part,
                                user_info=user_info,
                                interaction_count=current_interaction_count,
                                deepseek_manager=self
                            )
                            
                            # Aggiorna il contatore interno
                            self.user_last_extraction_counts[user_id] = current_interaction_count
                            
                            # Mostra notifica
                            self.notification_manager.show_extraction_started_info()
                        else:
                            print(f"[DEEPSEEK_MANAGER] Nessuna nuova conversazione da processare per {user_id}")
                    else:
                        print(f"[DEEPSEEK_MANAGER] Nessuna conversazione trovata per {user_id}")
                else:
                    # Se c'è ancora un'estrazione in corso, rimetti in coda
                    self.queue.put(request)
                    print(f"[DEEPSEEK_MANAGER] Estrazione ancora in corso, richiesta rimessa in coda")
                    
        except queue.Empty:
            # Coda vuota, niente da fare
            pass
        except Exception as e:
            print(f"[DEEPSEEK_MANAGER] Errore nel processare la coda: {str(e)}")
    
    def clear_user_data(self, user_id: str) -> bool:
        """
        Cancella tutti i dati DeepSeek per un utente.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            True se la cancellazione è riuscita
        """
        success = self.extractor.clear_user_extracted_data(user_id)
        if success:
            # Reset dei contatori interni
            if user_id in self.user_interaction_counts:
                del self.user_interaction_counts[user_id]
            if user_id in self.user_last_extraction_counts:
                del self.user_last_extraction_counts[user_id]
            # Cancella le notifiche
            self.notification_manager.clear_notifications()
        return success
    
    def reset_interaction_counts(self, user_id: str = None) -> None:
        """Reset dei contatori delle interazioni."""
        if user_id:
            # Reset per un utente specifico
            if user_id in self.user_interaction_counts:
                del self.user_interaction_counts[user_id]
            if user_id in self.user_last_extraction_counts:
                del self.user_last_extraction_counts[user_id]
        else:
            # Reset globale
            self.user_interaction_counts.clear()
            self.user_last_extraction_counts.clear()
        self.notification_manager.clear_notifications()
    
    def get_extraction_status(self, user_id: str) -> Dict[str, Any]:
        """
        Ottiene lo stato attuale dell'estrazione per un utente.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dict con informazioni sullo stato
        """
        interaction_count = self.user_interaction_counts.get(user_id, 0)
        last_extraction_count = self.user_last_extraction_counts.get(user_id, 0)
        
        return {
            "available": self.is_available(),
            "interaction_count": interaction_count,
            "last_extraction_count": last_extraction_count,
            "interactions_since_last": interaction_count - last_extraction_count,
            "extraction_in_progress": self._is_extraction_in_progress(user_id),
            "queue_size": self.queue.qsize()
        } 