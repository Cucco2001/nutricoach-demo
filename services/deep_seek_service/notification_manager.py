"""
Gestore per le notifiche dell'interfaccia utente per il servizio DeepSeek.

Questo modulo gestisce le notifiche e feedback all'utente riguardo lo stato
dell'estrazione automatica dei dati nutrizionali.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import threading

# Import del nuovo state manager
from services.state_service import app_state


class NotificationManager:
    """Gestore per le notifiche dell'interfaccia utente."""
    
    def __init__(self):
        """Inizializza il gestore delle notifiche."""
        self.notification_key = "deepseek_notification"
    
    def _is_streamlit_context_available(self) -> bool:
        """
        Verifica se siamo nel contesto principale di Streamlit.
        
        Returns:
            bool: True se possiamo accedere a st.session_state
        """
        try:
            # Prova ad accedere al session_state per verificare il contesto
            _ = st.session_state
            return True
        except Exception:
            return False
    
    def check_and_show_notifications(self) -> None:
        """Controlla e mostra le notifiche DeepSeek se presenti."""
        # Usa app_state come sorgente primaria
        notification = app_state.get(self.notification_key)
        
        if notification and notification.get("show", False):
            self._display_notification(notification)
            # Marca come mostrata
            notification["show"] = False
            app_state.set(self.notification_key, notification)
    
    def _display_notification(self, notification: Dict[str, Any]) -> None:
        """
        Mostra una notifica nell'interfaccia.
        
        Args:
            notification: Dict con type, message e show
        """
        notification_type = notification.get("type", "info")
        message = notification.get("message", "")
        
        if notification_type == "success":
            st.success(message)
        elif notification_type == "warning":
            st.warning(message)
        elif notification_type == "error":
            st.error(message)
        elif notification_type == "info":
            st.info(message)
    
    def set_success_notification(self, message: str = "✅ Dati nutrizionali aggiornati automaticamente!") -> None:
        """
        Imposta una notifica di successo.
        
        Args:
            message: Messaggio da mostrare
        """
        self._set_notification("success", message)
    
    def set_warning_notification(self, message: str) -> None:
        """
        Imposta una notifica di warning.
        
        Args:
            message: Messaggio da mostrare
        """
        self._set_notification("warning", message)
    
    def set_error_notification(self, message: str) -> None:
        """
        Imposta una notifica di errore.
        
        Args:
            message: Messaggio da mostrare
        """
        self._set_notification("error", message)
    
    def set_info_notification(self, message: str) -> None:
        """
        Imposta una notifica informativa.
        
        Args:
            message: Messaggio da mostrare
        """
        self._set_notification("info", message)
    
    def _set_notification(self, notification_type: str, message: str) -> None:
        """
        Imposta una notifica nell'app state.
        
        Args:
            notification_type: Tipo di notifica (success, warning, error, info)
            message: Messaggio da mostrare
        """
        notification = {
            "type": notification_type,
            "message": message,
            "show": True
        }
        
        # Salva sempre in app_state
        app_state.set(self.notification_key, notification)
        
        if not self._is_streamlit_context_available():
            # Se non siamo nel contesto Streamlit (thread in background), 
            # logga solo un messaggio
            print(f"[NOTIFICATION_MANAGER] {notification_type.upper()}: {message}")
    
    def clear_notifications(self) -> None:
        """Cancella tutte le notifiche pendenti."""
        app_state.delete(self.notification_key)
    
    def process_extraction_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Processa i risultati dell'estrazione e imposta le notifiche appropriate.
        
        Args:
            results: Lista dei risultati dell'estrazione
        """
        for result in results:
            if result.get("success"):
                self.set_success_notification()
                print("[NOTIFICATION_MANAGER] Notifica di successo impostata")
            elif "error" in result:
                error_msg = f"⚠️ Errore nell'estrazione automatica: {result['error']}"
                self.set_warning_notification(error_msg)
                print(f"[NOTIFICATION_MANAGER] Notifica di errore impostata: {result['error']}")
    
    def show_extraction_started_info(self) -> None:
        """Mostra una notifica che l'estrazione è iniziata."""
        if self._is_streamlit_context_available():
            # Se siamo nel contesto principale di Streamlit, mostra direttamente
            st.info("📊 Estrazione dati nutrizionali avviata in background...")
            print("[NOTIFICATION_MANAGER] Notifica di avvio estrazione mostrata")
        else:
            # Se siamo in un thread in background, imposta una notifica per dopo
            self.set_info_notification("📊 Estrazione dati nutrizionali avviata in background...")
            print("[NOTIFICATION_MANAGER] Notifica di avvio estrazione programmata per il thread principale") 