"""
Gestore per le notifiche dell'interfaccia utente per il servizio DeepSeek.

Questo modulo gestisce le notifiche e feedback all'utente riguardo lo stato
dell'estrazione automatica dei dati nutrizionali.
"""

import streamlit as st
from typing import Dict, List, Any, Optional


class NotificationManager:
    """Gestore per le notifiche dell'interfaccia utente."""
    
    def __init__(self):
        """Inizializza il gestore delle notifiche."""
        self.notification_key = "deepseek_notification"
    
    def check_and_show_notifications(self) -> None:
        """Controlla e mostra le notifiche DeepSeek se presenti."""
        if hasattr(st.session_state, self.notification_key):
            notification = getattr(st.session_state, self.notification_key)
            
            if notification and notification.get("show", False):
                self._display_notification(notification)
                # Marca come mostrata
                notification["show"] = False
    
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
        Imposta una notifica nel session state.
        
        Args:
            notification_type: Tipo di notifica (success, warning, error, info)
            message: Messaggio da mostrare
        """
        setattr(st.session_state, self.notification_key, {
            "type": notification_type,
            "message": message,
            "show": True
        })
    
    def clear_notifications(self) -> None:
        """Cancella tutte le notifiche pendenti."""
        if hasattr(st.session_state, self.notification_key):
            delattr(st.session_state, self.notification_key)
    
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
        st.info("📊 Estrazione dati nutrizionali avviata in background...")
        print("[NOTIFICATION_MANAGER] Notifica di avvio estrazione mostrata") 