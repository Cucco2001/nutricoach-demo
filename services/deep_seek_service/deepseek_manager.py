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


class DeepSeekManager:
    """Manager principale per il servizio DeepSeek."""
    
    def __init__(self):
        """Inizializza il manager DeepSeek."""
        self.extractor = NutritionalDataExtractor()
        self.notification_manager = NotificationManager()
        self.interaction_count_key = "interaction_count"
        self.last_extraction_count_key = "last_extraction_count"
        
        # Inizializza i contatori se non esistono
        if self.interaction_count_key not in st.session_state:
            st.session_state[self.interaction_count_key] = 0
        if self.last_extraction_count_key not in st.session_state:
            st.session_state[self.last_extraction_count_key] = 0
    
    def _is_extraction_in_progress(self, user_id: str) -> bool:
        """Controlla se un'estrazione è già in corso per questo utente."""
        # Cerca un thread attivo con il nome specifico
        for thread in threading.enumerate():
            if thread.name == f"DeepSeekExtraction-{user_id}" and thread.is_alive():
                print(f"[DEEPSEEK_MANAGER] Thread di estrazione per l'utente {user_id} è ancora attivo.")
                return True
        return False

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
        
        Args:
            user_id: ID dell'utente
            user_data_manager: Manager per i dati utente
            user_info: Informazioni dell'utente
            extraction_interval: Intervallo di interazioni per l'estrazione
        """
        if not self.is_available():
            return
            
        # Non incrementare il contatore se un'estrazione è già in corso.
        # Questo previene che le interazioni vengano "perse" se l'utente
        # scrive messaggi multipli mentre un'estrazione è attiva.
        # Il contatore verrà aggiornato solo alla prossima interazione
        # dopo che l'estrazione corrente sarà completata.
        if self._is_extraction_in_progress(user_id):
            print(f"[DEEPSEEK_MANAGER] Estrazione per {user_id} già in corso, interazione non contata per ora.")
            return

        # Incrementa il contatore delle interazioni solo se non c'è un'estrazione in corso
        st.session_state[self.interaction_count_key] += 1
        
        # Controlla se sono passate abbastanza interazioni
        last_extraction_count = st.session_state[self.last_extraction_count_key]
        current_interaction_count = st.session_state[self.interaction_count_key]
        interactions_since_last = current_interaction_count - last_extraction_count
        
        if interactions_since_last >= extraction_interval:
            print(f"[DEEPSEEK_MANAGER] Avvio estrazione dopo {interactions_since_last} interazioni.")
            
            # Ottieni la storia delle conversazioni
            conversation_history = user_data_manager.get_agent_qa(user_id)
            
            # Estrai solo le interazioni che non sono state ancora processate
            # Questo è il numero di scambi QA da includere
            num_new_interactions = interactions_since_last
            
            if conversation_history and len(conversation_history) >= num_new_interactions:
                
                new_conversation_part = conversation_history[-num_new_interactions:]
                
                print(f"[DEEPSEEK_MANAGER] Estraggo {len(new_conversation_part)} nuove interazioni.")

                # Avvia l'estrazione asincrona
                self.extractor.extract_data_async(
                    user_id=user_id,
                    conversation_history=new_conversation_part,
                    user_info=user_info or {},
                    interaction_count=current_interaction_count
                )
                
                # Mostra notifica di avvio
                self.notification_manager.show_extraction_started_info()
            else:
                print(f"[DEEPSEEK_MANAGER] Non ci sono abbastanza interazioni nella cronologia per avviare l'estrazione.")
    
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
                    if interaction_count:
                        st.session_state[self.last_extraction_count_key] = interaction_count
                    
                    # Pulisci il timestamp di estrazione per questo utente
                    user_id = result.get("user_id")
                    if user_id:
                        # Questo non è più necessario perché non usiamo più il timestamp
                        # per bloccare le estrazioni. Lasciato commentato per riferimento.
                        # extraction_start_key = f"last_extraction_start_{user_id}"
                        # if extraction_start_key in st.session_state:
                        #    del st.session_state[extraction_start_key]
                        pass
    
    def show_notifications(self) -> None:
        """Mostra le notifiche DeepSeek."""
        self.notification_manager.check_and_show_notifications()
    
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
            # Reset dei contatori
            st.session_state[self.interaction_count_key] = 0
            st.session_state[self.last_extraction_count_key] = 0
            # Cancella le notifiche
            self.notification_manager.clear_notifications()
        return success
    
    def reset_interaction_counts(self) -> None:
        """Reset dei contatori delle interazioni."""
        st.session_state[self.interaction_count_key] = 0
        st.session_state[self.last_extraction_count_key] = 0
        self.notification_manager.clear_notifications()
    
    def get_extraction_status(self) -> Dict[str, Any]:
        """
        Ottiene lo stato attuale dell'estrazione.
        
        Returns:
            Dict con informazioni sullo stato
        """
        return {
            "available": self.is_available(),
            "interaction_count": st.session_state.get(self.interaction_count_key, 0),
            "last_extraction_count": st.session_state.get(self.last_extraction_count_key, 0),
            "interactions_since_last": (
                st.session_state.get(self.interaction_count_key, 0) - 
                st.session_state.get(self.last_extraction_count_key, 0)
            )
        } 