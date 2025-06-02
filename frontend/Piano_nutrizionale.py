"""
Modulo per la gestione e visualizzazione del piano nutrizionale.

Questo modulo gestisce la visualizzazione dei dati nutrizionali estratti
automaticamente dal sistema DeepSeek durante le conversazioni con l'agente.
"""

import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

# Import del servizio PDF
from services.pdf_service import PDFGenerator


class PianoNutrizionale:
    """Gestisce la visualizzazione del piano nutrizionale e dei dati estratti"""
    
    def __init__(self):
        """Inizializza il gestore del piano nutrizionale"""
        self._setup_css_styles()
        self.pdf_generator = PDFGenerator()
    
    def _setup_css_styles(self):
        """Configura gli stili CSS personalizzati per l'interfaccia"""
        st.markdown("""
        <style>
        .main-title {
            font-size: 28px;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 10px;
        }
        .section-content {
            font-size: 14px;
        }
        .metric-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 5px 0;
        }
        .macro-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 12px;
            border-radius: 10px;
            margin: 8px 0;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .meal-card {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        .ingredient-card {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 8px;
            border-radius: 8px;
            margin: 5px 0;
            color: #333;
            font-size: 13px;
        }
        .info-card {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 12px;
            border-radius: 10px;
            margin: 8px 0;
            color: #333;
            font-size: 13px;
        }
        .stExpander > div > div > div > div {
            font-size: 14px;
        }
        .download-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            margin: 10px 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def display_nutritional_plan(self, user_id):
        """
        Mostra il piano nutrizionale e i dati estratti per l'utente.
        
        Args:
            user_id: ID dell'utente di cui mostrare i dati
        """
        st.markdown('<h1 class="main-title">📊 Piano Nutrizionale Personalizzato</h1>', unsafe_allow_html=True)
        
        try:
            extracted_data = self._load_user_nutritional_data(user_id)
            
            if not extracted_data:
                st.info("🤖 Nessun dato nutrizionale disponibile ancora. Continua la conversazione con l'agente per raccogliere dati.")
                return
            
            # Header con pulsante download
            self._display_header_with_download(extracted_data, user_id)
            st.divider()
            
            # Sezioni principali del piano nutrizionale
            self._display_caloric_needs_section(extracted_data)
            self._display_macros_section(extracted_data)
            self._display_daily_plan_section(extracted_data)
            self._display_registered_meals_section(extracted_data)
            
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
            # Genera PDF e crea download button diretto
            try:
                # Ottieni le informazioni dell'utente da session_state
                user_info = st.session_state.get('user_info', {})
                
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
        user_file_path = f"user_data/{user_id}.json"
        
        if not os.path.exists(user_file_path):
            st.warning("📝 File utente non trovato.")
            return None
            
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        return user_data.get("nutritional_info_extracted", {})
    
    def _display_caloric_needs_section(self, extracted_data):
        """
        Mostra la sezione del fabbisogno energetico.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if "caloric_needs" not in extracted_data:
            return
            
        with st.expander("🔥 Fabbisogno Energetico Giornaliero", expanded=False):
            caloric_data = extracted_data["caloric_needs"]
            
            # Metrics principali con stile colorato
            col1, col2, col3, col4 = st.columns(4)
            
            metrics = [
                ("⚡ Metabolismo Basale", caloric_data.get('bmr', 0), "Energia per le funzioni vitali"),
                ("🏃 Fabbisogno Base", caloric_data.get('fabbisogno_base', 0), "Con attività quotidiana"),
                ("💪 Dispendio Sportivo", caloric_data.get('dispendio_sportivo', 0), "Calorie dall'attività sportiva"),
                ("🎯 Fabbisogno Totale", caloric_data.get('fabbisogno_totale', 0), "Calorie totali giornaliere")
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
            
            # Info aggiuntive
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
        if "macros_total" not in extracted_data:
            return
            
        with st.expander("🥗 Distribuzione Calorica Giornaliera", expanded=False):
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
        if "daily_macros" not in extracted_data:
            return
            
        with st.expander("🍽️ Piano Pasti Giornaliero", expanded=False):
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
        
        for i, (pasto_nome, pasto_data) in enumerate(distribuzione_pasti.items()):
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
    
    def _display_registered_meals_section(self, extracted_data):
        """
        Mostra la sezione dei pasti creati/registrati.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        if "registered_meals" not in extracted_data:
            return
            
        with st.expander("👨‍🍳 Ricette e Pasti Creati", expanded=False):
            meals_data = extracted_data["registered_meals"]
            
            for i, meal in enumerate(meals_data):
                self._display_single_meal(meal, i, len(meals_data))
    
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
        <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
                    padding: 15px; border-radius: 12px; margin: 15px 0; color: white;">
            <h3>🍽️ {nome_pasto}</h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # Lista ingredienti
        self._display_meal_ingredients(meal)
        
        # Totali nutrizionali
        self._display_meal_nutritional_totals(meal)
        
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
            
        st.markdown("**🛒 Ingredienti:**")
        
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
        st.markdown("**📊 Valori Nutrizionali Totali:**")
        
        col1, col2, col3, col4 = st.columns(4)
        nutrition_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        nutrition_data = [
            ('🔥 Calorie', f"{totali.get('kcal_totali', 0)} kcal"),
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