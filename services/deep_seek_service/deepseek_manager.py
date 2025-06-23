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
        # Traccia solo l'indice dell'ultima conversazione processata per evitare duplicati
        self.user_last_conversation_index = {}  # {user_id: index_of_last_processed_conversation}
        # Set per tracciare conversazioni già in coda per evitare duplicati
        self.queued_conversations = set()  # {(user_id, conversation_index)}
    
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
        Controlla se ci sono nuove conversazioni e le mette in coda per l'estrazione.
        
        Args:
            user_id: ID dell'utente
            user_data_manager: Manager per i dati utente (può essere None, legge dal file)
            user_info: Informazioni dell'utente
            extraction_interval: Intervallo di interazioni per l'estrazione (default 1 = ogni conversazione)
        """
        if not self.is_available():
            return
            
        # Ottieni le conversazioni direttamente dal file
        conversation_history = self._get_user_conversations(user_id)
        
        if not conversation_history:
            print(f"[DEEPSEEK_MANAGER] Nessuna conversazione trovata per {user_id}")
            return
            
        # Trova le conversazioni nuove basandosi sull'indice
        total_conversations = len(conversation_history)
        last_processed_index = self.user_last_conversation_index.get(user_id, -1)
        
        # Metti in coda ogni conversazione nuova individualmente
        new_conversations_added = 0
        for i in range(last_processed_index + 1, total_conversations, extraction_interval):
            # Evita duplicati nella coda
            conversation_key = (user_id, i)
            if conversation_key not in self.queued_conversations:
                # Aggiungi alla coda
                self.queue.put({
                    'user_id': user_id,
                    'user_info': user_info,
                    'conversation_index': i,
                    'conversation': conversation_history[i]
                })
                self.queued_conversations.add(conversation_key)
                new_conversations_added += 1
        
        if new_conversations_added > 0:
            print(f"[DEEPSEEK_MANAGER] Aggiunte {new_conversations_added} conversazioni alla coda per {user_id}")
            print(f"[DEEPSEEK_MANAGER] Coda attuale: {self.queue.qsize()} elementi")
            
            # Se non c'è un'estrazione in corso, avvia il processing della coda
            if not self._is_extraction_in_progress(user_id):
                self.process_queue()
        else:
            print(f"[DEEPSEEK_MANAGER] Nessuna nuova conversazione da aggiungere per {user_id}")
    
    def check_and_process_results(self) -> None:
        """Controlla i risultati dell'estrazione e processa le notifiche."""
        # Recupera i risultati disponibili
        results = self.extractor.get_results()
        
        if results:
            # Processa le notifiche
            self.notification_manager.process_extraction_results(results)
        
        # Controlla sempre se ci sono richieste in coda da processare
        # Questo assicura che la coda continui ad essere processata anche se
        # il thread precedente è terminato
        self.process_queue()
    
    def show_notifications(self) -> None:
        """Mostra le notifiche DeepSeek."""
        self.notification_manager.check_and_show_notifications()
    
    def process_queue(self) -> None:
        """
        Processa UNA singola conversazione dalla coda.
        Chiamato quando un'estrazione finisce per avviare la prossima se presente.
        """
        try:
            # Prendi una richiesta dalla coda
            if not self.queue.empty():
                request = self.queue.get_nowait()
                
                user_id = request['user_id']
                user_info = request['user_info']
                conversation_index = request['conversation_index']
                conversation = request['conversation']
                
                # Rimuovi dalla lista delle conversazioni in coda
                conversation_key = (user_id, conversation_index)
                self.queued_conversations.discard(conversation_key)
                
                print(f"[DEEPSEEK_MANAGER] Processando conversazione {conversation_index} per utente {user_id}")
                
                # Verifica che non ci sia già un'estrazione in corso
                if not self._is_extraction_in_progress(user_id):
                    # Avvia l'estrazione per questa singola conversazione
                    self.extractor.extract_data_async(
                        user_id=user_id,
                        conversation_history=[conversation],  # Una sola conversazione
                        user_info=user_info,
                        interaction_count=conversation_index + 1,
                        deepseek_manager=self
                    )
                    
                    # Aggiorna l'indice dell'ultima conversazione processata
                    self.user_last_conversation_index[user_id] = conversation_index
                    
                    # Mostra notifica
                    self.notification_manager.show_extraction_started_info()
                    
                    print(f"[DEEPSEEK_MANAGER] Estrazione avviata per conversazione {conversation_index}")
                    print(f"[DEEPSEEK_MANAGER] Rimanenti in coda: {self.queue.qsize()}")
                else:
                    # Se c'è ancora un'estrazione in corso, rimetti in coda
                    self.queue.put(request)
                    self.queued_conversations.add(conversation_key)
                    print(f"[DEEPSEEK_MANAGER] Estrazione in corso, richiesta rimessa in coda")
                    
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
            # Reset dell'indice conversazioni
            if user_id in self.user_last_conversation_index:
                del self.user_last_conversation_index[user_id]
            
            # Rimuovi conversazioni in coda per questo utente
            self.queued_conversations = {
                key for key in self.queued_conversations 
                if key[0] != user_id
            }
            
            # Cancella le notifiche
            self.notification_manager.clear_notifications()
        return success
    
    def reset_interaction_counts(self, user_id: str = None) -> None:
        """Reset dei contatori delle interazioni."""
        if user_id:
            # Reset per un utente specifico
            if user_id in self.user_last_conversation_index:
                del self.user_last_conversation_index[user_id]
            
            # Rimuovi conversazioni in coda per questo utente
            self.queued_conversations = {
                key for key in self.queued_conversations 
                if key[0] != user_id
            }
        else:
            # Reset globale
            self.user_last_conversation_index.clear()
            self.queued_conversations.clear()
            
        self.notification_manager.clear_notifications()
    
    def get_extraction_status(self, user_id: str) -> Dict[str, Any]:
        """
        Ottiene lo stato attuale dell'estrazione per un utente.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Dict con informazioni sullo stato
        """
        last_processed_index = self.user_last_conversation_index.get(user_id, -1)
        conversations_in_queue = sum(1 for key in self.queued_conversations if key[0] == user_id)
        
        return {
            "available": self.is_available(),
            "last_processed_conversation_index": last_processed_index,
            "user_conversations_in_queue": conversations_in_queue,
            "extraction_in_progress": self._is_extraction_in_progress(user_id),
            "total_queue_size": self.queue.qsize()
        } 