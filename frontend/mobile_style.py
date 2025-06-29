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
    }

    /* --- Stili Base Mobile --- */
    body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text-color-dark);
        background-color: var(--background-color) !important;
        font-size: 16px !important; /* Evita zoom automatico su iOS */
    }
    
    .main .block-container {
        padding: 1rem 0.5rem 0.5rem !important;
        max-width: 100% !important;
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
        margin: 2rem auto;
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

    /* --- Sidebar Mobile --- */
    .css-1d391kg {
        width: 280px !important;
    }
    
    /* --- Input Fields Mobile --- */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        font-size: 16px !important; /* Evita zoom automatico */
        padding: 0.75rem !important;
        border-radius: var(--border-radius) !important;
    }

    /* --- Chat Mobile --- */
    div[data-testid="stChatMessage"] {
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stChatMessage"]:has([aria-label="assistant avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #f0f2f6;
        border-radius: var(--border-radius);
        padding: 1rem !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #e1ffc7;
        border-radius: var(--border-radius);
        padding: 1rem !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }

    /* --- Chat Input Mobile --- */
    .stChatInput > div {
        padding: 0.5rem !important;
    }
    
    .stChatInput input {
        font-size: 16px !important;
        padding: 0.75rem 1rem !important;
        border-radius: var(--border-radius) !important;
        min-height: 44px !important;
    }
    
    /* --- Titoli Mobile --- */
    h1, h2, h3 {
        color: var(--text-color-dark);
        line-height: 1.3 !important;
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
        padding: 1rem !important;
        border-radius: var(--border-radius) !important;
        background-color: var(--card-background-color) !important;
        border: 1px solid var(--border-color) !important;
        margin-bottom: 1rem !important;
    }
    
    /* --- Alert Messages Mobile --- */
    .stAlert {
        margin-bottom: 1rem !important;
        padding: 1rem !important;
        border-radius: var(--border-radius) !important;
        font-size: 0.95rem !important;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 