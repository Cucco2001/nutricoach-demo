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
        
        /* Colori Verde come Bottoni (stesso del logout) */
        --meal-green-dark: #27ae60;
        --meal-green-light: #2ecc71;
        --stat-green-1: #27ae60;
        --stat-green-2: #2ecc71;
        --stat-green-3: #58d68d;
        --stat-green-4: #52c41a;
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
        margin: 2rem auto;
    }

    /* --- Form --- */
    .stForm {
        background: transparent;
        border: none;
        padding: 0;
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
    
    /* --- HOME STYLES --- */
    .home-welcome-gradient {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .home-welcome-gradient h1 {
        font-size: 1.8rem !important;
        margin: 0 0 8px 0 !important;
    }
    
    .home-welcome-gradient p {
        font-size: 1rem !important;
        margin: 5px 0 !important;
    }
    
    .home-section-card {
        background: white;
        padding: 15px;
        border-radius: 12px;
        margin: 12px 0;
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        border: 1px solid var(--border-color);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .home-section-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .home-meal-card {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 10px 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .home-meal-card h4 {
        font-size: 1.1rem !important;
        margin: 0 !important;
    }
    
    .home-stat-card {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin: 3px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .home-stat-card h4 {
        font-size: 1rem !important;
        margin: 0 0 5px 0 !important;
    }
    
    .home-stat-card p {
        font-size: 1rem !important;
        margin: 0 !important;
    }
    
    .home-stat-card:hover {
        transform: scale(1.05);
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
        padding: 15px;
        border-radius: 12px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.12);
    }
    
    .home-processing {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        padding: 18px;
        border-radius: 12px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.12);
    }
    
    .home-no-data {
        background: linear-gradient(135deg, var(--meal-green-dark) 0%, var(--meal-green-light) 100%);
        padding: 18px;
        border-radius: 12px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.12);
    }
    
    .home-ingredient-list {
        font-size: 0.85em;
        margin: 8px 0;
        line-height: 1.3;
    }
    
    .home-meal-separator {
        margin: 10px 0;
        border: 1px solid #e0e0e0;
        opacity: 0.6;
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True) 