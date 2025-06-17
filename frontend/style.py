import streamlit as st

def load_css():
    """
    Carica e inietta il CSS personalizzato basato sullo stile di sito_web.
    """
    css = """
    /* --- Google Font Import --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* --- Variabili Colore e Stile --- */
    :root {
        --primary-color: #27ae60;
        --primary-color-light: #2ecc71;
        --text-color-dark: #2c3e50;
        --background-color-light: #f7fcf9;
        --white: #ffffff;
        --light-gray: #f8f9fa;
        --medium-gray: #e9ecef;
        --dark-gray: #666;
        --box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        --box-shadow-hover: 0 15px 40px rgba(0, 0, 0, 0.08);
        --border-radius: 20px;
        --gradient: linear-gradient(135deg, var(--primary-color-light) 0%, var(--primary-color) 100%);
    }

    /* --- Stili Globali --- */
    body {
        font-family: 'Inter', sans-serif;
        color: var(--text-color-dark);
        background-color: var(--background-color-light);
    }

    /* --- Contenitore Principale dell'App --- */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    /* --- Sidebar --- */
    .st-emotion-cache-1jicfl2 {
        background-color: var(--white);
        border-right: 1px solid var(--medium-gray);
    }
    
    /* Titolo Sidebar */
    .st-emotion-cache-1jicfl2 .st-emotion-cache-16txtl3 {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-color-dark);
    }

    /* Radio buttons nella Sidebar */
    .st-emotion-cache-1jicfl2 .st-radio label {
        padding: 0.75rem 1.25rem;
        margin-bottom: 0.5rem;
        border-radius: 10px;
        transition: background-color 0.3s ease, color 0.3s ease;
        font-weight: 500;
    }
    .st-emotion-cache-1jicfl2 .st-radio [aria-selected="true"] label {
        background-color: var(--primary-color);
        color: var(--white);
    }
    .st-emotion-cache-1jicfl2 .st-radio label:hover {
        background-color: var(--medium-gray);
    }

    /* --- Bottoni --- */
    .stButton > button {
        width: 100%;
        padding: 0.9rem 1.8rem;
        border: none;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        background-color: var(--primary-color);
        color: var(--white);
    }
    .stButton > button:hover {
        background-color: var(--primary-color-light);
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(39, 174, 96, 0.3);
    }
    .stButton > button:disabled {
        background-color: #e9ecef;
        color: #666;
        cursor: not-allowed;
    }

    /* --- Titoli e Testi --- */
    h1 {
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--text-color-dark);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    h2 {
        font-size: 2.2rem;
        font-weight: 600;
        color: var(--text-color-dark);
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }

    h3 {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-color-dark);
        margin-bottom: 1rem;
    }

    /* --- Stili per i Componenti Custom --- */

    /* Card generica */
    .card {
        background: var(--white);
        border-radius: var(--border-radius);
        padding: 2.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid var(--medium-gray);
        box-shadow: var(--box-shadow);
        margin-bottom: 2rem;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: var(--box-shadow-hover);
    }

    .section-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        color: var(--text-color-dark);
    }

    .section-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: var(--dark-gray);
        margin-bottom: 3rem;
    }
    
    .gradient-text {
        background: var(--gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Stile per i messaggi della chat */
    [data-testid="chat-message-container"] {
        border-radius: 15px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* Messaggio dell'assistente */
     [data-testid="chat-message-container"] [data-testid="stChatMessageContent"] {
        background-color: var(--white);
        box-shadow: var(--box-shadow);
    }

    /* Messaggio dell'utente */
    [data-testid="chat-message-container"] [data-testid="stChatMessageContent"] {
        background-color: #eafaf1; /* Verde molto chiaro */
    }

    /* Input della chat */
    .st-emotion-cache-1c7y2kd {
        border-top: 1px solid var(--medium-gray);
    }
    
    /* --- Stili specifici per l'app --- */
    
    /* Form di login */
    .login-container {
        max-width: 450px;
        margin: 4rem auto;
        padding: 3rem;
        background: var(--white);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        text-align: center;
    }

    /* Messaggio di benvenuto */
    .welcome-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Logo nel header */
    .welcome-header img {
        height: 80px;
        margin-bottom: 1rem;
    }

    .welcome-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 