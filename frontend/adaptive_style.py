import streamlit as st
from frontend.style import load_css
from frontend.mobile_style import load_mobile_css
from frontend.device_detector import get_device_type, is_mobile

def setup_responsive_app():
    """
    Funzione principale che rileva il dispositivo in modo affidabile
    e carica il CSS corretto. Non mostra più il pannello di debug.
    """
    device_type = get_device_type()

    if is_mobile():
        load_mobile_css()
    else:
        load_css()
    
    if is_mobile():
        add_mobile_optimizations()

def add_responsive_meta_tags():
    """Aggiunge meta tags essenziali per il responsive design."""
    st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0">', unsafe_allow_html=True)

def add_mobile_optimizations():
    """Aggiunge ottimizzazioni CSS specifiche per mobile per una migliore UX."""
    st.markdown("""
    <style>
        /* Prevenire zoom su input in iOS */
        input[type="text"], textarea, select {
            font-size: 16px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# === FUNZIONI DI COMPATIBILITÀ ===
def load_css_responsive():
    """
    Alias per setup_responsive_app() per compatibilità.
    """
    return setup_responsive_app()

def is_mobile_device():
    """
    Alias per is_mobile() per compatibilità.
    """
    return is_mobile()

# === CONFIGURAZIONI PRESET ===
def mobile_first_mode():
    """
    Attiva modalità mobile-first per sviluppo.
    """
    force_mobile()
    st.info("🚀 Modalità Mobile-First attivata!")

def desktop_development_mode():
    """
    Attiva modalità desktop per sviluppo.
    """
    force_desktop()
    st.info("🖥️ Modalità Desktop attivata!")

def production_mode():
    """
    Configurazione per produzione (rilevamento automatico).
    """
    # Reset forzature manuali se presenti
    from services.state_service import app_state
    app_state.delete('force_device_type') 