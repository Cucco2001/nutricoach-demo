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



def render_user_sidebar():
    """
    Renderizza la sidebar con le informazioni dell'utente.
    
    Gestisce il form per inserire le informazioni iniziali o
    mostra le informazioni esistenti con il pulsante ricomincia.
    """
    with st.sidebar:
        st.markdown("## 👤 Le Tue Info", unsafe_allow_html=True)
        
        if not st.session_state.user_info.get("età"):
            # Usa il modulo frontend per gestire il form delle informazioni utente
            handle_user_info_form(
                user_id=st.session_state.user_info["id"],
                user_data_manager=st.session_state.user_data_manager,
                create_new_thread_func=st.session_state.chat_manager.create_new_thread
            )
        else:
            # Usa il modulo frontend per mostrare le informazioni utente
            handle_user_info_display(st.session_state.user_info)
            
            # Usa il modulo frontend per gestire il bottone "Ricomincia"
            handle_restart_button(
                user_data_manager=st.session_state.user_data_manager,
                deepseek_manager=st.session_state.deepseek_manager,
                create_new_thread_func=st.session_state.chat_manager.create_new_thread
            )
            



def handle_nutrition_questions_flow():
    """
    Gestisce il flusso delle domande nutrizionali.
    
    Returns:
        bool: True se ci sono ancora domande da gestire, False altrimenti
    """
    if st.session_state.current_question < len(NUTRITION_QUESTIONS):
        # Usa il modulo frontend per gestire le domande nutrizionali
        has_more_questions = handle_nutrition_questions(
            user_info=st.session_state.user_info,
            user_id=st.session_state.user_info["id"],
            user_data_manager=st.session_state.user_data_manager
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
    # Inizializza il token tracker se non esiste
    if 'token_tracker' not in st.session_state:
        st.session_state.token_tracker = TokenCostTracker(model="gpt-4")
    
    if not st.session_state.messages:
        chat_history = st.session_state.user_data_manager.get_chat_history(st.session_state.user_info["id"])
        if chat_history:
            st.session_state.messages = [
                {"role": msg.role, "content": msg.content}
                for msg in chat_history
            ]
            # Traccia i messaggi esistenti per avere statistiche accurate
            for msg in st.session_state.messages:
                st.session_state.token_tracker.track_message(msg["role"], msg["content"])
        else:
            # Se non c'è history, invia il prompt iniziale
            initial_prompt = get_initial_prompt(
                user_info=st.session_state.user_info,
                nutrition_answers=st.session_state.nutrition_answers,
                user_preferences=st.session_state.user_info['preferences']
            )
            
            # Traccia il prompt iniziale come input
            st.session_state.token_tracker.track_message("user", initial_prompt)
            
            # Crea un nuovo thread solo se non esiste già
            if not hasattr(st.session_state, 'thread_id'):
                st.session_state.chat_manager.create_new_thread()
            
            # Imposta lo stato di generazione prima di chiamare l'agente
            st.session_state.agent_generating = True
            
            try:
                # Invia il prompt iniziale usando il manager
                response = st.session_state.chat_manager.chat_with_assistant(initial_prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Traccia la risposta dell'assistente
                st.session_state.token_tracker.track_message("assistant", response)
                
                # Salva il messaggio nella history
                st.session_state.user_data_manager.save_chat_message(
                    st.session_state.user_info["id"],
                    "assistant",
                    response
                )
                
                # Rimuovi lo stato di generazione dopo aver completato tutto
                st.session_state.agent_generating = False
                
            except Exception as e:
                # In caso di errore, assicurati di resettare lo stato
                st.session_state.agent_generating = False
                raise e
            
            st.rerun()


def display_chat_messages():
    """
    Mostra la cronologia dei messaggi della chat.
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def handle_user_input():
    """
    Gestisce l'input dell'utente e la generazione della risposta.
    """
    user_input = st.chat_input("Scrivi un messaggio...")
    if user_input:
        # Se l'agente non sta già generando, inizia il processo
        if not st.session_state.agent_generating:
            # Aggiungi il messaggio dell'utente
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Traccia il messaggio dell'utente
            if 'token_tracker' in st.session_state:
                st.session_state.token_tracker.track_message("user", user_input)
            
            # Salva il messaggio dell'utente nella history
            st.session_state.user_data_manager.save_chat_message(
                st.session_state.user_info["id"],
                "user",
                user_input
            )
            
            # Imposta lo stato di generazione e salva l'input per il processing
            st.session_state.agent_generating = True
            st.session_state.pending_user_input = user_input
            
            # Fai immediatamente un rerun per aggiornare l'interfaccia
            st.rerun()
    
    # Se c'è un input pendente e l'agente sta generando, processalo ora
    if (st.session_state.agent_generating and 
        hasattr(st.session_state, 'pending_user_input') and 
        st.session_state.pending_user_input):
        
        user_input = st.session_state.pending_user_input
        st.session_state.pending_user_input = None  # Clear the pending input
        
        with st.spinner("L'assistente sta elaborando la risposta..."):
            try:
                # Usa il chat manager per la conversazione
                response = st.session_state.chat_manager.chat_with_assistant(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Traccia la risposta dell'assistente
                if 'token_tracker' in st.session_state:
                    st.session_state.token_tracker.track_message("assistant", response)
                    
                    # Salva le statistiche dei costi nel file utente
                    stats = st.session_state.token_tracker.get_conversation_stats()
                    st.session_state.user_data_manager.save_cost_stats(
                        st.session_state.user_info["id"],
                        stats
                    )
                
                # Salva la risposta dell'assistente nella history
                st.session_state.user_data_manager.save_chat_message(
                    st.session_state.user_info["id"],
                    "assistant",
                    response
                )
                
                # Salva la domanda e risposta dell'agente
                st.session_state.user_data_manager.save_agent_qa(
                    st.session_state.user_info["id"],
                    user_input,
                    response
                )
                
                # Controlla se è necessario estrarre dati nutrizionali con DeepSeek
                st.session_state.deepseek_manager.check_and_extract_if_needed(
                    user_id=st.session_state.user_info["id"],
                    user_data_manager=st.session_state.user_data_manager,
                    user_info=st.session_state.user_info
                )
                
                # Rimuovi lo stato di generazione dopo aver completato tutto
                st.session_state.agent_generating = False
                
            except Exception as e:
                # In caso di errore, assicurati di resettare lo stato
                st.session_state.agent_generating = False
                raise e
        
        # Fai un rerun finale per aggiornare l'interfaccia
        st.rerun()


def render_chat_area():
    """
    Renderizza l'area principale della chat.
    
    Gestisce il flusso tra tutorial, domande nutrizionali e chat vera e propria.
    """
    if st.session_state.user_info.get("età"):
        # Se ci sono ancora domande nutrizionali da gestire
        if handle_nutrition_questions_flow():
            return
        
        # Inizializza la chat history se necessario
        initialize_chat_history()
        
        # Mostra i messaggi della chat
        display_chat_messages()
        
        # Mostra notifiche DeepSeek se presenti
        st.session_state.deepseek_manager.show_notifications()
        
        # Gestisci l'input dell'utente
        handle_user_input()
    else:
        # Se il tutorial non è ancora stato formalmente completato (premendo "Inizia")
        if not is_tutorial_completed(st.session_state.user_info['id']):
            # Mostra il tutorial (o il suo messaggio di completamento)
            show_app_tutorial()
            
            # Se tutte le sezioni sono state visitate, mostra anche il messaggio di default
            if not are_all_sections_visited(st.session_state.user_info['id']):
                 st.markdown("""
                    <div class="content-card">
                        <h3>👈 Inizia da qui!</h3>
                        <p>Per avviare la tua consulenza nutrizionale personalizzata con NutrAICoach, inserisci le tue informazioni di base nel pannello a sinistra.</p>
                        <p>Una volta completato, l'assistente AI ti guiderà attraverso il resto del processo.</p>
                    </div>
                """, unsafe_allow_html=True)
            return

        # Se il tutorial è completato, ma mancano i dati, mostra solo il messaggio
        st.markdown("""
            <div class="content-card">
                <h3>👈 Inizia da qui!</h3>
                <p>Per avviare la tua consulenza nutrizionale personalizzata con NutrAICoach, inserisci le tue informazioni di base nel pannello a sinistra.</p>
                <p>Una volta completato, l'assistente AI ti guiderà attraverso il resto del processo.</p>
            </div>
        """, unsafe_allow_html=True)


def chat_interface():
    """
    Interfaccia principale della chat.
    
    Coordina tutti i componenti dell'interfaccia della chat:
    - Servizi di background (DeepSeek)
    - Creazione assistente
    - Sidebar informazioni utente
    - Area principale della chat
    """
    # Controlla risultati DeepSeek in background
    st.session_state.deepseek_manager.check_and_process_results()
    st.session_state.deepseek_manager.show_notifications()
    
    # L'assistente è ora creato in initialization.py
    
    # Renderizza la sidebar delle informazioni utente
    render_user_sidebar()
    
    # Renderizza l'area principale della chat
    render_chat_area() 