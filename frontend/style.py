import streamlit as st

def load_css():
    """
    Carica CSS ottimizzato per performance veloci.
    """
    css = """
    /* --- Variabili Colore --- */
    :root {
        --primary-color: #27ae60;
        --background-color: #f7fcf9;
        --card-background-color: #ffffff;
        --text-color-dark: #2c3e50;
        --border-color: #e0e0e0;
        --border-radius: 12px;
    }

    /* --- Stili Base --- */
    body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text-color-dark);
        background-color: var(--background-color) !important;
    }
    
    .main .block-container {
        padding: 2rem 2rem 1rem !important;
    }
    
    /* --- Header App --- */
    .app-header {
        border-bottom: 1px solid rgba(39, 174, 96, 0.2);
        padding: 1.5rem 0;
        margin-bottom: 2rem;
    }

    .app-header-content {
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
    
    /* --- Login --- */
    .login-wrapper {
        max-width: 450px;
        margin: 4rem auto;
    }

    /* --- Bottoni --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        border: none;
        font-weight: 600;
    }
    .stButton > button:hover {
        opacity: 0.85;
    }

    /* --- Chat --- */
    div[data-testid="stChatMessage"]:has([aria-label="assistant avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #f0f2f6;
        border-radius: var(--border-radius);
    }

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stChatMessageContent"] {
        background-color: #e1ffc7;
        border-radius: var(--border-radius);
    }
    
    /* --- Titoli --- */
    h1, h2, h3 {
        color: var(--text-color-dark);
    }
    
    .welcome-header {
        text-align: center;
        margin-bottom: 2rem;
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
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 