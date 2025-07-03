import streamlit as st
import re
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

# Import del nuovo state manager
from services.state_service import app_state

def detect_device_type():
    """
    Funzione per rilevare il device type SOLO all'inizializzazione.
    Restituisce il device type rilevato senza stampare messaggi ripetuti.
    """
    return get_device_type()

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



def get_device_type():
    """
    Rileva il tipo di dispositivo per ogni utente individualmente.
    """
    # Ottieni l'ID utente per salvare device_type specifico per utente
    user_info = app_state.get_user_info()
    user_id = user_info.id if user_info else 'anonymous'
    
    # Chiave specifica per utente
    device_key = f'device_type_{user_id}'
    
    # Se già rilevato per questo utente, restituisci sempre quello
    device_type = app_state.get(device_key)
    if device_type:
        print(f"📱 [DEVICE] Cache per utente {user_id}: {device_type}")
        return device_type

    # Altrimenti, rileva e salva per questo utente
    width = streamlit_js_eval(js_expressions='window.innerWidth', key="WIDTH", want_output=True)
    print(f"📏 [DEVICE] Width rilevata per utente {user_id}: {width}")
    if width is None:
        print("⚠️ [DEVICE] Width è None, default desktop")
        return 'desktop'  # Default sicuro

    device_type = 'desktop' if width > 768 else 'mobile'
    print(f"🎯 [DEVICE] Utente {user_id}: {width} > 768? {width > 768} → {device_type}")
    app_state.set(device_key, device_type)
    return device_type

def is_mobile():
    """Restituisce True se il dispositivo è considerato mobile per l'utente corrente."""
    return get_device_type() == 'mobile'

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
        app_state.set_force_device_type(selected_device)
        app_state.set_device_choice_made(True)
        st.rerun()
    
    return selected_device

def device_info_display():
    """
    Mostra informazioni sul dispositivo attualmente rilevato.
    """
    device_type = get_device_type()
    is_forced = app_state.get_force_device_type() is not None
    
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

    # Salva il tipo di dispositivo rilevato
    app_state.set_device_type(device_type)

def reset_device_detection():
    """
    Resetta la rilevazione del dispositivo, forzando un nuovo rilevamento.
    """
    # Pulisci dallo state manager
    app_state.delete('device_type')
    app_state.delete('device_detection_done')
    app_state.set_force_device_type('')
    app_state.set_device_choice_made(False)
    
    print("🔄 Rilevazione dispositivo resettata") 