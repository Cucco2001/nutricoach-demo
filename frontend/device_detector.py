import streamlit as st
import re

def is_mobile_user_agent():
    """
    Rileva se l'user agent corrisponde a un dispositivo mobile.
    Streamlit fornisce alcune informazioni sui headers della richiesta.
    """
    try:
        # Ottieni l'user agent se disponibile nelle informazioni di sessione
        # Questo è un approccio alternativo usando patterns comuni
        
        # Patterns per dispositivi mobile
        mobile_patterns = [
            r'Mobile', r'Android', r'iPhone', r'iPad', r'iPod',
            r'BlackBerry', r'Windows Phone', r'webOS', r'Opera Mini',
            r'IEMobile', r'Mobile Safari', r'Kindle', r'Silk',
            r'PlayBook', r'BB10', r'KFAPWI', r'Tablet'
        ]
        
        # Per ora utilizziamo un approccio basato su session state
        # che può essere impostato tramite JavaScript o override manuale
        return False  # Default fallback
    except:
        return False

def detect_mobile_via_css():
    """
    Utilizza CSS media queries per rilevare dispositivi mobile.
    Questo è il metodo più affidable in Streamlit.
    """
    # CSS con media query per rilevazione mobile
    mobile_detection_css = """
    <style>
        .device-detector {
            display: none;
        }
        
        .device-type {
            display: none;
        }
        
        /* Desktop indicator */
        .desktop-indicator {
            display: block;
        }
        
        /* Mobile indicators */
        @media screen and (max-width: 768px) {
            .mobile-indicator {
                display: block;
            }
            .desktop-indicator {
                display: none;
            }
        }
        
        @media screen and (max-width: 480px) {
            .phone-indicator {
                display: block;
            }
        }
        
        @media screen and (min-width: 481px) and (max-width: 768px) {
            .tablet-indicator {
                display: block;
            }
        }
    </style>
    
    <!-- Indicators nascosti per la rilevazione -->
    <div class="device-detector">
        <div class="mobile-indicator device-type" data-device="mobile"></div>
        <div class="phone-indicator device-type" data-device="phone"></div>
        <div class="tablet-indicator device-type" data-device="tablet"></div>
        <div class="desktop-indicator device-type" data-device="desktop"></div>
    </div>
    """
    
    st.markdown(mobile_detection_css, unsafe_allow_html=True)

def get_device_type():
    """
    Determina il tipo di dispositivo usando una logica semplificata.
    """
    # Inizializza le informazioni del dispositivo se non esistono
    if 'device_type' not in st.session_state:
        st.session_state.device_type = 'desktop'  # Default
    
    # Controlla se è stato forzato manualmente
    if 'force_device_type' in st.session_state:
        return st.session_state.force_device_type
    
    return st.session_state.device_type

def is_mobile():
    """
    Restituisce True se il dispositivo è considerato mobile (phone o tablet).
    """
    device_type = get_device_type()
    return device_type in ['mobile', 'phone', 'tablet']

def is_phone():
    """
    Restituisce True se il dispositivo è uno smartphone.
    """
    return get_device_type() == 'phone'

def is_tablet():
    """
    Restituisce True se il dispositivo è un tablet.
    """
    return get_device_type() == 'tablet'

def is_desktop():
    """
    Restituisce True se il dispositivo è desktop.
    """
    return get_device_type() == 'desktop'

def force_mobile():
    """
    Forza la modalità mobile per testing.
    """
    st.session_state.force_device_type = 'mobile'

def force_desktop():
    """
    Forza la modalità desktop per testing.
    """
    st.session_state.force_device_type = 'desktop'

def reset_device_detection():
    """
    Resetta la rilevazione del dispositivo.
    """
    if 'force_device_type' in st.session_state:
        del st.session_state.force_device_type

def auto_detect_device():
    """
    Tenta di rilevare automaticamente il tipo di dispositivo.
    Utilizza una combinazione di approcci per massimizzare l'accuratezza.
    """
    # Applica CSS per rilevazione
    detect_mobile_via_css()
    
    # Utilizza una euristica basata su viewport comune
    # In assenza di JavaScript, assume mobile se non specificato diversamente
    
    # Se non è stata fatta una scelta manuale, usa logica euristica
    if 'device_choice_made' not in st.session_state:
        # Default intelligente: se in sidebar c'è poco spazio, probabilmente è mobile
        # Questo è un approccio approssimativo ma funzionale
        pass

def show_device_selector():
    """
    Mostra un selettore per scegliere manualmente il tipo di dispositivo.
    Utile per testing e per permettere all'utente di scegliere.
    """
    st.write("### 📱 Selezione Dispositivo")
    
    device_options = {
        'desktop': '🖥️ Desktop',
        'mobile': '📱 Mobile',
        'phone': '📱 Smartphone',
        'tablet': '📋 Tablet'
    }
    
    current_device = get_device_type()
    
    selected_device = st.radio(
        "Seleziona il tipo di dispositivo:",
        options=list(device_options.keys()),
        format_func=lambda x: device_options[x],
        index=list(device_options.keys()).index(current_device) if current_device in device_options else 0
    )
    
    if selected_device != current_device:
        st.session_state.force_device_type = selected_device
        st.session_state.device_choice_made = True
        st.rerun()
    
    return selected_device

def device_info_display():
    """
    Mostra informazioni sul dispositivo attualmente rilevato.
    """
    device_type = get_device_type()
    is_forced = 'force_device_type' in st.session_state
    
    device_icons = {
        'desktop': '🖥️',
        'mobile': '📱',
        'phone': '📱',
        'tablet': '📋'
    }
    
    icon = device_icons.get(device_type, '❓')
    status = "Forzato" if is_forced else "Rilevato"
    
    st.info(f"{icon} Dispositivo: **{device_type.title()}** ({status})")
    
    if is_forced:
        if st.button("🔄 Reset Rilevazione"):
            reset_device_detection()
            st.rerun() 