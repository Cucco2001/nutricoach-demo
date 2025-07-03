"""
Modulo per l'interfaccia utente della chat.

Contiene tutte le funzioni per gestire l'interfaccia della chat,
inclusa la sidebar delle informazioni utente, la visualizzazione
dei messaggi e l'input dell'utente.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.handle_nutrition_questions import handle_nutrition_questions
from frontend.handle_initial_info import handle_user_info_form, handle_user_info_display
from frontend.buttons import handle_restart_button
from frontend.tutorial import show_app_tutorial, is_tutorial_completed, are_all_sections_visited
from agent.prompts import get_initial_prompt
from services.token_cost_service import TokenCostTracker

# Import del nuovo state manager
from services.state_service import app_state



def render_user_sidebar():
    """
    Renderizza la sidebar con le informazioni dell'utente.
    
    Gestisce il form per inserire le informazioni iniziali o
    mostra le informazioni esistenti con il pulsante ricomincia.
    """
    with st.sidebar:
        st.markdown("## 👤 Le Tue Info", unsafe_allow_html=True)
        
        # Ottieni user_info dal nuovo state manager
        user_info = app_state.get_user_info()
        if not user_info:
            st.warning("⚠️ Nessun utente autenticato.")
            return
        
        # Se il tutorial non è completato, mostra sempre il form anche se ci sono dati salvati
        tutorial_completed = is_tutorial_completed(user_info.id)
        
        if not user_info.età or not tutorial_completed:
            # Usa il modulo frontend per gestire il form delle informazioni utente
            user_data_manager = app_state.get_user_data_manager()
            chat_manager = app_state.get_chat_manager()
            
            if user_data_manager and chat_manager:
                handle_user_info_form(
                    user_id=user_info.id,
                    user_data_manager=user_data_manager,
                    create_new_thread_func=chat_manager.create_new_thread
                )
        else:
            # Usa il modulo frontend per mostrare le informazioni utente
            handle_user_info_display(user_info.__dict__)
            
            # Usa il modulo frontend per gestire il bottone "Ricomincia"
            user_data_manager = app_state.get_user_data_manager()
            deepseek_manager = app_state.get_deepseek_manager()
            chat_manager = app_state.get_chat_manager()
            
            if user_data_manager and deepseek_manager and chat_manager:
                handle_restart_button(
                    user_data_manager=user_data_manager,
                    deepseek_manager=deepseek_manager,
                    create_new_thread_func=chat_manager.create_new_thread
                )
            



def handle_nutrition_questions_flow():
    """
    Gestisce il flusso delle domande nutrizionali.
    
    Returns:
        bool: True se ci sono ancora domande da gestire, False altrimenti
    """
    current_question = app_state.get_current_question()
    user_info = app_state.get_user_info()
    
    if current_question < len(NUTRITION_QUESTIONS):
        # Usa il modulo frontend per gestire le domande nutrizionali
        has_more_questions = handle_nutrition_questions(
            user_info=user_info.__dict__ if user_info else {},
            user_id=user_info.id if user_info else "",
            user_data_manager=app_state.get_user_data_manager()
        )
        
        # Se non ci sono più domande, passa alla chat
        if not has_more_questions:
            st.rerun()
        
        return True
    
    return False


def initialize_chat_history():
    """
    Inizializza la chat history caricando messaggi esistenti o creando il prompt iniziale.
    """
    # Il token tracker è ora gestito in initialization.py
    token_tracker = app_state.get_token_tracker()
    if not token_tracker:
        from services.token_cost_service import TokenCostTracker
        token_tracker = TokenCostTracker(model="gpt-4")
        app_state.set_token_tracker(token_tracker)
    
    messages = app_state.get_messages()
    user_info = app_state.get_user_info()
    
    if not messages:
        user_data_manager = app_state.get_user_data_manager()
        if not user_data_manager:
            st.error("❌ User data manager non disponibile")
            return
            
        chat_history = user_data_manager.get_chat_history(user_info.id)
        if chat_history:
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in chat_history
            ]
            app_state.set_messages(messages)
            # Traccia i messaggi esistenti per avere statistiche accurate
            for msg in messages:
                token_tracker.track_message(msg["role"], msg["content"])
        else:
            # Se non c'è history, invia il prompt iniziale
            nutrition_answers = app_state.get_nutrition_answers()
            initial_prompt = get_initial_prompt(
                user_info=user_info.__dict__,
                nutrition_answers=nutrition_answers,
                user_preferences=user_info.preferences or {}
            )
            
            # Traccia il prompt iniziale come input
            token_tracker.track_message("user", initial_prompt)
            
            # Crea un nuovo thread solo se non esiste già
            chat_manager = app_state.get_chat_manager()
            if not chat_manager:
                st.error("❌ Chat manager non disponibile")
                return
                
            thread_id = app_state.get_thread_id()
            if not thread_id:
                st.info("🔄 Inizializzazione thread di conversazione...")
                thread_id = chat_manager.create_new_thread()
                if not thread_id:
                    st.error("❌ Impossibile creare thread di conversazione")
                    return
            
            # Imposta lo stato di generazione prima di chiamare l'agente
            app_state.set_agent_generating(True)
            
            try:
                # Invia il prompt iniziale usando il manager
                response = chat_manager.chat_with_assistant(initial_prompt)
                app_state.add_message("assistant", response)
                
                # Traccia la risposta dell'assistente
                token_tracker.track_message("assistant", response)
                
                # Salva il messaggio nella history
                user_data_manager.save_chat_message(
                    user_info.id,
                    "assistant",
                    response
                )
                
                # Rimuovi lo stato di generazione dopo aver completato tutto
                app_state.set_agent_generating(False)
                
            except Exception as e:
                # In caso di errore, assicurati di resettare lo stato
                app_state.set_agent_generating(False)
                raise e
            
            st.rerun()


def display_chat_messages():
    """
    Mostra la cronologia dei messaggi della chat.
    """
    messages = app_state.get_messages()
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def handle_user_input():
    """
    Gestisce l'input dell'utente e la generazione della risposta.
    """
    # Se l'agente sta generando, mostra un messaggio informativo invece del campo di input
    if app_state.is_agent_generating():
        user_input = None
    else:
        # CSS per ridurre lo spazio tra bottone e chat input
        st.markdown("""
        <style>
        .stButton > button {
            margin-bottom: -12px !important;
            padding: 8px 16px !important;
            height: 36px !important;
            font-size: 14px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Bottone Continua subito sopra la chat input, senza colonne/container
        continue_clicked = st.button("▶️ Continua", use_container_width=True, key="continue_btn")
        user_input = st.chat_input("Scrivi un messaggio...")
        
        # Se viene premuto il bottone "Continua", simula l'invio di "continua"
        if continue_clicked:
            user_input = "continua"
    if user_input:
        # Se l'agente non sta già generando, inizia il processo
        if not app_state.is_agent_generating():
            # Aggiungi il messaggio dell'utente
            app_state.add_message("user", user_input)
            
            # Traccia il messaggio dell'utente
            token_tracker = app_state.get_token_tracker()
            if token_tracker:
                token_tracker.track_message("user", user_input)
            
            # Ottieni user_info dal nuovo state manager
            user_info = app_state.get_user_info()
            
            # Salva il messaggio dell'utente nella history
            user_data_manager = app_state.get_user_data_manager()
            if user_data_manager:
                user_data_manager.save_chat_message(
                    user_info.id,
                    "user",
                    user_input
                )
            
            # Imposta lo stato di generazione e salva l'input per il processing
            app_state.set_agent_generating(True)
            app_state.set_pending_user_input(user_input)
            
            # Fai immediatamente un rerun per aggiornare l'interfaccia
            st.rerun()
    
    # Se c'è un input pendente e l'agente sta generando, processalo ora
    pending_input = app_state.get_pending_user_input()
    if (app_state.is_agent_generating() and pending_input):
        
        user_input = pending_input
        app_state.set_pending_user_input(None)  # Clear the pending input
        
        with st.spinner("L'assistente sta elaborando la risposta..."):
            try:
                # Ottieni user_info dal nuovo state manager
                user_info = app_state.get_user_info()
                
                # Usa il chat manager per la conversazione
                chat_manager = app_state.get_chat_manager()
                if not chat_manager:
                    st.error("❌ Chat manager non disponibile")
                    return
                    
                response = chat_manager.chat_with_assistant(user_input)
                app_state.add_message("assistant", response)
                
                # Traccia la risposta dell'assistente
                token_tracker = app_state.get_token_tracker()
                if token_tracker:
                    token_tracker.track_message("assistant", response)
                    
                    # Salva le statistiche dei costi nel file utente
                    stats = token_tracker.get_conversation_stats()
                    user_data_manager = app_state.get_user_data_manager()
                    if user_data_manager:
                        user_data_manager.save_cost_stats(
                            user_info.id,
                            stats
                        )
                
                # Salva la risposta dell'assistente nella history
                user_data_manager = app_state.get_user_data_manager()
                if user_data_manager:
                    user_data_manager.save_chat_message(
                        user_info.id,
                        "assistant",
                        response
                    )
                
                    # Salva la domanda e risposta dell'agente
                    user_data_manager.save_agent_qa(
                        user_info.id,
                        user_input,
                        response
                    )
                
                # Controlla se è necessario estrarre dati nutrizionali con DeepSeek
                deepseek_manager = app_state.get_deepseek_manager()
                if deepseek_manager:
                    deepseek_manager.check_and_extract_if_needed(
                        user_id=user_info.id,
                        user_data_manager=app_state.get_user_data_manager(),
                        user_info=user_info.__dict__
                    )
                
                # Rimuovi lo stato di generazione dopo aver completato tutto
                app_state.set_agent_generating(False)
                
            except Exception as e:
                # In caso di errore, assicurati di resettare lo stato
                app_state.set_agent_generating(False)
                raise e
        
        # Fai un rerun finale per aggiornare l'interfaccia
        st.rerun()


def render_chat_area():
    """
    Renderizza l'area principale della chat.
    
    Gestisce il flusso tra tutorial, domande nutrizionali e chat vera e propria.
    """
    # Ottieni user_info dal nuovo state manager
    user_info = app_state.get_user_info()
    if not user_info:
        st.warning("⚠️ Nessun utente autenticato.")
        return
    
    # Prima controlla se il tutorial è stato completato, indipendentemente dai dati salvati
    if not is_tutorial_completed(user_info.id):
        # Mostra il tutorial se non è stato completato
        show_app_tutorial()
        return
    
    if user_info.età:
        # Se ci sono ancora domande nutrizionali da gestire
        if handle_nutrition_questions_flow():
            return
        
        # Inizializza la chat history se necessario
        initialize_chat_history()
        
        # Mostra i messaggi della chat
        display_chat_messages()
        
        # Mostra notifiche DeepSeek se presenti
        deepseek_manager = app_state.get_deepseek_manager()
        if deepseek_manager:
            deepseek_manager.show_notifications()
        
        # Gestisci l'input dell'utente
        handle_user_input()
    else:
        # Se non ci sono dati età, significa che l'utente deve ancora compilare il form
        # ma il tutorial è già stato completato, quindi non mostriamo nulla
        # (il form sarà visibile nella sidebar)
        pass

def chat_interface():
    """
    Interfaccia principale della chat.
    
    Coordina tutti i componenti dell'interfaccia della chat:
    - Servizi di background (DeepSeek)
    - Creazione assistente
    - Sidebar informazioni utente
    - Area principale della chat
    """
    # Controlla risultati DeepSeek in background - con protezione
    deepseek_manager = app_state.get_deepseek_manager()
    if deepseek_manager:
        deepseek_manager.check_and_process_results()
        deepseek_manager.show_notifications()
    
    # L'assistente è ora creato in initialization.py
    
    # Renderizza la sidebar delle informazioni utente
    render_user_sidebar()
    
    # Renderizza l'area principale della chat
    render_chat_area() 