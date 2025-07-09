"""
Modulo per il tutorial introduttivo di NutrAICoach.

Contiene le funzioni per mostrare un tutorial interattivo che spiega
le quattro sezioni principali dell'applicazione.
"""

import streamlit as st


def show_app_tutorial():
    """
    Mostra il tutorial introduttivo interattivo delle 4 sezioni principali dell'app.
    L'utente deve visitare tutte e quattro le sezioni per completare il tutorial.
    
    Returns:
        bool: True se il tutorial è stato completato, False se ancora in corso
    """
    # Controlla se il tutorial è già stato completato per questo utente
    tutorial_key = f"tutorial_completed_{st.session_state.user_info['id']}"
    
    if st.session_state.get(tutorial_key, False):
        return True
    
    # Inizializza le chiavi per tracciare i passaggi del tutorial
    user_id = st.session_state.user_info['id']
    home_visited_key = f"tutorial_home_visited_{user_id}"
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"
    
    # Inizializza i valori se non esistono
    home_visited = st.session_state.get(home_visited_key, False)
    chat_visited = st.session_state.get(chat_visited_key, False)
    preferences_visited = st.session_state.get(preferences_visited_key, False)
    plan_visited = st.session_state.get(plan_visited_key, False)
    
    # Header del tutorial
    st.markdown("---")
    st.markdown("## 🎯 Benvenuto in NutrAICoach!")
    
    # Calcola le sezioni completate per la logica di fine tutorial
    total_sections = 4
    completed_sections = sum([home_visited, chat_visited, preferences_visited, plan_visited])
    
    # Container principale del tutorial
    tutorial_container = st.container()
    
    with tutorial_container:
        # Sezioni interattive organizzate verticalmente
        _display_tutorial_section(
            "💬", "**Chat**", 
            "Due modalità di agente:",
            [
                "Crea/Modifica dieta: L'agente ti guiderà nella realizzazione di una dieta tipo in base alle tue abitudini e necessità",
                "Coaching: L'agente ti guiderà durante il tuo percorso nutrizionale, chiedigli di analizzare il tuo pasto o le alternative!"
            ],
            chat_visited_key,
            chat_visited
        )

        st.markdown("<br>", unsafe_allow_html=True)

        _display_tutorial_section(
            "🏠", "**Home**", 
            "La tua dashboard nutrizionale principale!",
            [
                "Visualizza la dieta del giorno corrente",
            ],
            home_visited_key,
            home_visited
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        
        _display_tutorial_section(
            "⚙️", "**Preferenze**",
            "Personalizza ancor di più la tua esperienza!",
            [
                "Imposta le tue preferenze alimentari",
                "Gestisci allergie e intolleranze"
            ],
            preferences_visited_key,
            preferences_visited
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        _display_tutorial_section(
            "📋", "**Piano Nutrizionale**",
            "Visualizza il tuo piano personalizzato!",
            [
                "Visualizza il piano nutrizionale creato dall'agente",
                "Scarica il PDF del tuo piano settimanale"
            ],
            plan_visited_key,
            plan_visited
        )
        
        # Sezione con suggerimenti di utilizzo
        st.markdown("---")
        st.markdown("### 🚀 **Come utilizzare NutrAICoach:**")
        
        step_cols = st.columns(3)
        with step_cols[0]:
            st.markdown("""
            **1️⃣ Inserisci i tuoi dati**  
            Compila le informazioni nella barra laterale
            """)
        
        with step_cols[1]:
            st.markdown("""
            **2️⃣ Rispondi alle domande**  
            L'agente ti farà alcune domande nutrizionali
            """)
        
        with step_cols[2]:
            st.markdown("""
            **3️⃣ Inizia a chattare!**  
            Ricevi il tuo piano nutrizionale personalizzato
            """)
        
        # Controllo per procedere
        st.markdown("---")
        
        if completed_sections == total_sections:
            # Tutte le sezioni sono state visitate
            st.info("👈 **Compila** i tuoi dati nella barra laterale e clicca su **Inizia** per cominciare!")
            
        else:
            # Non tutte le sezioni sono state visitate
            missing_sections = []
            if not home_visited:
                missing_sections.append("🏠 Home")
            if not chat_visited:
                missing_sections.append("💬 Chat")
            if not preferences_visited:
                missing_sections.append("⚙️ Preferenze")
            if not plan_visited:
                missing_sections.append("📋 Piano Nutrizionale")
            
            st.warning(f"📍 **Per continuare, visita le seguenti sezioni:** {', '.join(missing_sections)}")
            st.info("👆 Clicca sui pulsanti delle sezioni qui sopra per esplorarle!")
    
    return False


def _display_tutorial_section(emoji, title, subtitle, features, session_key, is_visited):
    """
    Mostra una singola sezione del tutorial in formato interattivo e semplificato.
    Utilizza un expander per un'esperienza più fluida, preservando la logica di completamento.
    
    Args:
        emoji: Emoji della sezione
        title: Titolo della sezione
        subtitle: Sottotitolo descrittivo
        features: Lista delle caratteristiche da mostrare
        session_key: Chiave per salvare lo stato nella sessione
        is_visited: Se la sezione è già stata visitata
    """
    label = f"{emoji} {title}"

    with st.expander(label):
        st.markdown(f"**{subtitle}**")
        
        # Mostra le caratteristiche in colonne
        feature_cols = st.columns(2) if len(features) > 2 else [st.container()]
        for i, feature in enumerate(features):
            col_index = i % len(feature_cols) if len(feature_cols) > 1 else 0
            with feature_cols[col_index]:
                st.markdown(f"• {feature}")

        # Se la sezione viene aperta per la prima volta, la marchiamo come visitata
        # e attiviamo un rerun per aggiornare la UI.
        if not is_visited:
            st.session_state[session_key] = True
            st.rerun()


def are_all_sections_visited(user_id: str) -> bool:
    """
    Controlla se tutte le sezioni del tutorial sono state visitate.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        bool: True se tutte le sezioni sono state visitate, False altrimenti
    """
    home_visited_key = f"tutorial_home_visited_{user_id}"
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"
    
    return (st.session_state.get(home_visited_key, False) and
            st.session_state.get(chat_visited_key, False) and
            st.session_state.get(preferences_visited_key, False) and
            st.session_state.get(plan_visited_key, False))


def is_tutorial_completed(user_id: str) -> bool:
    """
    Controlla se il tutorial è stato completato per un utente specifico.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        bool: True se il tutorial è completato, False altrimenti
    """
    tutorial_key = f"tutorial_completed_{user_id}"
    return st.session_state.get(tutorial_key, False)


def reset_tutorial(user_id: str):
    """
    Resetta il tutorial per permettere di rivederlo.
    
    Args:
        user_id: ID dell'utente
    """
    tutorial_key = f"tutorial_completed_{user_id}"
    home_visited_key = f"tutorial_home_visited_{user_id}"
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"

    if tutorial_key in st.session_state:
        del st.session_state[tutorial_key]
    if home_visited_key in st.session_state:
        del st.session_state[home_visited_key]
    if chat_visited_key in st.session_state:
        del st.session_state[chat_visited_key]
    if preferences_visited_key in st.session_state:
        del st.session_state[preferences_visited_key]
    if plan_visited_key in st.session_state:
        del st.session_state[plan_visited_key]


def check_tutorial_in_chat():
    """
    Controlla se mostrare il tutorial nella sezione Chat.
    
    Returns:
        bool: True se il tutorial deve essere mostrato, False altrimenti
    """
    # Mostra il tutorial solo se l'utente è autenticato ma non ha ancora inserito i dati
    if (st.session_state.user_info.get("id") and 
        not st.session_state.user_info.get("età")):
        
        tutorial_key = f"tutorial_completed_{st.session_state.user_info['id']}"
        return not st.session_state.get(tutorial_key, False)
    
    return False 