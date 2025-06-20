"""
Modulo per l'interfaccia utente delle preferenze alimentari.

Gestisce la visualizzazione e l'interazione con l'utente per la gestione
delle preferenze alimentari, inclusi form, bottoni e validazione input.
"""

import streamlit as st
from typing import Optional
from .food_preferences import FoodPreferences


class PreferencesUI:
    """Gestisce l'interfaccia utente per le preferenze alimentari"""
    
    def __init__(self, food_preferences: FoodPreferences):
        """
        Inizializza l'interfaccia delle preferenze.
        
        Args:
            food_preferences: Gestore della logica delle preferenze alimentari
        """
        self.food_preferences = food_preferences
    
    def display_preferences_interface(self, user_id: str):
        """
        Mostra l'interfaccia completa per la gestione delle preferenze.
        
        Args:
            user_id: ID dell'utente
        """
        st.markdown("""
            <div class="welcome-header">
                <h1>🥗 Le Tue <span class="gradient-text">Preferenze</span></h1>
                <p class="section-subtitle">Aggiungi cibi che ami o che vuoi evitare. L'AI adatterà il piano nutrizionale per te.</p>
            </div>
        """, unsafe_allow_html=True)

        # Inizializza le preferenze nella sessione
        self.food_preferences.initialize_session_preferences(user_id)
        
        col1, col2 = st.columns(2)

        with col1:
            self._display_excluded_foods_section()

        with col2:
            self._display_preferred_foods_section()
        
        # Bottone di salvataggio
        if st.button("Salva preferenze"):
            if self.food_preferences.save_preferences(user_id, ""):
                st.success("Preferenze salvate con successo!")
                st.rerun()
    
    def _display_excluded_foods_section(self):
        """Mostra la sezione degli alimenti esclusi"""
        st.markdown("<h3>🚫 Alimenti da Escludere</h3>", unsafe_allow_html=True)
        
        # Mostra gli alimenti esclusi esistenti
        excluded_foods = self.food_preferences.get_excluded_foods()
        for i, food in enumerate(excluded_foods):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"- {food}")
            with col2:
                if st.button("🗑️", key=f"del_excluded_{i}", help="Rimuovi alimento"):
                    if self.food_preferences.remove_excluded_food(i):
                        st.rerun()
        
        # Form per aggiungere nuovo alimento escluso
        self._display_add_food_form("excluded")
    
    def _display_preferred_foods_section(self):
        """Mostra la sezione degli alimenti preferiti"""
        st.markdown("<h3>❤️ Alimenti Preferiti</h3>", unsafe_allow_html=True)
        
        # Mostra gli alimenti preferiti esistenti
        preferred_foods = self.food_preferences.get_preferred_foods()
        for i, food in enumerate(preferred_foods):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(f"- {food}")
            with col2:
                if st.button("🗑️", key=f"del_preferred_{i}", help="Rimuovi alimento"):
                    if self.food_preferences.remove_preferred_food(i):
                        st.rerun()
        
        # Form per aggiungere nuovo alimento preferito
        self._display_add_food_form("preferred")
    
    def _display_add_food_form(self, food_type: str):
        """
        Mostra il form per aggiungere un nuovo alimento.
        
        Args:
            food_type: Tipo di alimento ("excluded" o "preferred")
        """
        label = "Inserisci un alimento da escludere" if food_type == "excluded" else "Inserisci un alimento preferito"
        
        # Utilizzo un form che si resetta automaticamente dopo il submit
        with st.form(key=f"add_{food_type}_form", clear_on_submit=True):
            col1, col2 = st.columns([0.7, 0.3])
            
            with col1:
                food_name = st.text_input(label, key=f"{food_type}_foods_input")
            
            with col2:
                st.write("")  # Spacer per allineare il bottone
                submitted = st.form_submit_button("➕ Aggiungi", use_container_width=True)
            
            if submitted and food_name:
                # Valida il nome dell'alimento
                is_valid, error_message = self.food_preferences.validate_food_name(food_name)
                
                if not is_valid:
                    st.error(error_message)
                else:
                    # Aggiungi l'alimento alla lista appropriata
                    success = False
                    if food_type == "excluded":
                        success = self.food_preferences.add_excluded_food(food_name)
                    elif food_type == "preferred":
                        success = self.food_preferences.add_preferred_food(food_name)
                    
                    if success:
                        st.success(f"Alimento '{food_name}' aggiunto!")
                        st.rerun()
                    else:
                        st.warning(f"L'alimento '{food_name}' è già nella lista")
    
    def display_preferences_summary(self, user_id: str):
        """
        Mostra un riassunto delle preferenze dell'utente.
        
        Args:
            user_id: ID dell'utente
        """
        user_preferences = self.food_preferences.load_user_preferences(user_id)
        
        if not user_preferences:
            st.info("Nessuna preferenza alimentare configurata")
            return
        
        # Mostra alimenti esclusi
        excluded_foods = user_preferences.get("excluded_foods", [])
        if excluded_foods:
            st.write("**🚫 Alimenti esclusi:**")
            for food in excluded_foods:
                st.write(f"• {food}")
        
        # Mostra alimenti preferiti
        preferred_foods = user_preferences.get("preferred_foods", [])
        if preferred_foods:
            st.write("**❤️ Alimenti preferiti:**")
            for food in preferred_foods:
                st.write(f"• {food}")
    
    def display_compact_preferences(self, user_id: str):
        """
        Mostra le preferenze in formato compatto (per sidebar o aree ridotte).
        
        Args:
            user_id: ID dell'utente
        """
        user_preferences = self.food_preferences.load_user_preferences(user_id)
        
        if not user_preferences:
            st.caption("Nessuna preferenza configurata")
            return
        
        excluded_count = len(user_preferences.get("excluded_foods", []))
        preferred_count = len(user_preferences.get("preferred_foods", []))
        
        if excluded_count > 0:
            st.caption(f"🚫 {excluded_count} alimenti esclusi")
        
        if preferred_count > 0:
            st.caption(f"❤️ {preferred_count} alimenti preferiti")
    
    def display_preferences_for_agent(self, user_id: str) -> Optional[str]:
        """
        Formatta le preferenze per essere inviate all'agente nutrizionale.
        
        Args:
            user_id: ID dell'utente
            
        Returns:
            Optional[str]: Stringa formattata con le preferenze o None se vuote
        """
        user_preferences = self.food_preferences.load_user_preferences(user_id)
        
        if not user_preferences:
            return None
        
        preferences_text = []
        
        # Aggiungi alimenti esclusi
        excluded_foods = user_preferences.get("excluded_foods", [])
        if excluded_foods:
            preferences_text.append(f"ALIMENTI DA ESCLUDERE: {', '.join(excluded_foods)}")
        
        # Aggiungi alimenti preferiti
        preferred_foods = user_preferences.get("preferred_foods", [])
        if preferred_foods:
            preferences_text.append(f"ALIMENTI PREFERITI: {', '.join(preferred_foods)}")
        
        return "\n".join(preferences_text) if preferences_text else None 