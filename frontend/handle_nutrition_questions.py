"""
Modulo per la gestione dell'interfaccia delle domande nutrizionali.

Gestisce la visualizzazione e l'interazione con le domande del questionario nutrizionale,
inclusi follow-up dinamici, sport multipli e input temporali.
"""

import streamlit as st
from datetime import datetime
from .nutrition_questions import NUTRITION_QUESTIONS
from .sports_frontend import load_sports_data, get_sports_by_category, on_sport_category_change
from services.state_service import app_state


class NutritionQuestionHandler:
    """Gestisce l'interfaccia delle domande nutrizionali"""
    
    def __init__(self, user_data_manager):
        """
        Inizializza il gestore delle domande nutrizionali.
        
        Args:
            user_data_manager: Gestore dei dati utente
        """
        self.user_data_manager = user_data_manager
    
    def should_show_question(self, question, user_info):
        """
        Verifica se una domanda deve essere mostrata in base alle condizioni.
        
        Args:
            question: Oggetto domanda
            user_info: Informazioni dell'utente
            
        Returns:
            bool: True se la domanda deve essere mostrata
        """
        if "show_if" in question:
            return question["show_if"](user_info)
        return True
    
    def handle_radio_question(self, question):
        """
        Gestisce le domande di tipo radio con eventuali follow-up.
        
        Args:
            question: Oggetto domanda
            
        Returns:
            tuple: (answer, follow_up_answer) se completata, (None, None) altrimenti
        """
        # Mostra la domanda principale
        st.markdown(f"<h3>{question['question']}</h3>", unsafe_allow_html=True)
        answer = st.radio("", question["options"], label_visibility="collapsed")
        
        # Gestisce eventuali follow-up
        follow_up_answer = None
        if "follow_up" in question and answer == question["show_follow_up_on"]:
            follow_up_answer = self._handle_follow_up(question, answer)
        
        if st.button("Avanti"):
            return answer, follow_up_answer
        
        return None, None
    
    def handle_number_input_question(self, question, user_info):
        """
        Gestisce le domande con campi numerici multipli.
        
        Args:
            question: Oggetto domanda
            user_info: Informazioni dell'utente
            
        Returns:
            dict: Valori dei campi se completata, None altrimenti
        """
        question_text = question["question"](user_info) if callable(question["question"]) else question["question"]
        st.markdown(f"<h3>{question_text}</h3>", unsafe_allow_html=True)
        
        field_values = {}
        for field in question["fields"]:
            label = field["label"](user_info) if callable(field["label"]) else field["label"]
            st.markdown(f"<h4>{label}</h4>", unsafe_allow_html=True)
            field_values[field["id"]] = st.number_input(
                "",
                min_value=field["min"],
                max_value=field["max"],
                value=field["default"],
                label_visibility="collapsed"
            )
        
        if st.button("Avanti"):
            return field_values
        
        return None
    
    def _handle_follow_up(self, question, main_answer):
        """
        Gestisce i follow-up delle domande.
        
        Args:
            question: Oggetto domanda
            main_answer: Risposta principale
            
        Returns:
            Risposta del follow-up
        """
        if isinstance(question["follow_up"], str):
            # Gestione vecchio formato stringa
            st.markdown(f"<h4>{question['follow_up']}</h4>", unsafe_allow_html=True)
            return st.text_input("", label_visibility="collapsed")
        
        elif isinstance(question["follow_up"], dict):
            if question["follow_up"].get("type") == "multiple_sports":
                return self._handle_multiple_sports(question)
            else:
                return self._handle_structured_follow_up(question)
        
        return None
    
    def _handle_multiple_sports(self, question):
        """
        Gestisce il follow-up per sport multipli.
        
        Args:
            question: Oggetto domanda
            
        Returns:
            list: Lista dei dati sport
        """
        # Gestione sport multipli
        sports_list = app_state.get_sports_list()
        if not sports_list:
            sports_list = [{}]
            app_state.set_sports_list(sports_list)
        
        follow_up_answer = []
        
        for i, sport in enumerate(sports_list):
            st.markdown(f"### Sport {i+1}")
            sport_data = {}
            
            # Precarica i dati degli sport
            if not app_state.get_sports_data() or not app_state.get_sports_by_category():
                sports_data, sports_by_category = load_sports_data()
                app_state.set_sports_data(sports_data, sports_by_category)
            
            for field in question["follow_up"]["fields"]:
                show_field = True
                if "show_if" in field and "show_if_value" in field:
                    ref_value = sport.get(field["show_if"])
                    show_field = ref_value == field["show_if_value"]
                
                if show_field:
                    st.markdown(f"### {field['label']}")
                    sport_data = self._handle_sport_field(field, sport_data, sport, i)
            
            # Aggiorna lo sport con i dati attuali
            for key, value in sport_data.items():
                sport[key] = value
            
            follow_up_answer.append(sport_data)
        
        # Bottoni per aggiungere/rimuovere sport
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aggiungi altro sport"):
                sports_list.append({})
                app_state.set_sports_list(sports_list)
                st.rerun()
        with col2:
            if len(sports_list) > 1 and st.button("Rimuovi ultimo sport"):
                sports_list.pop()
                app_state.set_sports_list(sports_list)
                st.rerun()
        
        return follow_up_answer
    
    def _handle_sport_field(self, field, sport_data, sport, index):
        """
        Gestisce un singolo campo sport.
        
        Args:
            field: Definizione del campo
            sport_data: Dati dello sport correnti
            sport: Oggetto sport
            index: Indice dello sport
            
        Returns:
            dict: Dati sport aggiornati
        """
        if field["type"] == "select":
            if field["id"] == "sport_type":
                # Quando cambia la categoria, usa il callback
                sport_data[field["id"]] = st.selectbox(
                    "Seleziona",
                    options=field["options"],
                    key=f"{field['id']}_{index}",
                    label_visibility="collapsed",
                    on_change=on_sport_category_change,
                    args=(index,)
                )
            elif field["id"] == "specific_sport" and "dynamic_options" in field and field["dynamic_options"]:
                sport_data = self._handle_dynamic_sport_selection(field, sport_data, sport, index)
            elif field["id"] == "intensity":
                sport_data = self._handle_intensity_selection(field, sport_data, index)
            else:
                sport_data[field["id"]] = st.selectbox(
                    "Seleziona",
                    options=field["options"],
                    key=f"{field['id']}_{index}",
                    label_visibility="collapsed"
                )
        elif field["type"] == "number":
            sport_data[field["id"]] = st.number_input(
                "Numero",
                min_value=field["min"],
                max_value=field["max"],
                value=field["default"],
                key=f"{field['id']}_{index}",
                label_visibility="collapsed"
            )
        elif field["type"] == "text":
            sport_data[field["id"]] = st.text_input(
                "Testo",
                "",
                key=f"{field['id']}_{index}",
                label_visibility="collapsed"
            )
        
        return sport_data
    
    def _handle_dynamic_sport_selection(self, field, sport_data, sport, index):
        """
        Gestisce la selezione dinamica degli sport in base alla categoria.
        
        Args:
            field: Definizione del campo
            sport_data: Dati dello sport correnti
            sport: Oggetto sport
            index: Indice dello sport
            
        Returns:
            dict: Dati sport aggiornati
        """
        # Seleziona gli sport in base alla categoria scelta
        selected_category = sport.get("sport_type", "")
        if not selected_category and f"sport_type_{index}" in st.session_state:
            selected_category = st.session_state[f"sport_type_{index}"]
        
        # Usa i dati degli sport dall'app_state
        sports_by_category = app_state.get_sports_by_category()
        if sports_by_category and selected_category in sports_by_category:
            sports_options = sports_by_category[selected_category]
        else:
            sports_options = []
        sport_names = [s["name"] for s in sports_options]
        
        # Se non ci sono sport disponibili, mostra un messaggio
        if not sport_names:
            st.warning("Nessuno sport disponibile per questa categoria. Seleziona prima una categoria.")
            sport_data[field["id"]] = None
        else:
            # Crea un dizionario di riferimento sport_name -> sport_data
            sport_data_map = {s["name"]: s for s in sports_options}
            
            selected_sport_name = st.selectbox(
                "Seleziona",
                options=sport_names,
                key=f"{field['id']}_{index}",
                label_visibility="collapsed"
            )
            
            # Memorizza sia il nome che la chiave dello sport
            if selected_sport_name:
                sport_data[field["id"]] = {
                    "name": selected_sport_name,
                    "key": sport_data_map[selected_sport_name]["key"],
                    "kcal_per_hour": sport_data_map[selected_sport_name]["kcal_per_hour"],
                    "description": sport_data_map[selected_sport_name]["description"]
                }
            else:
                sport_data[field["id"]] = None
        
        return sport_data
    
    def _handle_intensity_selection(self, field, sport_data, index):
        """
        Gestisce la selezione dell'intensità con descrizioni.
        
        Args:
            field: Definizione del campo
            sport_data: Dati dello sport correnti
            index: Indice dello sport
            
        Returns:
            dict: Dati sport aggiornati
        """
        # Mostra le descrizioni per l'intensità
        intensity_options = field["options"]
        intensity_descriptions = field.get("descriptions", {})
        
        # Crea opzioni formattate con descrizioni
        formatted_options = [f"{opt} - {intensity_descriptions.get(opt, '')}" 
                            for opt in intensity_options]
        
        # Mostra il selectbox con le descrizioni
        formatted_selection = st.selectbox(
            "Seleziona",
            options=formatted_options,
            key=f"{field['id']}_{index}",
            label_visibility="collapsed"
        )
        
        # Estrai solo il valore dell'intensità (prima del trattino)
        selected_intensity = formatted_selection.split(' - ')[0] if formatted_selection else None
        sport_data[field["id"]] = selected_intensity
        
        return sport_data
    
    def _handle_structured_follow_up(self, question):
        """
        Gestisce follow-up strutturati (non sport).
        
        Args:
            question: Oggetto domanda
            
        Returns:
            dict: Risposte del follow-up
        """
        follow_up_answer = {}
        for field in question["follow_up"]["fields"]:
            show_field = True
            if "show_if" in field and "show_if_value" in field:
                ref_value = follow_up_answer.get(field["show_if"])
                show_field = ref_value == field["show_if_value"]
            
            if show_field:
                st.markdown(f"### {field['label']}")
                if field["type"] == "select":
                    follow_up_answer[field["id"]] = st.selectbox(
                        "",
                        options=field["options"]
                    )
                elif field["type"] == "number":
                    follow_up_answer[field["id"]] = st.number_input(
                        "",
                        min_value=field["min"],
                        max_value=field["max"],
                        value=field["default"]
                    )
                elif field["type"] == "text":
                    follow_up_answer[field["id"]] = st.text_input("")
                elif field["type"] == "dynamic_time":
                    follow_up_answer[field["id"]] = self._handle_dynamic_time_input(follow_up_answer, question, field)
        
        return follow_up_answer
    
    def _handle_dynamic_time_input(self, follow_up_answer, question, field):
        """
        Gestisce l'input dinamico dei tempi dei pasti.
        
        Args:
            follow_up_answer: Risposte correnti del follow-up
            question: Oggetto domanda
            field: Definizione del campo
            
        Returns:
            dict: Orari dei pasti
        """
        # Get the number of meals from the previous field
        num_meals = follow_up_answer.get("num_meals", 3)
        meal_times = {}
        
        # Define meal order and labels based on number of meals
        meal_order = {
            1: ["Pranzo"],
            2: ["Pranzo", "Cena"],
            3: ["Colazione", "Pranzo", "Cena"],
            4: ["Colazione", "Pranzo", "Spuntino pomeridiano", "Cena"],
            5: ["Colazione", "Spuntino mattutino", "Pranzo", "Spuntino pomeridiano", "Cena"]
        }
        
        # Get the appropriate meal labels for the selected number of meals
        meal_labels = meal_order.get(num_meals, [])
        
        # Create time input for each meal
        for i, label in enumerate(meal_labels):
            st.markdown(f"### {label}")
            # Set default times based on meal type
            default_times = {
                "Colazione": "07:30",
                "Spuntino mattutino": "10:30",
                "Pranzo": "13:00",
                "Spuntino pomeridiano": "16:30",
                "Cena": "20:00"
            }
            
            # Convert default time string to datetime.time object
            default_time = datetime.strptime(default_times[label], "%H:%M").time()
            
            time_value = st.time_input(
                "",
                value=default_time,
                key=f"meal_time_{question['id']}_{label}_{i}",
                label_visibility="collapsed"
            )
            meal_times[label] = time_value
        
        return {
            label: time_val.strftime("%H:%M") if time_val else None 
            for label, time_val in meal_times.items()
        }
    
    def save_answer(self, question_id, answer, follow_up_answer, user_id, user_info):
        """
        Salva la risposta della domanda.
        
        Args:
            question_id: ID della domanda
            answer: Risposta principale
            follow_up_answer: Risposta del follow-up
            user_id: ID dell'utente
            user_info: Informazioni dell'utente
        """
        # Salva la risposta
        nutrition_answers = app_state.get_nutrition_answers()
        nutrition_answers[question_id] = {
            "answer": answer,
            "follow_up": follow_up_answer
        }
        
        # Sincronizza con entrambi i sistemi
        st.session_state.nutrition_answers = nutrition_answers
        app_state.set_nutrition_answers(nutrition_answers)
        
        # Salva le risposte nutrizionali
        self.user_data_manager.save_nutritional_info(
            user_id,
            {
                **{k: v for k, v in user_info.items() if k not in ["id", "username"]},
                "nutrition_answers": nutrition_answers
            }
        )
        
        current_question = app_state.get_current_question() + 1
        st.session_state.current_question = current_question
        app_state.set_current_question(current_question)
    
    def handle_current_question(self, user_info, user_id):
        """
        Gestisce la domanda corrente.
        
        Args:
            user_info: Informazioni dell'utente
            user_id: ID dell'utente
            
        Returns:
            bool: True se ci sono ancora domande da processare
        """
        current_question = app_state.get_current_question()
        if current_question >= len(NUTRITION_QUESTIONS):
            return False
        
        current_q = NUTRITION_QUESTIONS[current_question]
        # Sincronizza anche st.session_state per compatibilità
        st.session_state.current_question = current_question
        
        # Verifica se la domanda deve essere mostrata
        if not self.should_show_question(current_q, user_info):
            # Salta la domanda se non deve essere mostrata
            current_question += 1
            st.session_state.current_question = current_question
            app_state.set_current_question(current_question)
            st.rerun()
            return True
        
        # Gestisce la domanda in base al tipo
        if current_q["type"] == "radio":
            answer, follow_up_answer = self.handle_radio_question(current_q)
            if answer is not None:
                self.save_answer(current_q["id"], answer, follow_up_answer, user_id, user_info)
                st.rerun()
        
        elif current_q["type"] == "number_input":
            field_values = self.handle_number_input_question(current_q, user_info)
            if field_values is not None:
                self.save_answer(current_q["id"], field_values, None, user_id, user_info)
                st.rerun()
        
        return True


def handle_nutrition_questions(user_info, user_id, user_data_manager):
    """
    Funzione principale per gestire le domande nutrizionali.
    
    Args:
        user_info: Informazioni dell'utente
        user_id: ID dell'utente  
        user_data_manager: Gestore dei dati utente
        
    Returns:
        bool: True se ci sono ancora domande, False se completate
    """
    st.title("NutrAICoach")
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    handler = NutritionQuestionHandler(user_data_manager)
    return handler.handle_current_question(user_info, user_id) 