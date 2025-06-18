import streamlit as st

def load_css():
    """
    Carica e inietta il CSS personalizzato per un'esperienza elegante, semplice e a tema.
    """
    css = """
    /* --- Google Font Import --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* --- Variabili Colore e Stile --- */
    :root {
        --primary-color: #27ae60;      /* Verde Scuro NutrAICoach */
        --background-color: #f7fcf9;   /* Sfondo Verde Molto Chiaro */
        --card-background-color: #ffffff;
        --text-color-dark: #2c3e50;
        --text-color-light: #555;
        --border-color: #e0e0e0;
        --box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        --border-radius: 12px;
    }

    /* --- Stili Globali e Sfondo a Tema --- */
    body, .stApp {
        font-family: 'Inter', sans-serif;
        color: var(--text-color-dark);
        background-color: var(--background-color) !important;
    }
    
    .main .block-container {
        padding: 2rem;
        padding-top: 1rem !important;
    }
    
    /* --- Header App --- */
    .app-header {
        background: transparent;
        border-bottom: 1px solid rgba(39, 174, 96, 0.2);
        padding: 1.5rem 0;
        margin-bottom: 2rem;
    }

    .app-header-content {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .app-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-color-dark);
        margin: 0;
    }
    
    /* --- Card di Contenuto --- */
    /* Usato per raggruppare sezioni di contenuto */
    .content-card {
        background-color: var(--card-background-color);
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--box-shadow);
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
    }
    
    /* Card più piccole per elementi secondari */
    .card {
        background-color: var(--card-background-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--box-shadow);
        border: 1px solid var(--border-color);
    }
    
    /* Info card speciale */
    .info-card {
        background: linear-gradient(135deg, #eafaf1 0%, #d4f1de 100%);
        border: 1px solid #c3e6cd;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 0.95rem;
    }
    
    /* --- Pagina di Login --- */
    .login-wrapper {
        max-width: 450px;
        margin: 4rem auto;
    }
    
    .login-wrapper .content-card {
        padding: 2.5rem;
        text-align: center;
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* --- Bottoni --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        padding: 0.8rem 1.5rem;
        border: none;
        font-weight: 600;
        transition: opacity 0.3s ease;
    }
    .stButton > button:hover {
        opacity: 0.85;
    }

    /* --- Chat --- */
    /* Messaggio Assistente */
    div[data-testid="stChatMessage"]:has([aria-label="assistant avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #f0f2f6;
        border-radius: var(--border-radius) var(--border-radius) var(--border-radius) 5px;
    }

    /* Messaggio Utente */
    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #e1ffc7;
        border-radius: var(--border-radius) var(--border-radius) 5px var(--border-radius);
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: var(--text-color-dark);
    }
    
    /* --- Stili per titoli speciali --- */
    .welcome-header {
        text-align: center;
        margin-bottom: 2rem;
        background: transparent !important;
    }
    
    .welcome-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-color-dark);
        margin-bottom: 0.5rem;
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
        font-size: 1.1rem;
        margin-bottom: 0;
    }
    
    /* Rimuovi background bianco dalle content-card nelle sezioni interne */
    .content-card:has(.welcome-header) {
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Fix per le tabs di Streamlit - rimuove sfondo bianco */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 