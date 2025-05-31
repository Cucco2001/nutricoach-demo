"""
Modulo per la visualizzazione dei progressi dell'utente.

Gestisce la visualizzazione della cronologia progressi, inclusi grafici,
tabelle e funzionalità di eliminazione dati.
"""

import streamlit as st
import pandas as pd


class ProgressDisplay:
    """Gestisce la visualizzazione dei progressi dell'utente"""
    
    def __init__(self, user_data_manager):
        """
        Inizializza il display dei progressi.
        
        Args:
            user_data_manager: Gestore dei dati utente
        """
        self.user_data_manager = user_data_manager
    
    def show_progress_history(self):
        """Mostra la storia dei progressi dell'utente"""
        if "user_info" in st.session_state and "id" in st.session_state.user_info:
            history = self.user_data_manager.get_progress_history(
                st.session_state.user_info["id"]
            )
            
            if history:
                self._display_progress_data(history)
            else:
                st.info("Nessun dato di progresso disponibile")
    
    def _display_progress_data(self, history):
        """
        Visualizza i dati di progresso.
        
        Args:
            history: Lista degli entry di progresso
        """
        # Prepara il DataFrame
        progress_df = pd.DataFrame([
            {
                "Data": entry.date,
                "Peso": entry.weight,
                **entry.measurements
            }
            for entry in history
        ])
        
        # Formatta i numeri con una cifra decimale
        numeric_columns = progress_df.select_dtypes(include=['float64']).columns
        progress_df[numeric_columns] = progress_df[numeric_columns].round(1)
        
        # Mostra il grafico del peso
        st.line_chart(progress_df.set_index("Data")["Peso"])
        
        # Mostra il dettaglio delle misurazioni
        self._show_measurements_detail(progress_df)
    
    def _show_measurements_detail(self, progress_df):
        """
        Mostra il dettaglio delle misurazioni con opzioni di visualizzazione.
        
        Args:
            progress_df: DataFrame con i dati di progresso
        """
        with st.expander("Dettaglio misurazioni"):
            # Aggiungi selettore per il tipo di visualizzazione
            view_type = st.radio(
                "Formato visualizzazione:",
                ["Tabella", "Dettagliato"],
                horizontal=True,
                key="view_type"
            )
            
            if view_type == "Tabella":
                self._show_table_view(progress_df)
            else:
                self._show_detailed_view(progress_df)
    
    def _show_table_view(self, progress_df):
        """
        Mostra la visualizzazione tabellare con pulsanti di eliminazione.
        
        Args:
            progress_df: DataFrame con i dati di progresso
        """
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.dataframe(progress_df, hide_index=True)
        with col2:
            # Aggiungi pulsanti di eliminazione allineati con la tabella
            for idx in range(len(progress_df)):
                if st.button("🗑️", key=f"delete_table_{idx}", help=f"Elimina voce del {progress_df.iloc[idx]['Data']}"):
                    self._delete_progress_entry(progress_df.iloc[idx]['Data'])
    
    def _show_detailed_view(self, progress_df):
        """
        Mostra la visualizzazione dettagliata con pulsanti di eliminazione.
        
        Args:
            progress_df: DataFrame con i dati di progresso
        """
        for idx, (index, row) in enumerate(progress_df.iterrows()):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                # Mostra i dati della riga
                st.write(f"Data: {row['Data']}")
                st.write(f"Peso: {row['Peso']} kg")
                measurements = {k: v for k, v in row.items() if k not in ['Data', 'Peso']}
                if measurements:
                    st.write("Misurazioni:")
                    for k, v in measurements.items():
                        st.write(f"- {k}: {v} cm")
            with col2:
                # Aggiungi il pulsante di eliminazione con chiave univoca
                if st.button("🗑️", key=f"delete_detailed_{row['Data']}_{idx}", help=f"Elimina voce del {row['Data']}"):
                    self._delete_progress_entry(row['Data'])
            st.divider()  # Aggiunge una linea di separazione tra le voci
    
    def _delete_progress_entry(self, date):
        """
        Elimina una voce di progresso.
        
        Args:
            date: Data della voce da eliminare
        """
        if self.user_data_manager.delete_progress_entry(
            st.session_state.user_info["id"],
            date
        ):
            st.success(f"Voce del {date} eliminata con successo!")
            st.rerun()
        else:
            st.error("Errore durante l'eliminazione della voce.") 