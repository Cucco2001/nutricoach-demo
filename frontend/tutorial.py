"""
Modulo per il tutorial introduttivo di NutrAICoach.

Contiene le funzioni per mostrare un tutorial interattivo che spiega
le quattro sezioni principali dell'applicazione.
"""

import streamlit as st


def show_app_tutorial():
    """
    Mostra il tutorial introduttivo interattivo delle 3 sezioni principali dell'app.
    L'utente deve visitare tutte e tre le sezioni per completare il tutorial.
    
    Returns:
        bool: True se il tutorial è stato completato, False se ancora in corso
    """
    # Controlla se il tutorial è già stato completato per questo utente
    tutorial_key = f"tutorial_completed_{st.session_state.user_info['id']}"
    
    if st.session_state.get(tutorial_key, False):
        return True
    
    # Inizializza le chiavi per tracciare i passaggi del tutorial
    user_id = st.session_state.user_info['id']
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"
    
    # Inizializza i valori se non esistono
    chat_visited = st.session_state.get(chat_visited_key, False)
    preferences_visited = st.session_state.get(preferences_visited_key, False)
    plan_visited = st.session_state.get(plan_visited_key, False)
    
    # Header del tutorial
    st.markdown("---")
    st.markdown("## 🎯 Benvenuto in NutrAICoach!")
    st.markdown("### Scopri le funzionalità dell'app visitando ogni sezione")
    
    # Calcola le sezioni completate per la logica di fine tutorial
    total_sections = 3
    completed_sections = sum([chat_visited, preferences_visited, plan_visited])
    
    # Container principale del tutorial
    tutorial_container = st.container()
    
    with tutorial_container:
        # Introduzione
        st.markdown("""
        **NutrAICoach** è il tuo assistente nutrizionale personale! 🥗  
        Per completare il tutorial, **esplora tutte e 3 le sezioni** cliccando sui pulsanti qui sotto.
        Ogni sezione si aprirà con informazioni dettagliate.
        """)
        
        # Sezioni interattive organizzate verticalmente
        _display_tutorial_section(
            "💬", "Chat", 
            "L'agente ti guiderà nella realizzazione di un giorno di dieta tipo in base ai tuoi suggerimenti e spunti. Successivamente, in base alle tue preferenze, genererà un piano nutrizionale settimanale adatto a te!",
            [
                "Chatta direttamente con il tuo assistente nutrizionale AI",
                "Ricevi consigli personalizzati e piani alimentari",
                "Fai domande su nutrizione, ricette e obiettivi",
                "L'agente ti guiderà passo dopo passo"
            ],
            chat_visited_key,
            chat_visited
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        _display_tutorial_section(
            "⚙️", "Preferenze",
            "Personalizza ancor di più la tua esperienza!",
            [
                "Imposta le tue preferenze alimentari",
                "Gestisci allergie e intolleranze", 
                "Scegli i tuoi cibi preferiti e quelli da evitare",
                "Modifica le impostazioni quando necessario"
            ],
            preferences_visited_key,
            preferences_visited
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        _display_tutorial_section(
            "📋", "Piano Nutrizionale",
            "Visualizza il tuo piano personalizzato!",
            [
                "Visualizza il piano nutrizionale creato dall'agente",
                "Scarica il PDF del tuo piano settimanale",
                "Accedi a tutti i dettagli nutrizionali",
                "Stampa le ricette e le porzioni"
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
            st.info("👈 Ora puoi compilare i tuoi dati nella barra laterale e cliccare su **Inizia** per cominciare!")
            
        else:
            # Non tutte le sezioni sono state visitate
            missing_sections = []
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
    if is_visited:
        label += " ✅"

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
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"
    
    return (st.session_state.get(chat_visited_key, False) and
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
    chat_visited_key = f"tutorial_chat_visited_{user_id}"
    preferences_visited_key = f"tutorial_preferences_visited_{user_id}"
    plan_visited_key = f"tutorial_plan_visited_{user_id}"

    if tutorial_key in st.session_state:
        del st.session_state[tutorial_key]
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