import streamlit as st

def load_mobile_css():
    """
    Carica CSS ottimizzato per dispositivi mobile con layout semplificato.
    """
    css = """
    /* --- Variabili Colore Mobile --- */
    :root {
        --primary-color: #27ae60;
        --background-color: #f7fcf9;
        --card-background-color: #ffffff;
        --text-color-dark: #2c3e50;
        --border-color: #e0e0e0;
        --border-radius: 8px;
        --mobile-padding: 1rem;
        
        /* Colori Verde come Bottoni (stesso del logout) Mobile */
        --meal-green-dark: #27ae60;
        --meal-green-light: #2ecc71;
        --stat-green-1: #27ae60;
        --stat-green-2: #2ecc71;
        --stat-green-3: #58d68d;
        --stat-green-4: #52c41a;
    }

    /* --- Stili Base Mobile --- */
    body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text-color-dark);
        background-color: var(--background-color) !important;
        font-size: 16px !important; /* Evita zoom automatico su iOS */
    }
    
    .main .block-container {
        /* Padding ridotto per un look più pulito, soprattutto in chat */
        padding: 0.5rem 0.5rem 6rem !important; /* Aggiunto padding-bottom per l'input fisso */
        max-width: 100% !important;
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    
    /* --- Header App Mobile --- */
    .app-header {
        border-bottom: 1px solid rgba(39, 174, 96, 0.2);
        padding: 1rem 0;
        margin-bottom: 1rem;
    }

    .app-header-content {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        text-align: center;
    }

    .app-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-color-dark);
        margin: 0;
        line-height: 1.2;
    }
    
    /* --- Login Mobile --- */
    .login-wrapper {
        max-width: 100%;
        margin: 1rem auto;
        padding: 0 var(--mobile-padding);
    }

    /* --- Bottoni Mobile --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        border: none;
        font-weight: 600;
        width: 100% !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        min-height: 44px !important; /* Touch target iOS */
    }
    .stButton > button:hover {
        opacity: 0.85;
    }

    /* Stile specifico per bottone submit nel form per sovrascrivere il default */
    .stForm .stButton > button {
        background-color: var(--primary-color);
        color: white;
    }

    /* --- Sidebar Mobile --- */
    /* La regola con selettore generato è stata rimossa perché instabile */
    
    /* --- Input Fields Mobile --- */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        font-size: 16px !important; /* Evita zoom automatico */
        padding: 0.75rem !important;
        border-radius: var(--border-radius) !important;
    }

    /* --- CHAT MIGLIORATA PER MOBILE --- */
    
    /* Contenitore dei messaggi */
    div[data-testid="stChatMessage"] {
        margin-bottom: 0.75rem !important;
        padding: 0 0.25rem; /* Leggero padding laterale */
    }
    
    /* Messaggi dell'assistente */
    div[data-testid="stChatMessage"]:has([aria-label="assistant avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #f0f2f6;
        border-radius: 20px; /* Bordi più arrotondati */
        border-bottom-left-radius: 5px; /* Angolo "appuntito" */
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important; /* Font più leggibile */
        line-height: 1.5 !important;
    }

    /* Messaggi dell'utente */
    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #dcf8c6; /* Verde più "WhatsApp-like" */
        border-radius: 20px; /* Bordi più arrotondati */
        border-bottom-right-radius: 5px; /* Angolo "appuntito" */
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important; /* Font più leggibile */
        line-height: 1.5 !important;
    }

    /* --- INPUT CHAT FISSO IN BASSO --- */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: var(--background-color);
        padding: 1rem 0.5rem !important;
        border-top: 1px solid var(--border-color);
        z-index: 1000;
    }
    
    .stChatInput > div {
        background-color: white;
        border-radius: 20px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stChatInput input {
        font-size: 16px !important;
        padding: 0.75rem 1rem !important;
        border-radius: 20px !important;
        border: none !important;
        min-height: 44px;
    }
    
    /* --- Titoli Mobile --- */
    h1, h2, h3 {
        color: var(--text-color-dark);
        line-height: 1.4;
    }
    
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        font-size: 1.4rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    h3 {
        font-size: 1.2rem !important;
        margin-bottom: 0.6rem !important;
    }
    
    .welcome-header {
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 0 var(--mobile-padding);
    }
    
    .welcome-header h1 {
        font-size: 2rem !important;
        font-weight: 700;
        color: var(--text-color-dark);
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    .section-subtitle {
        color: #666;
        font-size: 1rem !important;
        margin-bottom: 0;
        line-height: 1.4;
    }

    /* Le vecchie regole per la chat sono state rimosse per pulizia.
       Quelle nuove sono state applicate sopra. */

    /* --- Cards Mobile --- */
    .stExpander {
        border-radius: var(--border-radius) !important;
        margin-bottom: 1rem !important;
    }
    
    /* --- Radio Buttons Mobile --- */
    .stRadio > div {
        gap: 0.5rem !important;
    }
    
    .stRadio label {
        font-size: 1rem !important;
        padding: 0.5rem 0 !important;
        min-height: 44px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* --- Columns Mobile - Stack verticalmente --- */
    .row-widget.stColumns {
        flex-direction: column !important;
        gap: 1rem !important;
    }
    
    .column {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    /* --- Tabelle Mobile --- */
    .stDataFrame {
        overflow-x: auto !important;
    }
    
    table {
        font-size: 0.9rem !important;
    }
    
    /* --- Metriche Mobile --- */
    .metric-container {
        text-align: center !important;
        padding: 1rem !important;
    }
    
    /* --- Scrollbar Mobile --- */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 2px;
    }
    
    /* --- Loading States Mobile --- */
    .stSpinner {
        display: flex !important;
        justify-content: center !important;
        padding: 2rem !important;
    }
    
    /* --- Form Elements Mobile --- */
    .stForm {
        padding: 0 !important;
        background-color: transparent !important;
        border: none !important;
        margin-bottom: 1rem !important;
    }
    
    /* --- Alert Messages Mobile --- */
    .stAlert {
        margin-bottom: 1rem !important;
        padding: 1rem !important;
        border-radius: var(--border-radius) !important;
        font-size: 0.95rem !important;
    }

    /* Rendi la sidebar (colonna sinistra) più stretta */
    section[data-testid="stSidebar"] {
        width: 200px !important;
        min-width: 200px !important;
    }
    
    /* --- HOME STYLES MOBILE --- */
    .home-welcome-gradient {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 8px 0;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.12);
    }
    
    .home-welcome-gradient h1 {
        font-size: 1.5rem !important;
        margin: 0 0 6px 0 !important;
    }
    
    .home-welcome-gradient p {
        font-size: 0.9rem !important;
        margin: 3px 0 !important;
    }
    
    .home-section-card {
        background: white;
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid var(--border-color);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .home-section-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.12);
    }
    
    /* Card specifiche per le preferenze (Mobile) */
    .preferences-card {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid var(--border-color);
        color: white;
        height: 100%;
    }

    .preferences-card h3 {
        color: white !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.5);
        padding-bottom: 6px;
        margin-top: 0;
    }
    
    .home-meal-card {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 8px 12px;
        border-radius: 8px;
        margin: 8px 0;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .home-meal-card h4 {
        font-size: 1rem !important;
        margin: 0 !important;
    }
    
    .home-stat-card {
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        color: white;
        margin: 2px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .home-stat-card h4 {
        font-size: 0.9rem !important;
        margin: 0 0 3px 0 !important;
    }
    
    .home-stat-card p {
        font-size: 0.9rem !important;
        margin: 0 !important;
    }
    
    .home-stat-card:hover {
        transform: scale(1.03);
    }
    
    .home-stat-card.tdee {
        background: var(--stat-green-1);
    }
    
    .home-stat-card.proteine {
        background: var(--stat-green-2);
    }
    
    .home-stat-card.carboidrati {
        background: var(--stat-green-3);
    }
    
    .home-stat-card.grassi {
        background: var(--stat-green-4);
    }
    
    .home-current-day {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 12px;
        border-radius: 10px;
        margin: 12px 0;
        color: white;
        text-align: center;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
    }
    
    .home-processing {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 12px 0;
        color: white;
        text-align: center;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
    }
    
    .home-no-data {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 12px 0;
        color: white;
        text-align: center;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
    }
    
    .home-ingredient-list {
        font-size: 0.8em;
        margin: 6px 0;
        line-height: 1.3;
    }
    
    .home-meal-separator {
        margin: 8px 0;
        border: 1px solid #e0e0e0;
        opacity: 0.6;
    }
    
    /* Responsive Navigation mobile */
    .home-nav-description {
        flex-direction: column;
        gap: 10px;
    }
    
    .home-nav-item {
        padding: 5px 0;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 