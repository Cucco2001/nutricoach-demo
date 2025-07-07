"""
Modulo per la gestione della homepage dell'applicazione.

Questo modulo gestisce la visualizzazione della homepage che include:
- Dieta del giorno corrente
- Collegamenti alle altre sezioni
- Panoramica rapida dello stato nutrizionale
"""

import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import per riutilizzare funzionalità del Piano Nutrizionale
from frontend.Piano_nutrizionale import PianoNutrizionale

# Import del sistema di stili adattivi
from frontend.adaptive_style import get_device_type

# Nota: Utilizziamo st.session_state per mantenere compatibilità


class Home:
    """Gestisce la homepage dell'applicazione con la dieta giornaliera e i collegamenti alle sezioni"""
    
    def __init__(self):
        """Inizializza il gestore della homepage"""
        self.piano_nutrizionale = PianoNutrizionale()
        self._setup_css_styles()
    
    def _setup_css_styles(self):
        """Gli stili CSS sono ora gestiti dai file globali style.py e mobile_style.py"""
        pass
    
    def display_home(self, user_id: str):
        """
        Mostra la homepage con la dieta del giorno corrente e i collegamenti alle sezioni.
        
        Args:
            user_id: ID dell'utente
        """
        # Header di benvenuto
        self._display_welcome_header()
        
        # Controlla se DeepSeek sta elaborando
        is_processing = self.piano_nutrizionale._is_deepseek_processing(user_id)
        
        if is_processing:
            self._display_processing_message()
        else:
            # Carica i dati nutrizionali
            extracted_data = self.piano_nutrizionale._load_user_nutritional_data(user_id)
            
            if not extracted_data:
                self._display_no_data_message()
            else:
                # Mostra la dieta del giorno corrente
                self._display_current_day_diet(extracted_data)
                
                # Separatore
                st.markdown("---")
                
                
    
    def _display_welcome_header(self):
        """Mostra l'header di benvenuto personalizzato"""
        # Ottieni informazioni utente
        user_info = st.session_state.get('user_info', {})
        username = user_info.get('username', 'Utente')
        
        # Ottieni il saluto in base all'ora del giorno
        greeting = self._get_time_based_greeting()
        
        # Ottieni il giorno corrente
        current_day = self._get_current_day()
        
        st.markdown(f"""
        <div class="home-welcome-gradient">
            <h1>🥗 {greeting}, {username}!</h1>
            <p style="font-size: 8em; font-weight: 900; line-height: 1.0; opacity: 0.98; margin: 0.3em 0;">
                📅 {current_day}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_processing_message(self):
        """Mostra il messaggio quando DeepSeek sta elaborando"""
        st.markdown("""
        <div class="home-processing">
            <h2>🤖 Elaborazione in corso...</h2>
            <p>Stiamo analizzando i tuoi dati nutrizionali dalla conversazione con l'assistente.</p>
            <p>La tua dieta giornaliera sarà disponibile a breve!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostra comunque i collegamenti alle sezioni
        st.markdown("---")
    
    def _display_no_data_message(self):
        """Mostra il messaggio quando non ci sono dati disponibili"""
        st.markdown("""
        <div class="home-no-data">
            <h2>🍽️ Inizia il tuo percorso nutrizionale</h2>
            <p>Non hai ancora un piano nutrizionale personalizzato.</p>
            <p>Inizia a chattare con l'assistente per creare la tua dieta personalizzata!</p>
        </div>
        """, unsafe_allow_html=True)
        

    
    def _display_current_day_diet(self, extracted_data: Dict):
        """
        Mostra la dieta del giorno corrente.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        # Determina il giorno corrente della settimana (1-7)
        current_day_num = self._get_current_day_number()
        
        # Trova i dati per il giorno corrente
        day_data, is_day_1, day_found = self._find_current_day_data(extracted_data, current_day_num)
        
        if not day_found:
            self._display_no_current_day_data(current_day_num)
            return
        
        # Header per la dieta del giorno
        day_name = self._get_day_name(current_day_num)
        

        
        # Mostra i pasti del giorno
        if is_day_1:
            # Giorno 1: formato lista
            sorted_meals = self.piano_nutrizionale._sort_meals_by_time(day_data)
            self._display_meals_simplified(sorted_meals, is_day_1=True)
        else:
            # Giorni 2-7: formato dizionario
            self._display_meals_simplified(day_data, is_day_1=False)
    
    def _display_meals_simplified(self, meals_data, is_day_1: bool = True):
        """
        Mostra i pasti in formato semplificato per la homepage.
        
        Args:
            meals_data: Dati dei pasti
            is_day_1: True se sono dati del giorno 1, False altrimenti
        """
        if is_day_1:
            # Formato lista (giorno 1)
            for i, meal in enumerate(meals_data):
                self._display_single_meal_simplified(meal, i, len(meals_data))
        else:
            # Formato dizionario (giorni 2-7)
            meal_order = ['colazione', 'spuntino_mattutino', 'pranzo', 'spuntino_pomeridiano', 'cena', 'spuntino_serale']
            
            displayed_meals = 0
            for meal_name in meal_order:
                if meal_name in meals_data and meals_data[meal_name]:
                    self._display_weekly_meal_simplified(meal_name, meals_data[meal_name])
                    displayed_meals += 1
            
            # Se non ci sono pasti nell'ordine standard, mostra tutti
            if displayed_meals == 0:
                for meal_name, meal_data in meals_data.items():
                    if meal_data:
                        self._display_weekly_meal_simplified(meal_name, meal_data)
    
    def _display_single_meal_simplified(self, meal: Dict, index: int, total_meals: int):
        """
        Mostra un singolo pasto in formato semplificato.
        
        Args:
            meal: Dati del pasto
            index: Indice del pasto
            total_meals: Numero totale di pasti
        """
        nome_pasto = meal.get('nome_pasto', 'Pasto').title()
        
        # Determina emoji per il pasto
        emoji_pasto = self._get_meal_emoji(nome_pasto)
        
        # Container per il pasto
        with st.container():
            # Header del pasto - Card grande e verde
            st.markdown(f"""
            <div class="home-meal-card">
                <h4>{emoji_pasto} {nome_pasto}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Tendina per i dettagli del pasto
            with st.expander("👀 Vedi alimenti", expanded=False):
                # Mostra ingredienti con stile migliorato
                if "alimenti" in meal and meal["alimenti"]:
                    for alimento in meal["alimenti"]:
                        nome = alimento.get('nome_alimento', 'N/A')
                        quantita = alimento.get('quantita_g', 'N/A')
                        stato = alimento.get('stato', '')
                        misura = alimento.get('misura_casalinga', '')
                        sostituti = alimento.get('sostituti', '')
                        
                        # Costruisci la descrizione dell'ingrediente con sostituti
                        ingrediente_desc = f"**{nome}** - {quantita}g"
                        if stato and stato != 'N/A':
                            ingrediente_desc += f" ({stato})"
                        if misura and misura != 'N/A':
                            ingrediente_desc += f" - {misura}"
                        if sostituti and sostituti != 'N/A' and sostituti.strip():
                            ingrediente_desc += f" ➜ *{sostituti}*"
                        
                        st.markdown(f"• {ingrediente_desc}")
                else:
                    st.info("Nessun ingrediente disponibile per questo pasto.")
            
            # Separatore sottile
            if index < total_meals - 1:
                st.markdown('<hr class="home-meal-separator">', unsafe_allow_html=True)
    
    def _display_weekly_meal_simplified(self, meal_name: str, meal_data: Dict):
        """
        Mostra un pasto settimanale in formato semplificato.
        
        Args:
            meal_name: Nome del pasto
            meal_data: Dati del pasto
        """
        # Converti il nome del pasto
        meal_display_names = {
            'colazione': '🌅 Colazione',
            'spuntino_mattutino': '🥤 Spuntino Mattutino', 
            'pranzo': '🍽️ Pranzo',
            'spuntino_pomeridiano': '🥨 Spuntino Pomeridiano',
            'cena': '🌙 Cena',
            'spuntino_serale': '🌃 Spuntino Serale'
        }
        
        display_name = meal_display_names.get(meal_name, f'🍽️ {meal_name.title()}')
        
        # Header del pasto - Card grande e verde
        st.markdown(f"""
        <div class="home-meal-card">
            <h4>{display_name}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Tendina per i dettagli del pasto
        with st.expander("👀 Vedi alimenti", expanded=False):
            # Mostra ingredienti con stile migliorato
            if "alimenti" in meal_data and meal_data["alimenti"]:
                alimenti = meal_data["alimenti"]
                
                if isinstance(alimenti, list):
                    for alimento in alimenti:
                        nome = alimento.get('nome_alimento', 'N/A')
                        quantita = alimento.get('quantita_g', 'N/A')
                        misura = alimento.get('misura_casalinga', '')
                        sostituti = alimento.get('sostituti', '')
                        
                        # Costruisci la descrizione dell'ingrediente con sostituti
                        ingrediente_desc = f"**{nome}** - {quantita}g"
                        if misura and misura != 'N/A':
                            ingrediente_desc += f" - {misura}"
                        if sostituti and sostituti != 'N/A' and sostituti.strip():
                            ingrediente_desc += f" ➜ *{sostituti}*"
                        
                        st.markdown(f"• {ingrediente_desc}")
                
                elif isinstance(alimenti, dict):
                    for nome, quantita in alimenti.items():
                        if isinstance(quantita, (int, float)) and quantita > 0:
                            st.markdown(f"• **{nome}** - {quantita}g")
                        else:
                            st.markdown(f"• **{nome}** - Quantità da definire")
            else:
                st.info("Nessun ingrediente disponibile per questo pasto.")
        
        # Separatore sottile
        st.markdown('<hr class="home-meal-separator">', unsafe_allow_html=True)
    
    def _display_no_current_day_data(self, current_day_num: int):
        """
        Mostra il messaggio quando non ci sono dati per il giorno corrente.
        
        Args:
            current_day_num: Numero del giorno corrente
        """
        day_name = self._get_day_name(current_day_num)
        
        st.markdown(f"""
        <div class="home-processing">
            <h3>📅 {day_name}</h3>
            <p>Non hai ancora una dieta programmata per oggi.</p>
            <p>Chatta con l'assistente per creare il tuo piano settimanale!</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_section_links(self):
        """Mostra i collegamenti alle altre sezioni in modo accattivante"""
        st.markdown("""
        <div style="text-align: center; margin: 30px 0;">
            <h3>🧭 Naviga nelle sezioni</h3>
            <p>Accedi rapidamente alle funzionalità principali</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Grid di collegamenti
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💬 Chat con l'Assistente", use_container_width=True, type="primary", key="nav_to_chat"):
                st.session_state.current_page = "Chat"
                st.rerun()
        
        with col2:
            if st.button("⚙️ Preferenze", use_container_width=True, key="nav_to_preferences"):
                st.session_state.current_page = "Preferenze"
                st.rerun()
        
        with col3:
            if st.button("📊 Piano Nutrizionale", use_container_width=True, key="nav_to_nutrition"):
                st.session_state.current_page = "Piano Nutrizionale"
                st.rerun()
        
        # Aggiungi descrizioni accattivanti
        st.markdown("""
        <div class="home-nav-description">
            <div class="home-nav-item">
                <small style="color: #666;">Parla con l'AI per creare la tua dieta</small>
            </div>
            <div class="home-nav-item">
                <small style="color: #666;">Personalizza le tue preferenze alimentari</small>
            </div>
            <div class="home-nav-item">
                <small style="color: #666;">Visualizza il piano completo e scarica il PDF</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_quick_overview(self, extracted_data: Dict):
        """
        Mostra una panoramica veloce dei dati nutrizionali.
        
        Args:
            extracted_data: Dati nutrizionali estratti
        """
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center; margin: 20px 0;">
            <h3>📊 Panoramica Veloce</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostra statistiche principali se disponibili
        col1, col2, col3, col4 = st.columns(4)
        
        # Fabbisogno calorico
        with col1:
            caloric_data = extracted_data.get("caloric_data", {})
            tdee = caloric_data.get("tdee", 0)
            if tdee > 0:
                st.markdown(f"""
                <div class="home-stat-card tdee">
                    <h4>🔥 TDEE</h4>
                    <p style="font-size: 1.2em; margin: 0;">{tdee} kcal</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="home-stat-card" style="background: #ddd; color: #666;">
                    <h4>🔥 TDEE</h4>
                    <p style="font-size: 1.2em; margin: 0;">N/A</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Proteine
        with col2:
            macros_data = extracted_data.get("macros_data", {})
            proteine = macros_data.get("proteine_g", 0)
            if proteine > 0:
                st.markdown(f"""
                <div class="home-stat-card proteine">
                    <h4>🥩 Proteine</h4>
                    <p style="font-size: 1.2em; margin: 0;">{proteine}g</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="home-stat-card" style="background: #ddd; color: #666;">
                    <h4>🥩 Proteine</h4>
                    <p style="font-size: 1.2em; margin: 0;">N/A</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Carboidrati
        with col3:
            carboidrati = macros_data.get("carboidrati_g", 0)
            if carboidrati > 0:
                st.markdown(f"""
                <div class="home-stat-card carboidrati">
                    <h4>🍞 Carboidrati</h4>
                    <p style="font-size: 1.2em; margin: 0;">{carboidrati}g</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="home-stat-card" style="background: #ddd; color: #666;">
                    <h4>🍞 Carboidrati</h4>
                    <p style="font-size: 1.2em; margin: 0;">N/A</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Grassi
        with col4:
            grassi = macros_data.get("grassi_g", 0)
            if grassi > 0:
                st.markdown(f"""
                <div class="home-stat-card grassi">
                    <h4>🥑 Grassi</h4>
                    <p style="font-size: 1.2em; margin: 0;">{grassi}g</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="home-stat-card" style="background: #ddd; color: #666;">
                    <h4>🥑 Grassi</h4>
                    <p style="font-size: 1.2em; margin: 0;">N/A</p>
                </div>
                """, unsafe_allow_html=True)
    
    def _get_time_based_greeting(self) -> str:
        """
        Restituisce un saluto in base all'ora del giorno.
        
        Returns:
            str: Saluto personalizzato
        """
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Buongiorno"
        elif 12 <= current_hour < 17:
            return "Buon pomeriggio"
        elif 17 <= current_hour < 21:
            return "Buonasera"
        else:
            return "Buonanotte"
    
    def _get_current_day(self) -> str:
        """
        Restituisce il giorno corrente in formato leggibile.
        
        Returns:
            str: Giorno corrente
        """
        days = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        return days[datetime.now().weekday()]
    
    def _get_current_day_number(self) -> int:
        """
        Restituisce il numero del giorno corrente (1-7, dove 1 = Lunedì).
        
        Returns:
            int: Numero del giorno corrente
        """
        return datetime.now().weekday() + 1
    
    def _get_day_name(self, day_num: int) -> str:
        """
        Restituisce il nome del giorno dato il numero.
        
        Args:
            day_num: Numero del giorno (1-7)
            
        Returns:
            str: Nome del giorno
        """
        days = {1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 
                5: "Venerdì", 6: "Sabato", 7: "Domenica"}
        return days.get(day_num, f"Giorno {day_num}")
    
    def _find_current_day_data(self, extracted_data: Dict, current_day_num: int) -> Tuple[Optional[Dict], bool, bool]:
        """
        Trova i dati per il giorno corrente.
        
        Args:
            extracted_data: Dati nutrizionali estratti
            current_day_num: Numero del giorno corrente
            
        Returns:
            Tuple[Optional[Dict], bool, bool]: (dati_giorno, is_day_1, trovato)
        """
        # Controlla se è il giorno 1 (Lunedì) e ci sono dati weekly_diet_day_1
        if current_day_num == 1 and "weekly_diet_day_1" in extracted_data:
            day_1_data = extracted_data["weekly_diet_day_1"]
            if day_1_data:
                return day_1_data, True, True
        
        # Controlla i giorni 2-7 nella sezione weekly_diet_days_2_7
        if "weekly_diet_days_2_7" in extracted_data:
            weekly_data = extracted_data["weekly_diet_days_2_7"]
            day_key = f"giorno_{current_day_num}"
            
            if day_key in weekly_data and weekly_data[day_key]:
                return weekly_data[day_key], False, True
        
        return None, False, False
    
    def _get_meal_emoji(self, nome_pasto: str) -> str:
        """
        Restituisce l'emoji appropriata per il pasto.
        
        Args:
            nome_pasto: Nome del pasto
            
        Returns:
            str: Emoji del pasto
        """
        nome_lower = nome_pasto.lower()
        
        if 'colazione' in nome_lower or 'breakfast' in nome_lower:
            return '🌅'
        elif 'pranzo' in nome_lower or 'lunch' in nome_lower:
            return '🍽️'
        elif 'cena' in nome_lower or 'dinner' in nome_lower:
            return '🌙'
        elif 'spuntino' in nome_lower or 'merenda' in nome_lower or 'snack' in nome_lower:
            if 'mattut' in nome_lower or 'mattina' in nome_lower:
                return '🥤'
            elif 'pomer' in nome_lower or 'pomeriggio' in nome_lower:
                return '🥨'
            elif 'seral' in nome_lower or 'sera' in nome_lower:
                return '🌃'
            else:
                return '🍎'
        else:
            return '🍽️'


# Funzione di utilità per mantenere compatibilità con app.py
def handle_home():
    """
    Funzione wrapper per compatibilità con app.py.
    Gestisce la visualizzazione della homepage.
    """
    if "user_info" not in st.session_state or "id" not in st.session_state.user_info:
        st.warning("⚠️ Nessun utente autenticato.")
        return
    
    home = Home()
    home.display_home(st.session_state.user_info["id"]) 