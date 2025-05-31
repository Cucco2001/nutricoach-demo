"""
Modulo per il tracking dei progressi dell'utente.

Gestisce l'input dei dati di progresso (peso, misurazioni) e
l'integrazione con il sistema di valutazione periodica.
"""

import streamlit as st
import json
from datetime import datetime


class ProgressTracker:
    """Gestisce il tracking dei progressi dell'utente"""
    
    def __init__(self, user_data_manager, chat_handler):
        """
        Inizializza il tracker dei progressi.
        
        Args:
            user_data_manager: Gestore dei dati utente
            chat_handler: Funzione per gestire la chat con l'assistente
        """
        self.user_data_manager = user_data_manager
        self.chat_handler = chat_handler
    
    def show_tracking_form(self):
        """Mostra il form per il tracking dei progressi"""
        with st.expander("Traccia i tuoi progressi"):
            weight = st.number_input("Peso attuale (kg)", min_value=30.0, max_value=200.0, step=0.1, format="%.1f")
            date = st.date_input("Data misurazione")
            measurements = {}
            
            col1, col2 = st.columns(2)
            with col1:
                measurements["circonferenza_vita"] = st.number_input("Circonferenza vita (cm)", min_value=0.0, step=0.1, format="%.1f")
                measurements["circonferenza_fianchi"] = st.number_input("Circonferenza fianchi (cm)", min_value=0.0, step=0.1, format="%.1f")
            
            with col2:
                measurements["circonferenza_braccio"] = st.number_input("Circonferenza braccio (cm)", min_value=0.0, step=0.1, format="%.1f")
                measurements["circonferenza_coscia"] = st.number_input("Circonferenza coscia (cm)", min_value=0.0, step=0.1, format="%.1f")
            
            if st.button("Salva progressi"):
                self._save_progress(weight, date, measurements)
    
    def _save_progress(self, weight, date, measurements):
        """
        Salva i progressi dell'utente e verifica se è necessaria una valutazione periodica.
        
        Args:
            weight: Peso attuale
            date: Data della misurazione  
            measurements: Dizionario delle misurazioni
        """
        # Arrotonda tutti i valori a una cifra decimale
        weight = round(weight, 1)
        measurements = {k: round(v, 1) for k, v in measurements.items()}
        
        # Salva i progressi
        self.user_data_manager.track_progress(
            user_id=st.session_state.user_info["id"],
            weight=weight,
            date=date.strftime("%Y-%m-%d"),
            measurements=measurements
        )
        
        # Verifica se è necessaria una valutazione periodica
        self._check_periodic_evaluation()
        
        st.success("Progressi salvati con successo!")
        st.rerun()
    
    def _check_periodic_evaluation(self):
        """Verifica se è necessaria una valutazione periodica e la esegue"""
        progress_history = self.user_data_manager.get_progress_history(st.session_state.user_info["id"])
        
        if len(progress_history) >= 2:
            last_entry = progress_history[-1]
            first_entry = progress_history[0]
            
            # Calcola le settimane passate
            last_date = datetime.strptime(last_entry.date, "%Y-%m-%d")
            first_date = datetime.strptime(first_entry.date, "%Y-%m-%d")
            weeks_passed = (last_date - first_date).days / 7
            
            if weeks_passed >= 3:
                self._perform_periodic_evaluation(first_entry, last_entry, weeks_passed)
    
    def _perform_periodic_evaluation(self, first_entry, last_entry, weeks_passed):
        """
        Esegue una valutazione periodica del progresso.
        
        Args:
            first_entry: Prima entry del progresso
            last_entry: Ultima entry del progresso
            weeks_passed: Settimane trascorse
        """
        # Calcola la variazione di peso
        weight_change = last_entry.weight - first_entry.weight
        
        # Prepara il prompt per l'agente
        evaluation_prompt = f"""
        È passato un periodo di {weeks_passed:.1f} settimane dall'inizio del piano alimentare.
        È necessario valutare i progressi e adattare il piano.

        DATI INIZIALI:
        • Peso iniziale: {first_entry.weight} kg
        • Data iniziale: {first_entry.date}

        DATI ATTUALI:
        • Peso attuale: {last_entry.weight} kg
        • Data attuale: {last_entry.date}
        • Variazione peso: {weight_change:+.1f} kg

        MISURAZIONI INIZIALI:
        {json.dumps(first_entry.measurements, indent=2)}

        MISURAZIONI ATTUALI:
        {json.dumps(last_entry.measurements, indent=2)}

        OBIETTIVO ORIGINALE:
        • {st.session_state.user_info['obiettivo']}

        Per favore:
        1. Valuta i progressi rispetto all'obiettivo
        2. Ricalcola il metabolismo basale e il fabbisogno calorico
        3. Aggiorna le quantità dei macronutrienti
        4. Modifica il piano alimentare in base ai nuovi calcoli
        5. Fornisci raccomandazioni specifiche per il prossimo periodo

        IMPORTANTE: Inizia la tua risposta con "📊 VALUTAZIONE PERIODICA" e poi procedi con l'analisi.
        Assicurati di includere:
        - Un riepilogo dei progressi
        - I nuovi calcoli del metabolismo e delle calorie
        - Le modifiche al piano alimentare
        - Le raccomandazioni per il prossimo periodo

        Procedi con la valutazione e l'aggiornamento del piano.
        """
        
        # Invia il prompt all'agente
        response = self.chat_handler(evaluation_prompt)
        
        # Aggiungi un messaggio di notifica
        notification = "🔄 Il piano alimentare è stato aggiornato in base ai tuoi progressi. Controlla la chat per i dettagli."
        st.session_state.messages.append({"role": "assistant", "content": notification})
        self.user_data_manager.save_chat_message(
            st.session_state.user_info["id"],
            "assistant",
            notification
        )
        
        # Aggiungi la valutazione completa
        st.session_state.messages.append({"role": "assistant", "content": response})
        self.user_data_manager.save_chat_message(
            st.session_state.user_info["id"],
            "assistant",
            response
        )
        
        # Salva la domanda e risposta dell'agente
        self.user_data_manager.save_agent_qa(
            st.session_state.user_info["id"],
            evaluation_prompt,
            response
        )
        
        # Mostra un messaggio di successo con avviso dell'aggiornamento
        st.success("Progressi salvati con successo! Il piano alimentare è stato aggiornato in base ai tuoi progressi.") 