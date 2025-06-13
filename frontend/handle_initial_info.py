"""
Modulo per la gestione delle informazioni iniziali dell'utente.

Gestisce il form di inserimento dei dati personali base (età, sesso, peso, altezza, ecc.)
e la visualizzazione delle informazioni già inserite.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.tutorial import is_tutorial_completed


class InitialInfoHandler:
    """Gestisce il form delle informazioni iniziali dell'utente"""
    
    def __init__(self, user_data_manager, create_new_thread_func):
        """
        Inizializza il gestore delle informazioni iniziali.
        
        Args:
            user_data_manager: Gestore dei dati utente
            create_new_thread_func: Funzione per creare un nuovo thread
        """
        self.user_data_manager = user_data_manager
        self.create_new_thread_func = create_new_thread_func
    
    def handle_user_info_form(self, user_id):
        """
        Gestisce il form per l'inserimento delle informazioni utente.
        
        Args:
            user_id: ID dell'utente
        """
        # Carica le informazioni nutrizionali salvate
        nutritional_info = self.user_data_manager.get_nutritional_info(user_id)
        # Carica le preferenze utente
        user_preferences = self.user_data_manager.get_user_preferences(user_id)
        
        with st.form("user_info_form"):
            st.write("Per iniziare, inserisci i tuoi dati:")
            
            # Campi del form con valori di default
            età = st.number_input(
                "Età", 
                18, 100, 
                nutritional_info.età if nutritional_info else 24
            )
            
            sesso = st.selectbox(
                "Sesso", 
                ["Maschio", "Femmina"], 
                index=0 if not nutritional_info else (0 if nutritional_info.sesso == "Maschio" else 1)
            )
            
            peso = st.number_input(
                "Peso (kg)", 
                min_value=40, 
                max_value=200, 
                value=nutritional_info.peso if nutritional_info else 74, 
                step=1
            )
            
            altezza = st.number_input(
                "Altezza (cm)", 
                140, 220, 
                nutritional_info.altezza if nutritional_info else 180
            )
            
            attività = st.selectbox(
                "Livello di attività fisica (a parte sport praticato)",
                ["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"],
                index=self._get_activity_index(nutritional_info)
            )
            
            obiettivo = st.selectbox(
                "Obiettivo",
                ["Perdita di peso", "Mantenimento", "Aumento di peso"],
                index=self._get_objective_index(nutritional_info)
            )
            
            # Controlla se il tutorial è completato
            tutorial_completed = is_tutorial_completed(user_id)
            
            # Disabilita il pulsante se il tutorial non è completato
            if not tutorial_completed:
                st.warning("⚠️ Completa il tutorial visitando tutte le sezioni (Chat, Preferenze, Piano Nutrizionale) prima di iniziare!")
            
            button_disabled = not tutorial_completed
            button_label = "Inizia" if tutorial_completed else "Inizia (Completa prima il tutorial)"
            
            if st.form_submit_button(button_label, disabled=button_disabled):
                self._save_user_info(
                    user_id, età, sesso, peso, altezza, attività, obiettivo, 
                    user_preferences, nutritional_info
                )
                st.rerun()
    
    def display_user_info(self, user_info):
        """
        Mostra le informazioni dell'utente già inserite.
        
        Args:
            user_info: Dizionario con le informazioni dell'utente
        """
        st.write("Dati inseriti:")
        for key, value in user_info.items():
            if key == "peso":
                st.write(f"Peso: {int(value)} kg")
            elif key not in ["id", "username", "preferences"]:
                st.write(f"{key.capitalize()}: {value}")
    
    def _get_activity_index(self, nutritional_info):
        """
        Ottiene l'indice del livello di attività per il selectbox.
        
        Args:
            nutritional_info: Informazioni nutrizionali salvate
            
        Returns:
            int: Indice dell'attività nel selectbox
        """
        activities = ["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"]
        if nutritional_info and nutritional_info.attività in activities:
            return activities.index(nutritional_info.attività)
        return 0
    
    def _get_objective_index(self, nutritional_info):
        """
        Ottiene l'indice dell'obiettivo per il selectbox.
        
        Args:
            nutritional_info: Informazioni nutrizionali salvate
            
        Returns:
            int: Indice dell'obiettivo nel selectbox
        """
        objectives = ["Perdita di peso", "Mantenimento", "Aumento di peso"]
        if nutritional_info and nutritional_info.obiettivo in objectives:
            return objectives.index(nutritional_info.obiettivo)
        return 0
    
    def _save_user_info(self, user_id, età, sesso, peso, altezza, attività, obiettivo, user_preferences, nutritional_info):
        """
        Salva le informazioni dell'utente.
        
        Args:
            user_id: ID dell'utente
            età: Età dell'utente
            sesso: Sesso dell'utente
            peso: Peso dell'utente
            altezza: Altezza dell'utente
            attività: Livello di attività dell'utente
            obiettivo: Obiettivo dell'utente
            user_preferences: Preferenze dell'utente
            nutritional_info: Informazioni nutrizionali esistenti
        """
        # Aggiorna le informazioni dell'utente
        user_info = {
            "età": età,
            "sesso": sesso,
            "peso": peso,
            "altezza": altezza,
            "attività": attività,
            "obiettivo": obiettivo,
            "preferences": user_preferences
        }
        st.session_state.user_info.update(user_info)
        
        # Salva le informazioni nutrizionali
        self.user_data_manager.save_nutritional_info(user_id, user_info)
        
        # Se ci sono risposte nutrizionali salvate, caricale
        if nutritional_info and nutritional_info.nutrition_answers:
            st.session_state.nutrition_answers = nutritional_info.nutrition_answers
            st.session_state.current_question = len(NUTRITION_QUESTIONS)
        
        # Crea un nuovo thread quando si inizia una nuova consulenza
        self.create_new_thread_func()


def handle_user_info_display(user_info):
    """
    Funzione di convenienza per mostrare le informazioni utente.
    
    Args:
        user_info: Informazioni dell'utente da visualizzare
    """
    handler = InitialInfoHandler(None, None)
    handler.display_user_info(user_info)


def handle_user_info_form(user_id, user_data_manager, create_new_thread_func):
    """
    Funzione di convenienza per gestire il form delle informazioni utente.
    
    Args:
        user_id: ID dell'utente
        user_data_manager: Gestore dei dati utente
        create_new_thread_func: Funzione per creare un nuovo thread
    """
    handler = InitialInfoHandler(user_data_manager, create_new_thread_func)
    handler.handle_user_info_form(user_id) 