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
        --primary-color: #27ae60;      /* Verde Scuro Nutricoach */
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

    /* --- Pagina di Login --- */
    .login-wrapper {
        max-width: 450px;
        margin: 4rem auto;
    }
    
    .login-wrapper .content-card {
        padding: 2.5rem;
        text-align: center;
    }

    /* --- Bottoni --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: var(--card-background-color);
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
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 