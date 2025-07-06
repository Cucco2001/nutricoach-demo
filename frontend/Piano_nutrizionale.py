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
            # Ottieni user_id dal session_state
            user_id = None
            if hasattr(st.session_state, 'user_info') and st.session_state.user_info:
                user_id = st.session_state.user_info.get('id')
            
            if user_id:
                status = st.session_state.deepseek_manager.get_extraction_status(user_id)
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
            
            # === SEZIONE FABBISOGNO ENERGETICO ===
            with st.expander("🔥 Fabbisogno Energetico Giornaliero", expanded=False):
                self._display_caloric_needs_section(extracted_data)
            
            # === SEZIONE DISTRIBUZIONE MACROS ===
            with st.expander("🥗 Distribuzione Calorica Giornaliera", expanded=False):
                self._display_macros_section(extracted_data)

            # === SEZIONE PIANO PASTI ===
            with st.expander("🍽️ Piano Pasti Giornaliero", expanded=False):
                self._display_daily_plan_section(extracted_data)

            # === SEZIONE PIANO SETTIMANALE ===
            with st.expander("📅 Piano Settimanale - Ricette e Pasti Creati", expanded=False):
                self._display_weekly_diet_day_1_section(extracted_data)
            
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

        caloric_data = extracted_data["caloric_needs"]
        
        # Metrics principali con stile colorato
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            ("⚡ Metabolismo", caloric_data.get('bmr', 0), "Energia per le funzioni vitali"),
            ("🏃 Fabbisogno Base", caloric_data.get('fabbisogno_base', 0), "Con attività quotidiana"),
            ("💪 Dispendio Sportivo", caloric_data.get('dispendio_sportivo', 0), "Calorie dall'attività sportiva"),
            ("🎯 Fabbisogno Finale", caloric_data.get('fabbisogno_finale', 0), "Calorie totali giornaliere")
        ]
        
        for col, (title, value, description) in zip([col1, col2, col3, col4], metrics):
            with col:
                st.markdown(f'''
                <div class="metric-container">
                    <h4>{title}</h4>
                    <h2>{value} kcal</h2>
                    <small>{description}</small>
                </div>
                ''', unsafe_allow_html=True)
        
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
            # Cards dei macronutrienti colorate
            macros_info = [
                ('Proteine', '🥩', '#FF6B6B'),
                ('Carboidrati', '🍞', '#4ECDC4'), 
                ('Grassi', '🥑', '#45B7D1')
            ]
            
            for i, (macro, emoji, color) in enumerate(macros_info):
                row = macro_df.iloc[i]
                st.markdown(f'''
                <div style="background: linear-gradient(135deg, {color} 0%, {color}88 100%); 
                            padding: 12px; border-radius: 10px; margin: 8px 0; color: white;">
                    <h4>{emoji} {macro}</h4>
                    <p><strong>{row['Grammi']}g</strong> ({row['Kcal']} kcal)</p>
                    <p style="font-size: 12px; opacity: 0.9;">{row['Percentuale']}% del totale</p>
                </div>
                ''', unsafe_allow_html=True)
        
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
            kcal_finali = macros_data.get('kcal_finali', 0)
            st.markdown(f'''
            <div class="info-card">
                <strong>🔥 Calorie Totali:</strong> {kcal_finali} kcal
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

        daily_data = extracted_data["daily_macros"]
        
        num_pasti = daily_data.get('numero_pasti', 0)
        st.markdown(f'<div class="info-card"><strong>📅 Piano giornaliero:</strong> {num_pasti} pasti</div>', 
                   unsafe_allow_html=True)
        
        if "distribuzione_pasti" in daily_data:
            self._display_meal_distribution(daily_data["distribuzione_pasti"])
    
    def _display_meal_distribution(self, distribuzione_pasti):
        """
        Mostra la distribuzione dei pasti.
        
        Args:
            distribuzione_pasti: Dati della distribuzione dei pasti
        """
        # Timeline dei pasti colorata
        meal_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        # Definisce l'ordine cronologico dei pasti con tutte le varianti possibili
        meal_order = {
            'colazione': 1,
            'breakfast': 1,
            'prima_colazione': 1,
            
            'spuntino_mattutino': 2,
            'spuntino_mattina': 2,
            'spuntino_del_mattino': 2,
            'merenda_mattutina': 2,
            'snack_mattutino': 2,
            'break_mattutino': 2,
            
            'pranzo': 3,
            'lunch': 3,
            'pasto_principale': 3,
            
            'spuntino_pomeridiano': 4,
            'spuntino_pomeriggio': 4,
            'spuntino_del_pomeriggio': 4,
            'merenda': 4,
            'merenda_pomeridiana': 4,
            'snack_pomeridiano': 4,
            'break_pomeridiano': 4,
            
            'cena': 5,
            'dinner': 5,
            'secondo_pasto': 5,
            
            'spuntino_serale': 6,
            'merenda_serale': 6,
            'snack_serale': 6,
        }
        
        def get_meal_priority(meal_item):
            """Calcola la priorità di ordinamento per un pasto"""
            pasto_nome = meal_item[0].lower().strip()
            
            # Normalizza il nome rimuovendo spazi e caratteri speciali
            nome_normalizzato = pasto_nome.replace(' ', '_').replace('-', '_')
            
            # Cerca corrispondenza diretta
            if nome_normalizzato in meal_order:
                return meal_order[nome_normalizzato]
            
            # Ricerca parziale con parole chiave
            if 'colazione' in pasto_nome or 'breakfast' in pasto_nome:
                return 1
            elif ('spuntino' in pasto_nome or 'merenda' in pasto_nome or 'snack' in pasto_nome) and \
                 ('mattut' in pasto_nome or 'mattina' in pasto_nome):
                return 2
            elif 'pranzo' in pasto_nome or 'lunch' in pasto_nome:
                return 3
            elif ('spuntino' in pasto_nome or 'merenda' in pasto_nome or 'snack' in pasto_nome) and \
                 ('pomer' in pasto_nome or 'pomeriggio' in pasto_nome):
                return 4
            elif 'cena' in pasto_nome or 'dinner' in pasto_nome:
                return 5
            elif ('spuntino' in pasto_nome or 'merenda' in pasto_nome or 'snack' in pasto_nome) and \
                 ('seral' in pasto_nome or 'sera' in pasto_nome):
                return 6
            else:
                # Pasti non riconosciuti vanno alla fine
                return 999
        
        # Ordina i pasti secondo l'ordine cronologico usando la funzione avanzata
        sorted_meals = sorted(distribuzione_pasti.items(), key=get_meal_priority)
        
        for i, (pasto_nome, pasto_data) in enumerate(sorted_meals):
            # Controllo di sicurezza per pasto_data
            if not pasto_data:
                continue
                
            color = meal_colors[i % len(meal_colors)]
            kcal = pasto_data.get('kcal', 0)
            percentuale = pasto_data.get('percentuale_kcal', 0)
            
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, {color} 0%, {color}88 100%); 
                        padding: 15px; border-radius: 12px; margin: 10px 0; color: white;">
                <h3>🍽️ {pasto_nome.title()}</h3>
                <p style="font-size: 16px;"><strong>{kcal} kcal</strong> ({percentuale}% del totale)</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # Macros del pasto in cards piccole
            self._display_meal_macros(pasto_data)
    
    def _display_meal_macros(self, pasto_data):
        """
        Mostra i macronutrienti del singolo pasto.
        
        Args:
            pasto_data: Dati del pasto
        """
        # Controllo di sicurezza per pasto_data
        if not pasto_data:
            return
            
        col1, col2, col3 = st.columns(3)
        
        macro_info = [
            ("🥩 Proteine", pasto_data.get('proteine_g', 0), "g"),
            ("🍞 Carboidrati", pasto_data.get('carboidrati_g', 0), "g"),
            ("🥑 Grassi", pasto_data.get('grassi_g', 0), "g")
        ]
        
        for col, (label, value, unit) in zip([col1, col2, col3], macro_info):
            with col:
                st.markdown(f'<div class="ingredient-card"><strong>{label}:</strong> {value}{unit}</div>', 
                           unsafe_allow_html=True)
    
    def _display_weekly_diet_day_1_section(self, extracted_data):
        """
        Mostra la sezione dei pasti creati/registrati organizzati per giorno.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        # Verifica che extracted_data non sia None
        if not extracted_data:
            return
            
        # Controlla se ci sono dati da mostrare
        has_day1_data = "weekly_diet_day_1" in extracted_data and extracted_data["weekly_diet_day_1"]
        has_weekly_data = "weekly_diet_days_2_7" in extracted_data and extracted_data["weekly_diet_days_2_7"]
        
        if not has_day1_data and not has_weekly_data:
            return
        
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
            
        has_day1 = "weekly_diet_day_1" in extracted_data and extracted_data["weekly_diet_day_1"]
        weekly_diet_days_2_7 = extracted_data.get("weekly_diet_days_2_7", {})
        
        available_days = []
        if has_day1:
            available_days.append("Giorno 1")
        
        for day_num in range(2, 8):
            day_key = f"giorno_{day_num}"
            if day_key in weekly_diet_days_2_7 and weekly_diet_days_2_7[day_key]:
                available_days.append(f"Giorno {day_num}")
        
        if available_days:
            st.markdown(f"""
            <div class="home-welcome-gradient">
                <h4>📊 Piano Settimanale Disponibile</h4>
                <p><strong>Giorni con dati:</strong> {' • '.join(available_days)}</p>
                <p><em>Totale giorni pianificati: {len(available_days)}/7</em></p>
            </div>
            """, unsafe_allow_html=True)
    
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
            day_options["Giorno 1"] = (1, extracted_data["weekly_diet_day_1"], True)
        
        # Aggiungi Giorni 2-7 se disponibili
        if has_weekly_data:
            weekly_diet_days_2_7 = extracted_data["weekly_diet_days_2_7"]
            for day_num in range(2, 8):
                day_key = f"giorno_{day_num}"
                if day_key in weekly_diet_days_2_7 and weekly_diet_days_2_7[day_key]:
                    day_label = f"Giorno {day_num}"
                    day_options[day_label] = (day_num, weekly_diet_days_2_7[day_key], False)
        
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
            day_num, day_data, is_weekly_diet_day_1 = day_options[selected_day_label]
            
            st.markdown("---")  # Separatore
            
            # Mostra i pasti del giorno selezionato
            self._display_day_meals(day_num, day_data, is_weekly_diet_day_1)
    
    def _display_day_meals(self, day_num, day_data, is_weekly_diet_day_1=False):
        """
        Mostra i pasti di un singolo giorno.
        
        Args:
            day_num: Numero del giorno (1-7)
            day_data: Dati del giorno (lista per weekly_diet_day_1, dict per weekly_diet_days_2_7)
            is_weekly_diet_day_1: True se i dati vengono da weekly_diet_day_1 (giorno 1)
        """
        # Determina il nome del giorno
        day_names = {
            1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 
            5: "Venerdì", 6: "Sabato", 7: "Domenica"
        }
        day_name = day_names.get(day_num, f"Giorno {day_num}")
        
        # Header del giorno
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); 
                    padding: 20px; border-radius: 15px; margin: 20px 0; color: white; text-align: center;">
            <h2>📅 {day_name} (Giorno {day_num})</h2>
            <p><em>{'Piano base creato' if is_weekly_diet_day_1 else 'Piano settimanale generato'}</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        if is_weekly_diet_day_1:
            # Giorno 1: weekly_diet_day_1 (lista di pasti)
            sorted_meals = self._sort_meals_by_time(day_data)
            for i, meal in enumerate(sorted_meals):
                self._display_single_meal(meal, i, len(sorted_meals))
        else:
            # Giorni 2-7: weekly_diet_days_2_7 (dict di pasti)
            self._display_weekly_diet_day(day_data)
    
    def _display_weekly_diet_day(self, day_data):
        """
        Mostra i pasti di un giorno dalla weekly_diet_days_2_7.
        
        Args:
            day_data: Dati del giorno dalla sezione weekly_diet_days_2_7
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
        Mostra un singolo pasto dalla weekly_diet_days_2_7.
        
        Args:
            meal_name: Nome del pasto
            meal_data: Dati del pasto dalla weekly_diet_days_2_7
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
        
        # Header del pasto con stile colorato (senza expander per evitare nesting)
        st.markdown(f'''
        <div class="home-meal-card">
            <h3>{display_name}</h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # Alimenti del pasto
        if "alimenti" in meal_data and meal_data["alimenti"]:
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
    
    def _sort_meals_by_time(self, meals_data):
        """
        Ordina i pasti in base all'ordine cronologico corretto: colazione, spuntino mattutino, 
        pranzo, spuntino pomeridiano, cena, spuntino serale.
        
        Args:
            meals_data: Lista dei pasti non ordinati
            
        Returns:
            list: Lista dei pasti ordinati cronologicamente
        """
        if not meals_data:
            return []
        
        # Definisce l'ordine cronologico dei pasti
        meal_order = {
            'colazione': 1,
            'breakfast': 1,
            'prima_colazione': 1,
            
            'spuntino_mattutino': 2,
            'spuntino_mattina': 2,
            'spuntino_del_mattino': 2,
            'merenda_mattutina': 2,
            'snack_mattutino': 2,
            'break_mattutino': 2,
            
            'pranzo': 3,
            'lunch': 3,
            'pasto_principale': 3,
            
            'spuntino_pomeridiano': 4,
            'spuntino_pomeriggio': 4,
            'spuntino_del_pomeriggio': 4,
            'merenda': 4,
            'merenda_pomeridiana': 4,
            'snack_pomeridiano': 4,
            'break_pomeridiano': 4,
            
            'cena': 5,
            'dinner': 5,
            'secondo_pasto': 5,
            
            'spuntino_serale': 6,
            'merenda_serale': 6,
            'snack_serale': 6,
        }
        
        def get_meal_priority(meal):
            """Calcola la priorità di ordinamento per un pasto"""
            nome_pasto = meal.get('nome_pasto', '').lower().strip()
            
            # Normalizza il nome rimuovendo spazi e caratteri speciali
            nome_normalizzato = nome_pasto.replace(' ', '_').replace('-', '_')
            
            # Cerca corrispondenza diretta
            if nome_normalizzato in meal_order:
                return meal_order[nome_normalizzato]
            
            # Ricerca parziale con parole chiave
            if 'colazione' in nome_pasto or 'breakfast' in nome_pasto:
                return 1
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('mattut' in nome_pasto or 'mattina' in nome_pasto):
                return 2
            elif 'pranzo' in nome_pasto or 'lunch' in nome_pasto:
                return 3
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('pomer' in nome_pasto or 'pomeriggio' in nome_pasto):
                return 4
            elif 'cena' in nome_pasto or 'dinner' in nome_pasto:
                return 5
            elif ('spuntino' in nome_pasto or 'merenda' in nome_pasto or 'snack' in nome_pasto) and \
                 ('seral' in nome_pasto or 'sera' in nome_pasto):
                return 6
            else:
                # Pasti non riconosciuti vanno alla fine
                return 999
        
        # Ordina i pasti in base alla priorità cronologica
        return sorted(meals_data, key=get_meal_priority)
    
    def _display_single_meal(self, meal, index, total_meals):
        """
        Mostra un singolo pasto registrato.
        
        Args:
            meal: Dati del pasto
            index: Indice del pasto
            total_meals: Numero totale di pasti
        """
        nome_pasto = meal.get('nome_pasto', 'Pasto').title()
        
        # Header del pasto
        st.markdown(f'''
        <div class="home-meal-card">
            <h3>🍽️ {nome_pasto}</h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # Lista ingredienti
        self._display_meal_ingredients(meal)
        
        # Separatore tra i pasti
        if index < total_meals - 1:
            st.markdown('<hr style="margin: 20px 0; border: 1px solid #ddd;">', unsafe_allow_html=True)
    
    def _display_meal_ingredients(self, meal):
        """
        Mostra gli ingredienti del pasto.
        
        Args:
            meal: Dati del pasto
        """
        if "alimenti" not in meal or not meal["alimenti"]:
            return
        
        for alimento in meal["alimenti"]:
            nome = alimento.get('nome_alimento', 'N/A')
            quantita = alimento.get('quantita_g', 'N/A')
            stato = alimento.get('stato', 'N/A')
            misura = alimento.get('misura_casalinga', 'N/A')
            metodo = alimento.get('metodo_cottura', '')
            
            st.markdown(f'''
            <div class="ingredient-card">
                <strong>{nome}</strong><br>
                📏 {quantita}g ({stato})<br>
                🥄 {misura}
                {f'<br>🔥 {metodo}' if metodo else ''}
            </div>
            ''', unsafe_allow_html=True)
    
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
        
        col1, col2, col3, col4 = st.columns(4)
        nutrition_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        nutrition_data = [
            ('🔥 Calorie', f"{totali.get('kcal_finali', 0)} kcal"),
            ('🥩 Proteine', f"{totali.get('proteine_totali', 0)}g"),
            ('🍞 Carboidrati', f"{totali.get('carboidrati_totali', 0)}g"),
            ('🥑 Grassi', f"{totali.get('grassi_totali', 0)}g")
        ]
        
        for k, (col, (label, value)) in enumerate(zip([col1, col2, col3, col4], nutrition_data)):
            with col:
                color = nutrition_colors[k]
                st.markdown(f'''
                <div style="background: {color}; padding: 10px; border-radius: 8px; 
                            text-align: center; color: white; margin: 2px;">
                    <div style="font-size: 12px;">{label}</div>
                    <div style="font-size: 14px; font-weight: bold;">{value}</div>
                </div>
                ''', unsafe_allow_html=True)


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