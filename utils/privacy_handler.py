"""
Modulo per gestire privacy e disclaimer dell'applicazione.
Semplice, modulare e riutilizzabile.
"""

import json
import os
from typing import Dict, Any


class PrivacyHandler:
    """Gestisce privacy e disclaimer in modo modulare."""
    
    def __init__(self, storage_file: str = "user_privacy_consent.json"):
        self.storage_file = storage_file
        self.consent_data = self._load_consent_data()
    
    def _load_consent_data(self) -> Dict[str, Any]:
        """Carica i dati di consenso dal file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_consent_data(self):
        """Salva i dati di consenso nel file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.consent_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore nel salvataggio consenso privacy: {str(e)}")
    
    def has_user_accepted(self, user_id: str = "default") -> bool:
        """Verifica se l'utente ha accettato privacy e disclaimer controllando nel file utente."""
        # Per utenti veri, controlla SEMPRE nel file utente
        user_file_path = f"user_data/{user_id}.json"
        
        if not os.path.exists(user_file_path):
            return False
            
        try:
            with open(user_file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                privacy_consent = user_data.get("privacy_consent", {})
                return privacy_consent.get("accepted", False)
        except Exception:
            return False
    
    def accept_privacy(self, user_id: str = "default"):
        """Registra l'accettazione dell'utente salvando SEMPRE nel file utente."""
        from datetime import datetime
        
        consent_info = {
            "accepted": True,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Salva SEMPRE nel file utente
        user_file_path = f"user_data/{user_id}.json"
        
        try:
            # Carica dati utente esistenti o crea struttura vuota
            if os.path.exists(user_file_path):
                with open(user_file_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
            else:
                user_data = {}
            
            # Aggiorna il consenso privacy
            user_data["privacy_consent"] = consent_info
            
            # Assicurati che la directory esista
            os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
            
            # Salva il file utente aggiornato
            with open(user_file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Errore nel salvataggio consenso privacy per {user_id}: {str(e)}")

    def get_privacy_text(self) -> str:
        """Restituisce il testo di privacy e disclaimer."""
        return """
**Privacy & Disclaimer**

**Informativa sulla Privacy**
NutrAICoach è progettato per rispettare la tua privacy. Raccogliamo esclusivamente i dati necessari per personalizzare i tuoi piani nutrizionali:
- Informazioni personali di base (età, peso, altezza, sesso, livello di attività)
- Preferenze alimentari e restrizioni dietetiche
- Obiettivi nutrizionali e di salute
- Cronologia delle interazioni con l'assistente (solo per migliorare il servizio)

I tuoi dati vengono gestiti in modo anonimo e sicuro. Non condividiamo mai le tue informazioni personali con terze parti. I dati vengono utilizzati esclusivamente per fornire consigli nutrizionali personalizzati e migliorare l'esperienza utente.

**Disclaimer Medico Importante**
I consigli nutrizionali forniti da NutrAICoach sono di natura puramente informativa ed educativa. Questo strumento:
- NON sostituisce in alcun modo il parere di un medico, nutrizionista o dietista qualificato
- NON fornisce diagnosi mediche o trattamenti terapeutici
- NON è adatto per persone con patologie specifiche senza supervisione medica

**Avvertenze Importanti**
Prima di seguire il piano nutrizionale generato:
- Consulta sempre un professionista sanitario qualificato se hai patologie croniche (diabete, ipertensione, malattie cardiovascolari, disturbi alimentari, etc.)
- Informa il tuo medico se stai assumendo farmaci che potrebbero interagire con cambiamenti dietetici
- Non utilizzare questo strumento se sei in gravidanza, allattamento o hai disturbi alimentari senza supervisione medica


Utilizzando NutrAICoach accetti di aver compreso queste limitazioni e di utilizzare il servizio in modo responsabile.
        """.strip()
    
    def get_reminder_text(self) -> str:
        """Restituisce il testo di reminder breve."""
        return "⚕️ Questi consigli non sostituiscono un consulto medico/nutrizionale professionale."


# Istanza globale per facilità d'uso
privacy_handler = PrivacyHandler()


def check_privacy_acceptance(user_id: str = "default") -> bool:
    """Funzione di convenienza per verificare l'accettazione."""
    return privacy_handler.has_user_accepted(user_id)


def accept_privacy_terms(user_id: str = "default"):
    """Funzione di convenienza per accettare i termini."""
    privacy_handler.accept_privacy(user_id)


def get_privacy_disclaimer_text() -> str:
    """Funzione di convenienza per ottenere il testo."""
    return privacy_handler.get_privacy_text()


def get_reminder() -> str:
    """Funzione di convenienza per il reminder."""
    return privacy_handler.get_reminder_text() 