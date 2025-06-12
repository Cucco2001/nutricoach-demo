"""
Modulo per il tutorial introduttivo di NutriCoach.

Contiene le funzioni per mostrare un tutorial interattivo che spiega
le quattro sezioni principali dell'applicazione.
"""

import streamlit as st


def show_app_tutorial():
    """
    Mostra il tutorial introduttivo delle 4 sezioni principali dell'app.
    
    Returns:
        bool: True se il tutorial è stato completato, False se ancora in corso
    """
    # Controlla se il tutorial è già stato completato per questo utente
    tutorial_key = f"tutorial_completed_{st.session_state.user_info['id']}"
    
    if st.session_state.get(tutorial_key, False):
        return True
    
    # Header del tutorial
    st.markdown("---")
    st.markdown("## 🎯 Benvenuto in NutriCoach!")
    st.markdown("### Prima di iniziare, lascia che ti spieghi come funziona l'app")
    
    # Container principale del tutorial
    tutorial_container = st.container()
    
    with tutorial_container:
        # Introduzione
        st.markdown("""
        **NutriCoach** è il tuo assistente nutrizionale personale! 🥗  
        L'app è organizzata in **4 sezioni principali** che trovi nel menu a sinistra.
        """)
        
        # Sezioni con emoji e descrizioni
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 💬 **Chat**
            **Qui è dove avviene la magia!**
            - Chatta direttamente con il tuo assistente nutrizionale AI
            - Ricevi consigli personalizzati e piani alimentari
            - Fai domande su nutrizione, ricette e obiettivi
            - L'agente ti guiderà passo dopo passo
            
            ### 📊 **Progressi**
            **Traccia i tuoi risultati!**
            - Monitora i tuoi progressi nel tempo
            - Visualizza grafici del peso e misurazioni
            - Tieni traccia degli obiettivi raggiunti
            - Confronta i risultati settimana per settimana
            """)
        
        with col2:
            st.markdown("""
            ### ⚙️ **Preferenze**
            **Personalizza la tua esperienza!**
            - Imposta le tue preferenze alimentari
            - Gestisci allergie e intolleranze
            - Scegli i tuoi cibi preferiti e quelli da evitare
            - Modifica le impostazioni quando necessario
            
            ### 📋 **Piano Nutrizionale**
            **Il tuo piano personalizzato!**
            - Visualizza il piano nutrizionale creato dall'agente
            - Scarica il PDF del tuo piano settimanale
            - Accedi a tutti i dettagli nutrizionali
            - Stampa le ricette e le porzioni
            """)
        
        # Sezione con suggerimenti
        st.markdown("---")
        st.markdown("### 🚀 **Per iniziare:**")
        
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
        
        # Note aggiuntive
        st.markdown("---")
        st.info("""
        💡 **Suggerimento**: Puoi sempre tornare a questa spiegazione dal menu *Preferenze* > *Mostra Tutorial*
        """)
        
        # Bottoni di azione
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            if st.button("🎯 Ho capito, iniziamo!", type="primary", use_container_width=True):
                # Segna il tutorial come completato
                st.session_state[tutorial_key] = True
                st.rerun()
    
    return False


def reset_tutorial(user_id: str):
    """
    Resetta il tutorial per permettere di rivederlo.
    
    Args:
        user_id: ID dell'utente
    """
    tutorial_key = f"tutorial_completed_{user_id}"
    if tutorial_key in st.session_state:
        del st.session_state[tutorial_key]


def show_tutorial_button_in_preferences():
    """
    Mostra un bottone nelle preferenze per rivedere il tutorial.
    """
    st.markdown("---")
    st.markdown("### 🎯 Tutorial")
    
    if st.button("📖 Rivedi il tutorial dell'app", help="Mostra di nuovo la spiegazione delle 4 sezioni"):
        reset_tutorial(st.session_state.user_info['id'])
        st.success("Tutorial resettato! Vai alla sezione Chat per rivederlo.")
        st.rerun()


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