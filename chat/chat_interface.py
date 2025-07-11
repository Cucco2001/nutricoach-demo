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
from chat_coach.coach_interface import coach_interface



def render_user_sidebar():
    """
    Renderizza la sidebar con le informazioni dell'utente o la scelta della modalità.
    
    Mostra le informazioni utente prima dell'inizializzazione,
    poi mostra la scelta della modalità di chat dopo l'inizializzazione.
    """
    with st.sidebar:
        # Controlla se il tutorial è completato
        tutorial_completed = is_tutorial_completed(st.session_state.user_info['id'])
        
        # Controlla se l'utente ha completato l'inizializzazione
        user_initialized = (
            st.session_state.user_info.get("età") and 
            tutorial_completed and 
            st.session_state.current_question >= len(NUTRITION_QUESTIONS)
        )
        
        if not user_initialized:
            # Prima dell'inizializzazione: mostra le informazioni utente
            st.markdown("## 👤 Le Tue Info", unsafe_allow_html=True)
            
            if not st.session_state.user_info.get("età") or not tutorial_completed:
                # Usa il modulo frontend per gestire il form delle informazioni utente
                handle_user_info_form(
                    user_id=st.session_state.user_info["id"],
                    user_data_manager=st.session_state.user_data_manager,
                    create_new_thread_func=st.session_state.chat_manager.create_new_thread
                )
            else:
                # Usa il modulo frontend per mostrare le informazioni utente
                handle_user_info_display(st.session_state.user_info)
        else:
            # Dopo l'inizializzazione: mostra la scelta della modalità
            st.markdown("## 🔄 Modalità Chat", unsafe_allow_html=True)
            
            # Inizializza la modalità se non esiste
            if 'chat_mode' not in st.session_state:
                st.session_state.chat_mode = "Crea/Modifica Dieta"
            
            # Radio button per la selezione della modalità
            chat_mode = st.radio(
                "Cosa vuoi fare?",
                ["Crea/Modifica Dieta", "Chiedi al Nutrizionista AI"],
                key="chat_mode_selection",
                disabled=st.session_state.get('agent_generating', False)
            )
            
            # Aggiorna la modalità nella sessione
            st.session_state.chat_mode = chat_mode
            
            # Separatore
            st.markdown("---")
            
            # Pulsante per ricominciare (solo dopo l'inizializzazione)
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
                
                # Aggiungi il messaggio di presentazione all'inizio della prima risposta
                welcome_message = """🥗 **Ciao! Sono il tuo Coach Nutrizionale specializzato nella generazione di diete personalizzate.** 

Il mio compito è creare un piano alimentare su misura per te, basato sui tuoi dati personali, obiettivi e preferenze. Analizzerò tutti i parametri che mi hai fornito e ti guiderò passo dopo passo nella creazione della tua dieta settimanale completa.

---

"""
                
                # Combina il messaggio di benvenuto con la risposta dell'agente
                full_response = welcome_message + response
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Traccia la risposta dell'assistente
                st.session_state.token_tracker.track_message("assistant", response)
                
                # Salva il messaggio nella history
                st.session_state.user_data_manager.save_chat_message(
                    st.session_state.user_info["id"],
                    "assistant",
                    full_response
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
    # Se l'agente sta generando, mostra un messaggio informativo invece del campo di input
    if st.session_state.agent_generating:
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

        # Simula l'invio di "continua" se il bottone è premuto
        if continue_clicked:
            user_input = "continua"

        
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
    # Prima controlla se il tutorial è stato completato, indipendentemente dai dati salvati
    if not is_tutorial_completed(st.session_state.user_info['id']):
        # Mostra il tutorial se non è stato completato
        show_app_tutorial()
        return
    
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
        # Se non ci sono dati età, significa che l'utente deve ancora compilare il form
        # ma il tutorial è già stato completato, quindi non mostriamo nulla
        # (il form sarà visibile nella sidebar)
        pass


def render_coach_area():
    """
    Renderizza l'area del coach nutrizionale.
    
    Gestisce il flusso per la modalità coach dopo il tutorial e le domande nutrizionali.
    """
    # Prima controlla se il tutorial è stato completato
    if not is_tutorial_completed(st.session_state.user_info['id']):
        # Mostra il tutorial se non è stato completato
        show_app_tutorial()
        return
    
    if st.session_state.user_info.get("età"):
        # Se ci sono ancora domande nutrizionali da gestire
        if handle_nutrition_questions_flow():
            return
        
        # Mostra l'interfaccia del coach
        coach_interface()
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
    # Controlla risultati DeepSeek in background
    st.session_state.deepseek_manager.check_and_process_results()
    st.session_state.deepseek_manager.show_notifications()
    
    # L'assistente è ora creato in initialization.py
    
    # Renderizza la sidebar (che ora gestisce anche la scelta della modalità)
    render_user_sidebar()
    
    # Renderizza l'interfaccia appropriata in base alla modalità
    # Se l'utente non ha ancora completato l'inizializzazione, usa la modalità default
    if 'chat_mode' not in st.session_state:
        st.session_state.chat_mode = "Crea/Modifica Dieta"
    
    if st.session_state.chat_mode == "Crea/Modifica Dieta":
        # Modalità originale - crea/modifica dieta
        render_chat_area()
    else:
        # Modalità Coach - consigli nutrizionali
        render_coach_area() 