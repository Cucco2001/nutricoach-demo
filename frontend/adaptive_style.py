import streamlit as st
from frontend.style import load_css
from frontend.mobile_style import load_mobile_css
from frontend.device_detector import (
    get_device_type, is_mobile, force_mobile, force_desktop, 
    auto_detect_device, device_info_display, show_device_selector
)

def load_adaptive_css():
    """
    Funzione principale per caricare CSS adattivo basato sul dispositivo.
    Sostituisce la funzione load_css() originale.
    """
    # Rileva automaticamente il dispositivo
    auto_detect_device()
    
    # Carica gli stili appropriati
    if is_mobile():
        load_mobile_css()
    else:
        load_css()

def show_style_debug_panel():
    """
    Pannello di debug per testare gli stili su diversi dispositivi.
    Visibile solo in modalità debug.
    """
    if not st.session_state.get('debug_styles', False):
        return
    
    with st.sidebar:
        st.write("---")
        st.write("### 🎨 Debug Stili")
        
        # Mostra info dispositivo corrente
        device_info_display()
        
        # Controlli rapidi
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📱 Mobile"):
                force_mobile()
                st.rerun()
        with col2:
            if st.button("🖥️ Desktop"):
                force_desktop()
                st.rerun()

def enable_style_debug():
    """
    Abilita la modalità debug per gli stili.
    """
    st.session_state.debug_styles = True

def disable_style_debug():
    """
    Disabilita la modalità debug per gli stili.
    """
    st.session_state.debug_styles = False

def add_responsive_meta_tags():
    """
    Aggiunge meta tags necessari per il responsive design.
    """
    responsive_meta = """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    """
    st.markdown(responsive_meta, unsafe_allow_html=True)

def add_mobile_optimizations():
    """
    Aggiunge ottimizzazioni specifiche per mobile.
    """
    mobile_optimizations = """
    <style>
        /* Prevenire zoom su input in iOS */
        input[type="text"],
        input[type="email"],
        input[type="password"],
        input[type="number"],
        textarea,
        select {
            font-size: 16px !important;
        }
        
        /* Migliorare la scrolling su iOS */
        body {
            -webkit-overflow-scrolling: touch;
        }
        
        /* Nascondere scrollbar orizzontale su mobile */
        @media screen and (max-width: 768px) {
            body {
                overflow-x: hidden;
            }
        }
        
        /* Ottimizzazioni per touch */
        button, .stButton > button {
            -webkit-tap-highlight-color: rgba(0,0,0,0);
            touch-action: manipulation;
        }
    </style>
    """
    st.markdown(mobile_optimizations, unsafe_allow_html=True)

def setup_responsive_app():
    """
    Configurazione completa per un'app responsive.
    Da chiamare all'inizio dell'app dopo st.set_page_config().
    """
    # Aggiungi meta tags responsive
    add_responsive_meta_tags()
    
    # Carica CSS adattivo
    load_adaptive_css()
    
    # Aggiungi ottimizzazioni mobile se necessario
    if is_mobile():
        add_mobile_optimizations()
    
    # Mostra pannello debug se abilitato
    show_style_debug_panel()

# === FUNZIONI DI COMPATIBILITÀ ===
def load_css_responsive():
    """
    Alias per load_adaptive_css() per compatibilità.
    """
    return load_adaptive_css()

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
    enable_style_debug()
    st.info("🚀 Modalità Mobile-First attivata!")

def desktop_development_mode():
    """
    Attiva modalità desktop per sviluppo.
    """
    force_desktop()
    enable_style_debug()
    st.info("🖥️ Modalità Desktop attivata!")

def production_mode():
    """
    Configurazione per produzione (rilevamento automatico).
    """
    disable_style_debug()
    # Reset forzature manuali se presenti
    if 'force_device_type' in st.session_state:
        del st.session_state.force_device_type 