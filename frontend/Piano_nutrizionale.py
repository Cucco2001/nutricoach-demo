"""
Modulo per la gestione e visualizzazione del piano nutrizionale.

Questo modulo gestisce la visualizzazione dei dati nutrizionali estratti
automaticamente dal sistema DeepSeek durante le conversazioni con l'agente.
"""

import streamlit as st
import os
import json
import pandas as pd
import threading
import time
from datetime import datetime

# Import del servizio PDF
from services.pdf_service import PDFGenerator


class PianoNutrizionale:
    """Gestisce la visualizzazione del piano nutrizionale e dei dati estratti"""
    
    def __init__(self):
        """Inizializza il gestore del piano nutrizionale"""
        self.pdf_generator = PDFGenerator()
    
    def _setup_css_styles(self):
        """Configura gli stili CSS personalizzati per l'interfaccia"""
        pass  # Rimosso il CSS custom precedente
    
    def _is_deepseek_processing(self, user_id: str) -> bool:
        """
        Controlla se DeepSeek sta attualmente elaborando dati per l'utente.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            bool: True se DeepSeek sta elaborando, False altrimenti
        """
        try:
            # Metodo 1: Controlla se esiste un thread di estrazione attivo per questo utente
            for thread in threading.enumerate():
                if thread.name == f"DeepSeekExtraction-{user_id}" and thread.is_alive():
                    return True
            
            # Metodo 2: Controlla il session state per indicatori di elaborazione recente
            if hasattr(st.session_state, 'deepseek_manager'):
                # Controlla se c'è stata un'estrazione recente (negli ultimi 30 secondi)
                last_extraction_time = st.session_state.get(f"last_extraction_start_{user_id}", 0)
                current_time = time.time()
                if current_time - last_extraction_time < 30:  # 30 secondi di grazia
                    return True
            
            return False
        except Exception as e:
            print(f"[PIANO_NUTRIZIONALE] Errore nel controllo thread DeepSeek: {str(e)}")
            return False
    
    def _display_deepseek_loading_indicator(self):
        """Mostra l'indicatore di caricamento per l'elaborazione DeepSeek."""
        st.markdown("""
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <strong>🤖 Stiamo estraendo i tuoi dati nutrizionali dalla conversazione...</strong>
            <br>
            <small>Il piano nutrizionale e il PDF verranno aggiornati automaticamente al termine dell'elaborazione.</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostra informazioni aggiuntive se disponibili
        if hasattr(st.session_state, 'deepseek_manager'):
            status = st.session_state.deepseek_manager.get_extraction_status()
            if status.get('available', False):
                interactions_since_last = status.get('interactions_since_last', 0)
                st.caption(f"📊 Interazioni dall'ultima estrazione: {interactions_since_last}")

    def display_nutritional_plan(self, user_id):
        """
        Mostra il piano nutrizionale e i dati estratti per l'utente.
        
        Args:
            user_id: ID dell'utente di cui mostrare i dati
        """
        st.markdown("""
            <div class="welcome-header">
                <h1>Il Tuo Piano <span class="gradient-text">Nutrizionale</span></h1>
                <p class="section-subtitle">Qui trovi il riepilogo del tuo piano personalizzato, generato dall'AI.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Controlla se DeepSeek sta elaborando
        is_processing = self._is_deepseek_processing(user_id)
        
        if is_processing:
            self._display_deepseek_loading_indicator()
            # Auto-refresh ogni 5 secondi solo se è la prima volta che vediamo il processing
            if not st.session_state.get(f"deepseek_processing_shown_{user_id}", False):
                st.session_state[f"deepseek_processing_shown_{user_id}"] = True
                time.sleep(2)
                st.rerun()
        else:
            # Reset del flag quando il processing è finito
            if f"deepseek_processing_shown_{user_id}" in st.session_state:
                del st.session_state[f"deepseek_processing_shown_{user_id}"]
        
        try:
            extracted_data = self._load_user_nutritional_data(user_id)
            
            if not extracted_data:
                if not is_processing:
                    st.info("🤖 Nessun dato nutrizionale disponibile ancora. Continua la conversazione con l'agente per raccogliere dati.")
                return
            
            # Header con pulsante download
            self._display_header_with_download(extracted_data, user_id)
            st.divider()
            
            # Sezioni principali del piano nutrizionale in un layout a due colonne
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                self._display_caloric_needs_section(extracted_data)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                self._display_macros_section(extracted_data)
                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()
            
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            self._display_daily_plan_section(extracted_data)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            self._display_registered_meals_section(extracted_data)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Errore nel caricamento dei dati: {str(e)}")
    
    def _display_header_with_download(self, extracted_data, user_id):
        """
        Mostra l'header con informazioni e pulsante di download PDF.
        
        Args:
            extracted_data: Dati nutrizionali estratti
            user_id: ID dell'utente
        """
        last_updated = extracted_data.get("last_updated", "Sconosciuto")
        
        # Layout a due colonne per header + bottone download
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if last_updated != "Sconosciuto":
                try:
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d/%m/%Y alle %H:%M")
                    st.caption(f"📅 Ultimo aggiornamento dati: {formatted_date}")
                except:
                    st.caption(f"📅 Ultimo aggiornamento dati: {last_updated}")
        
        with col2:
            # Controlla se DeepSeek sta elaborando per disabilitare il PDF
            is_processing = self._is_deepseek_processing(user_id)
            
            if is_processing:
                st.button("⏳ PDF in aggiornamento...", disabled=True, use_container_width=True)
            else:
                # Genera PDF e crea download button diretto
                try:
                    # Ottieni le informazioni dell'utente da session_state
                    user_info = st.session_state.get('user_info', {}).copy()
                    
                    # Aggiungi nutrition_answers se disponibile
                    nutrition_answers = st.session_state.get('nutrition_answers', {})
                    if nutrition_answers:
                        user_info['nutrition_answers'] = nutrition_answers
                    
                    # Genera il PDF usando il servizio
                    pdf_bytes = self.pdf_generator.generate_nutritional_plan_pdf(user_id, user_info)
                    
                    # Crea nome file con timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    username = user_info.get('username', 'utente')
                    filename = f"piano_nutrizionale_{username}_{timestamp}.pdf"
                    
                    # Download diretto del PDF
                    st.download_button(
                        label="📄 Scarica PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    # Se c'è un errore nella generazione, mostra un pulsante disabilitato
                    st.button("❌ Errore PDF", disabled=True, use_container_width=True)
                    print(f"[PDF_ERROR] {str(e)}")

    def _handle_pdf_download(self, user_id):
        """
        DEPRECATA: Funzione non più utilizzata.
        Il download è ora gestito direttamente in _display_header_with_download.
        """
        pass

    def _load_user_nutritional_data(self, user_id):
        """
        Carica i dati nutrizionali dell'utente dal file JSON.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            dict: Dati nutrizionali estratti o None se non trovati
        """
        # Gestisci diversi formati di user_id
        possible_paths = [
            f"user_data/{user_id}.json",
            f"user_data/user_{user_id}.json"
        ]
        
        user_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                user_file_path = path
                break
        
        if not user_file_path:
            st.warning(f"📝 File utente non trovato per ID: {user_id}")
            st.info("💡 Possibili percorsi cercati:")
            for path in possible_paths:
                st.info(f"   • {path}")
            return None
            
        try:
            with open(user_file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            extracted_data = user_data.get("nutritional_info_extracted", {})
            
            # Verifica che ci siano effettivamente dati utili
            if not extracted_data:
                return None
                
            return extracted_data
            
        except json.JSONDecodeError as e:
            st.error(f"❌ Errore nel parsing del file JSON: {str(e)}")
            return None
        except Exception as e:
            st.error(f"❌ Errore nel caricamento del file: {str(e)}")
            return None
    
    def _display_caloric_needs_section(self, extracted_data):
        """
        Mostra la sezione del fabbisogno energetico.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "caloric_needs" not in extracted_data:
            return
            
        st.markdown("<h3>🔥 Fabbisogno Energetico</h3>", unsafe_allow_html=True)

        caloric_data = extracted_data["caloric_needs"]
        
        # Metrics principali
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Metabolismo Basale (BMR)", value=f"{caloric_data.get('bmr', 0)} kcal")
            st.metric(label="Dispendio Sportivo", value=f"{caloric_data.get('dispendio_sportivo', 0)} kcal")
        with col2:
            st.metric(label="Fabbisogno Base (con LAF)", value=f"{caloric_data.get('fabbisogno_base', 0)} kcal")
            st.metric(label="Obiettivo Finale", value=f"{caloric_data.get('fabbisogno_finale', 0)} kcal", delta=f"{caloric_data.get('aggiustamento_obiettivo', 0)} kcal")
        
        self._display_caloric_additional_info(caloric_data)
    
    def _display_caloric_additional_info(self, caloric_data):
        """
        Mostra informazioni aggiuntive sui calcoli calorici.
        
        Args:
            caloric_data: Dati del fabbisogno calorico
        """
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            laf = caloric_data.get('laf_utilizzato', 'N/A')
            st.write(f"**📈 Fattore Attività (LAF):** {laf}")
        with col2:
            aggiustamento = caloric_data.get('aggiustamento_obiettivo', 0)
            if aggiustamento != 0:
                simbolo = "+" if aggiustamento > 0 else ""
                st.write(f"**🎯 Aggiustamento Obiettivo:** {simbolo}{aggiustamento} kcal")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _display_macros_section(self, extracted_data):
        """
        Mostra la sezione dei macronutrienti.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "macros_total" not in extracted_data:
            return
            
        st.markdown("<h3>🥗 Distribuzione Macronutrienti</h3>", unsafe_allow_html=True)

        macros_data = extracted_data["macros_total"]
        
        # Crea DataFrame per il grafico
        macro_df = pd.DataFrame({
            'Macronutriente': ['Proteine', 'Carboidrati', 'Grassi'],
            'Grammi': [
                macros_data.get('proteine_g', 0),
                macros_data.get('carboidrati_g', 0),
                macros_data.get('grassi_g', 0)
            ],
            'Kcal': [
                macros_data.get('proteine_kcal', 0),
                macros_data.get('carboidrati_kcal', 0),
                macros_data.get('grassi_kcal', 0)
            ],
            'Percentuale': [
                macros_data.get('proteine_percentuale', 0),
                macros_data.get('carboidrati_percentuale', 0),
                macros_data.get('grassi_percentuale', 0)
            ]
        })
        
        self._display_macros_chart_and_cards(macro_df, macros_data)
    
    def _display_macros_chart_and_cards(self, macro_df, macros_data):
        """
        Mostra grafico e cards dei macronutrienti.
        
        Args:
            macro_df: DataFrame con i dati dei macronutrienti
            macros_data: Dati raw dei macronutrienti
        """
        # Layout a 2 colonne
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Grafico a barre colorato
            st.bar_chart(macro_df.set_index('Macronutriente')['Kcal'])
            
        with col2:
            # Cards dei macronutrienti
            st.metric(label="🥩 Proteine", value=f"{macro_df.iloc[0]['Grammi']}g", delta=f"{macro_df.iloc[0]['Percentuale']}%")
            st.metric(label="🍞 Carboidrati", value=f"{macro_df.iloc[1]['Grammi']}g", delta=f"{macro_df.iloc[1]['Percentuale']}%")
            st.metric(label="🥑 Grassi", value=f"{macro_df.iloc[2]['Grammi']}g", delta=f"{macro_df.iloc[2]['Percentuale']}%")
        
        # Fibre e calorie totali
        self._display_macros_totals(macros_data)
    
    def _display_macros_totals(self, macros_data):
        """
        Mostra totali di fibre e calorie.
        
        Args:
            macros_data: Dati dei macronutrienti
        """
        col1, col2 = st.columns(2)
        
        with col1:
            fibre = macros_data.get('fibre_g', 0)
            if fibre > 0:
                st.markdown(f'''
                <div class="info-card">
                    <strong>🌾 Fibre giornaliere:</strong> {fibre}g
                </div>
                ''', unsafe_allow_html=True)
        
        with col2:
            kcal_totali = macros_data.get('kcal_totali', 0)
            st.markdown(f'''
            <div class="info-card">
                <strong>🔥 Calorie Totali:</strong> {kcal_totali} kcal
            </div>
            ''', unsafe_allow_html=True)
    
    def _display_daily_plan_section(self, extracted_data):
        """
        Mostra la sezione del piano pasti giornaliero.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data or "daily_macros" not in extracted_data:
            return
            
        st.markdown("<h3>🍽️ Piano Pasti Giornaliero</h3>", unsafe_allow_html=True)

        daily_data = extracted_data["daily_macros"]
        
        num_pasti = daily_data.get('numero_pasti', 0)
        st.metric(label="Numero di Pasti Previsti", value=num_pasti)
        
        if "distribuzione_pasti" in daily_data:
            self._display_meal_distribution(daily_data["distribuzione_pasti"])
    
    def _display_meal_distribution(self, distribuzione_pasti):
        """
        Mostra la distribuzione dei pasti.
        
        Args:
            distribuzione_pasti: Dati della distribuzione dei pasti
        """
        for pasto_nome, pasto_data in distribuzione_pasti.items():
            if not pasto_data:
                continue
            
            with st.container():
                st.subheader(pasto_nome.title())
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Kcal", value=pasto_data.get('kcal', 0))
                with col2:
                    st.metric(label="% sul totale", value=f"{pasto_data.get('percentuale_kcal', 0)}%")
                
                # Macros del pasto in cards piccole
                self._display_meal_macros(pasto_data)
    
    def _display_meal_macros(self, pasto_data):
        """
        Mostra i macronutrienti del singolo pasto.
        
        Args:
            pasto_data: Dati del pasto
        """
        if not pasto_data:
            return
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Proteine", value=f"{pasto_data.get('proteine_g', 0)}g")
        with col2:
            st.metric(label="Carboidrati", value=f"{pasto_data.get('carboidrati_g', 0)}g")
        with col3:
            st.metric(label="Grassi", value=f"{pasto_data.get('grassi_g', 0)}g")
    
    def _display_registered_meals_section(self, extracted_data):
        """
        Mostra la sezione dei pasti creati/registrati organizzati per giorno.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        # Verifica che extracted_data non sia None
        if not extracted_data:
            return
            
        # Controlla se ci sono dati da mostrare
        has_day1_data = "registered_meals" in extracted_data and extracted_data["registered_meals"]
        has_weekly_data = "weekly_diet" in extracted_data and extracted_data["weekly_diet"]
        
        if not has_day1_data and not has_weekly_data:
            return
            
        st.markdown("<h3>📅 Piano Settimanale - Ricette e Pasti</h3>", unsafe_allow_html=True)
        
        # Mostra i giorni disponibili
        self._display_weekly_plan_overview(extracted_data)
        
        # Crea il menu a tendina per selezionare il giorno
        self._display_day_selector_and_content(extracted_data, has_day1_data, has_weekly_data)
    
    def _display_weekly_plan_overview(self, extracted_data):
        """
        Mostra una panoramica dei giorni disponibili nel piano settimanale.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if not extracted_data:
            return
            
        has_day1 = "registered_meals" in extracted_data and extracted_data["registered_meals"]
        weekly_diet = extracted_data.get("weekly_diet", {})
        
        available_days = []
        if has_day1:
            available_days.append("Giorno 1")
        
        for day_num in range(2, 8):
            day_key = f"giorno_{day_num}"
            if day_key in weekly_diet and weekly_diet[day_key]:
                available_days.append(f"Giorno {day_num}")
        
        if available_days:
            st.markdown(f"**Giorni con dati:** {' • '.join(available_days)}")
    
    def _display_day_selector_and_content(self, extracted_data, has_day1_data, has_weekly_data):
        """
        Mostra il selettore di giorni e il contenuto del giorno selezionato.
        
        Args:
            extracted_data: Dati nutrizionali estratti
            has_day1_data: True se ci sono dati del giorno 1
            has_weekly_data: True se ci sono dati della settimana
        """
        # Prepara le opzioni del menu a tendina
        day_options = {}
        day_names = {
            1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 
            5: "Venerdì", 6: "Sabato", 7: "Domenica"
        }
        
        # Aggiungi Giorno 1 se disponibile
        if has_day1_data:
            day_options["Giorno 1"] = (1, extracted_data["registered_meals"], True)
        
        # Aggiungi Giorni 2-7 se disponibili
        if has_weekly_data:
            weekly_diet = extracted_data["weekly_diet"]
            for day_num in range(2, 8):
                day_key = f"giorno_{day_num}"
                if day_key in weekly_diet and weekly_diet[day_key]:
                    day_label = f"Giorno {day_num}"
                    day_options[day_label] = (day_num, weekly_diet[day_key], False)
        
        # Se non ci sono giorni disponibili, non mostrare nulla
        if not day_options:
            st.info("📝 Nessun giorno di dieta disponibile")
            return
        
        # Menu a tendina per selezionare il giorno
        st.markdown("### 📅 Seleziona il giorno da visualizzare:")
        
        selected_day_label = st.selectbox(
            "Scegli un giorno:",
            options=list(day_options.keys()),
            format_func=lambda x: f"{day_names.get(int(x.split()[-1]), '')} {x}",
            key="day_selector"
        )
        
        # Mostra il contenuto del giorno selezionato
        if selected_day_label and selected_day_label in day_options:
            day_num, day_data, is_registered_meals = day_options[selected_day_label]
            
            st.markdown("---")  # Separatore
            
            # Mostra i pasti del giorno selezionato
            self._display_day_meals(day_num, day_data, is_registered_meals)
    
    def _display_day_meals(self, day_num, day_data, is_registered_meals=False):
        """
        Mostra i pasti di un singolo giorno.
        
        Args:
            day_num: Numero del giorno (1-7)
            day_data: Dati del giorno (lista per registered_meals, dict per weekly_diet)
            is_registered_meals: True se i dati vengono da registered_meals (giorno 1)
        """
        # Determina il nome del giorno
        day_names = {
            1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 
            5: "Venerdì", 6: "Sabato", 7: "Domenica"
        }
        day_name = day_names.get(day_num, f"Giorno {day_num}")
        
        # Header del giorno
        st.subheader(f"📅 {day_name} (Giorno {day_num})")
        
        if is_registered_meals:
            # Giorno 1: registered_meals (lista di pasti)
            sorted_meals = self._sort_meals_by_time(day_data)
            for i, meal in enumerate(sorted_meals):
                self._display_single_meal(meal, i, len(sorted_meals))
        else:
            # Giorni 2-7: weekly_diet (dict di pasti)
            self._display_weekly_diet_day(day_data)
    
    def _display_weekly_diet_day(self, day_data):
        """
        Mostra i pasti di un giorno dalla weekly_diet.
        
        Args:
            day_data: Dati del giorno dalla sezione weekly_diet
        """
        # Ordine dei pasti
        meal_order = ['colazione', 'spuntino_mattutino', 'pranzo', 'spuntino_pomeridiano', 'cena', 'spuntino_serale']
        
        meals_found = 0
        for meal_name in meal_order:
            if meal_name in day_data and day_data[meal_name]:
                meal_data = day_data[meal_name]
                self._display_weekly_diet_meal(meal_name, meal_data)
                meals_found += 1
        
        # Se non ci sono pasti nell'ordine standard, mostra tutti quelli disponibili
        if meals_found == 0:
            for meal_name, meal_data in day_data.items():
                if meal_data:
                    self._display_weekly_diet_meal(meal_name, meal_data)
    
    def _display_weekly_diet_meal(self, meal_name, meal_data):
        """
        Mostra un singolo pasto dalla weekly_diet.
        
        Args:
            meal_name: Nome del pasto
            meal_data: Dati del pasto dalla weekly_diet
        """
        # Converti il nome del pasto in forma leggibile
        meal_display_names = {
            'colazione': '🌅 Colazione',
            'spuntino_mattutino': '🥤 Spuntino Mattutino', 
            'pranzo': '🍽️ Pranzo',
            'spuntino_pomeridiano': '🥨 Spuntino Pomeridiano',
            'cena': '🌙 Cena',
            'spuntino_serale': '🌃 Spuntino Serale'
        }
        
        display_name = meal_display_names.get(meal_name, f'🍽️ {meal_name.title()}')
        
        with st.expander(display_name):
            # Alimenti del pasto
            if "alimenti" in meal_data and meal_data["alimenti"]:
                st.markdown("**🛒 Ingredienti:**")
                
                alimenti = meal_data["alimenti"]
                
                # Gestisce sia formato lista che formato dizionario
                if isinstance(alimenti, list):
                    # Formato lista: [{"nome_alimento": "...", "quantita_g": ..., "misura_casalinga": "..."}]
                    for alimento in alimenti:
                        nome = alimento.get('nome_alimento', 'N/A')
                        quantita = alimento.get('quantita_g', 'N/A')
                        misura = alimento.get('misura_casalinga', '')
                        
                        st.markdown(f"- **{nome}**: {quantita}g ({misura})" if misura else f"- **{nome}**: {quantita}g")

                elif isinstance(alimenti, dict):
                    # Formato dizionario: {"nome_alimento": quantita_g}
                    for nome_alimento, quantita in alimenti.items():
                        if isinstance(quantita, (int, float)) and quantita > 0:
                            st.markdown(f"- **{nome_alimento}**: {quantita}g")
                        else:
                            st.markdown(f"- **{nome_alimento}**: Quantità da definire")
            
            # Separatore
            st.markdown('<hr style="margin: 20px 0; border: 1px solid #ddd;">', unsafe_allow_html=True)
    
    def _display_single_meal(self, meal, index, total_meals):
        """
        Mostra un singolo pasto registrato.
        
        Args:
            meal: Dati del pasto
            index: Indice del pasto
            total_meals: Numero totale di pasti
        """
        nome_pasto = meal.get('nome_pasto', 'Pasto').title()
        
        with st.expander(f"🍽️ {nome_pasto}"):
            # Lista ingredienti
            self._display_meal_ingredients(meal)
            
            # Totali nutrizionali
            self._display_meal_nutritional_totals(meal)
    
    def _display_meal_ingredients(self, meal):
        """
        Mostra gli ingredienti del pasto.
        
        Args:
            meal: Dati del pasto
        """
        if "alimenti" not in meal or not meal["alimenti"]:
            return
            
        st.markdown("**🛒 Ingredienti:**")
        
        for alimento in meal["alimenti"]:
            nome = alimento.get('nome_alimento', 'N/A')
            quantita = alimento.get('quantita_g', 'N/A')
            stato = alimento.get('stato', 'N/A')
            misura = alimento.get('misura_casalinga', 'N/A')
            metodo = alimento.get('metodo_cottura', '')
            
            st.markdown(f"- **{nome}**: {quantita}g ({stato}, {misura}) {metodo if metodo else ''}")
    
    def _display_meal_nutritional_totals(self, meal):
        """
        Mostra i totali nutrizionali del pasto.
        
        Args:
            meal: Dati del pasto
        """
        if "totali_pasto" not in meal:
            return
            
        totali = meal["totali_pasto"]
        
        # Controllo di sicurezza per totali None - non mostra nulla se non disponibili
        if not totali:
            return
        
        st.markdown("**📊 Valori Nutrizionali Totali:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Calorie", value=f"{totali.get('kcal_totali', 0)} kcal")
            st.metric(label="Carboidrati", value=f"{totali.get('carboidrati_totali', 0)}g")
        with col2:
            st.metric(label="Proteine", value=f"{totali.get('proteine_totali', 0)}g")
            st.metric(label="Grassi", value=f"{totali.get('grassi_totali', 0)}g")


# Funzione di utilità per mantenere compatibilità con app.py
def handle_user_data():
    """
    Funzione wrapper per compatibilità con app.py.
    Gestisce la visualizzazione dei dati utente estratti da DeepSeek.
    """
    if "user_info" not in st.session_state or "id" not in st.session_state.user_info:
        st.warning("⚠️ Nessun utente autenticato.")
        return
    
    piano_nutrizionale = PianoNutrizionale()
    piano_nutrizionale.display_nutritional_plan(st.session_state.user_info["id"]) 