"""
Modulo per il tutorial introduttivo di NutrAICoach.

Contiene le funzioni per mostrare un tutorial interattivo che spiega
le quattro sezioni principali dell'applicazione.
"""

import streamlit as st

# Import del nuovo state manager
from services.state_service import app_state


def show_app_tutorial():
    """
    Mostra il tutorial introduttivo interattivo delle 3 sezioni principali dell'app.
    L'utente deve visitare tutte e tre le sezioni per completare il tutorial.
    
    Returns:
        bool: True se il tutorial è stato completato, False se ancora in corso
    """
    # Ottieni user_id dal nuovo state manager
    user_info = app_state.get_user_info()
    if not user_info:
        return False
    
    user_id = user_info.id
    
    # Controlla se il tutorial è già stato completato per questo utente
    if app_state.is_tutorial_completed(user_id):
        return True
    
    # Ottieni lo stato delle sezioni visitate
    chat_visited = app_state.is_tutorial_section_visited(user_id, 'chat')
    preferences_visited = app_state.is_tutorial_section_visited(user_id, 'preferences')
    plan_visited = app_state.is_tutorial_section_visited(user_id, 'plan')
    
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
            user_id,
            "chat",
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
            user_id,
            "preferences",
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
            user_id,
            "plan",
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


def _display_tutorial_section(emoji, title, subtitle, features, user_id, section, is_visited):
    """
    Mostra una singola sezione del tutorial in formato interattivo e semplificato.
    Utilizza un expander per un'esperienza più fluida, preservando la logica di completamento.
    
    Args:
        emoji: Emoji della sezione
        title: Titolo della sezione
        subtitle: Sottotitolo descrittivo
        features: Lista delle caratteristiche da mostrare
        user_id: ID dell'utente
        section: Nome della sezione (chat, preferences, plan)
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
            app_state.set_tutorial_section_visited(user_id, section, True)
            st.rerun()


def are_all_sections_visited(user_id: str) -> bool:
    """
    Controlla se tutte le sezioni del tutorial sono state visitate.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        bool: True se tutte le sezioni sono state visitate, False altrimenti
    """
    return app_state.are_all_tutorial_sections_visited(user_id)


def is_tutorial_completed(user_id: str) -> bool:
    """
    Controlla se il tutorial è stato completato per un utente specifico.
    
    Args:
        user_id: ID dell'utente
        
    Returns:
        bool: True se il tutorial è completato, False altrimenti
    """
    return app_state.is_tutorial_completed(user_id)


def reset_tutorial(user_id: str):
    """
    Resetta il tutorial per permettere di rivederlo.
    
    Args:
        user_id: ID dell'utente
    """
    app_state.reset_tutorial(user_id)


def check_tutorial_in_chat():
    """
    Controlla se mostrare il tutorial nella sezione Chat.
    
    Returns:
        bool: True se il tutorial deve essere mostrato, False altrimenti
    """
    # Ottieni user_info dal nuovo state manager
    user_info = app_state.get_user_info()
    if not user_info:
        return False
    
    # Mostra il tutorial solo se l'utente è autenticato ma non ha ancora inserito i dati
    if user_info.id and not user_info.età:
        return not app_state.is_tutorial_completed(user_info.id)
    
    return False 