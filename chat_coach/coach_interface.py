"""
Interfaccia Coach Nutrizionale

Gestisce l'interfaccia utente per la modalità coach nutrizionale
con supporto per upload di immagini e chat interattiva.
"""

import streamlit as st
import base64
from typing import List, Optional
import logging

from .coach_manager import CoachManager

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def initialize_coach_session():
    """
    Inizializza la sessione del coach se non esiste.
    """
    if 'coach_messages' not in st.session_state:
        st.session_state.coach_messages = []
        
    if 'coach_manager' not in st.session_state:
        st.session_state.coach_manager = CoachManager(
            st.session_state.openai_client,
            st.session_state.user_data_manager
        )
        
    if 'coach_generating' not in st.session_state:
        st.session_state.coach_generating = False
        
    if 'coach_initialized' not in st.session_state:
        st.session_state.coach_initialized = False


def image_to_base64(uploaded_file) -> str:
    """
    Converte un file immagine caricato in base64.
    
    Args:
        uploaded_file: File caricato da Streamlit
        
    Returns:
        String base64 dell'immagine
    """
    try:
        # Leggi il file
        image_bytes = uploaded_file.read()
        
        # Codifica in base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Ottieni il tipo MIME
        mime_type = uploaded_file.type
        
        # Costruisci la data URL
        data_url = f"data:{mime_type};base64,{image_base64}"
        
        return data_url
        
    except Exception as e:
        logger.error(f"Errore nella conversione immagine: {str(e)}")
        return None


def display_coach_messages():
    """
    Visualizza i messaggi della chat del coach.
    """
    for message in st.session_state.coach_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                # Messaggio utente
                st.write(message["content"])
                
                # Mostra immagini se presenti
                if "images" in message and message["images"]:
                    st.write("📸 **Immagini allegate:**")
                    for i, image_data in enumerate(message["images"]):
                        if image_data.startswith("data:image"):
                            # Mostra l'immagine base64
                            st.image(image_data, caption=f"Immagine {i+1}", width=300)
                        else:
                            st.write(f"Immagine {i+1}: {image_data}")
            else:
                # Messaggio del coach
                st.write(message["content"])


def handle_coach_input():
    """
    Gestisce l'input dell'utente per il coach.
    """
    # Se il coach sta generando, mostra un messaggio
    if st.session_state.coach_generating:
        st.info("🤖 Il coach sta elaborando la risposta...")
        return
    
    # Sezione per upload immagini - resa più compatta
    with st.expander("📸 Clicca qui per caricare una foto del tuo pasto"):
        uploaded_files = st.file_uploader(
            "Carica una o più immagini",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="coach_images",
            label_visibility="collapsed"
        )
    
    # Input di testo
    user_input = st.chat_input("Scrivi al tuo coach nutrizionale...")
    
    if user_input:
        # Processa le immagini se ci sono
        images = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                image_data = image_to_base64(uploaded_file)
                if image_data:
                    images.append(image_data)
        
        # Aggiungi il messaggio dell'utente
        user_message = {
            "role": "user",
            "content": user_input
        }
        
        if images:
            user_message["images"] = images
        
        st.session_state.coach_messages.append(user_message)
        
        # Imposta lo stato di generazione
        st.session_state.coach_generating = True
        st.session_state.pending_coach_input = user_input
        st.session_state.pending_coach_images = images
        
        # Rerun per aggiornare l'interfaccia
        st.rerun()


def process_coach_response():
    """
    Processa la risposta del coach se c'è un input pendente.
    """
    if (st.session_state.coach_generating and 
        hasattr(st.session_state, 'pending_coach_input') and
        st.session_state.pending_coach_input):
        
        user_input = st.session_state.pending_coach_input
        images = getattr(st.session_state, 'pending_coach_images', [])
        
        # Pulisci i valori pendenti
        st.session_state.pending_coach_input = None
        st.session_state.pending_coach_images = []
        
        with st.spinner("🤖 Il coach sta elaborando la risposta..."):
            try:
                # Ottieni o crea il thread del coach
                thread_id = getattr(st.session_state, 'coach_thread_id', None)
                
                if not thread_id:
                    # Inizializza la conversazione del coach
                    welcome_msg = st.session_state.coach_manager.initialize_coach_conversation(
                        st.session_state.user_info
                    )
                    thread_id = st.session_state.coach_thread_id
                    
                    # Aggiungi il messaggio di benvenuto
                    if not any(msg.get("role") == "assistant" for msg in st.session_state.coach_messages):
                        st.session_state.coach_messages.append({
                            "role": "assistant",
                            "content": welcome_msg
                        })
                
                # Prepara la cronologia conversazione
                conversation_history = []
                if hasattr(st.session_state, 'coach_messages'):
                    # Converti i messaggi della sessione in formato OpenAI (escludi il messaggio appena aggiunto)
                    for msg in st.session_state.coach_messages[:-1]:  # Escludi l'ultimo messaggio (quello appena aggiunto)
                        if msg["role"] in ["user", "assistant"]:
                            conversation_history.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                
                # Ottieni la risposta del coach
                response_data = st.session_state.coach_manager.get_response(
                    user_message=user_input,
                    images=images,
                    conversation_history=conversation_history
                )
                
                # Estrai il contenuto della risposta
                if response_data.get("success"):
                    response = response_data.get("content", "Errore nella risposta del coach")
                else:
                    response = response_data.get("content", "Errore nella comunicazione con il coach")
                
                # Aggiungi la risposta del coach
                st.session_state.coach_messages.append({
                    "role": "assistant",
                    "content": response
                })
                
                # Salva le statistiche dei costi
                stats = st.session_state.coach_manager.get_token_stats()
                st.session_state.user_data_manager.save_cost_stats(
                    st.session_state.user_info["id"],
                    stats
                )
                
                # Rimuovi lo stato di generazione
                st.session_state.coach_generating = False
                
            except Exception as e:
                logger.error(f"Errore nella conversazione con il coach: {str(e)}")
                st.error(f"Errore: {str(e)}")
                st.session_state.coach_generating = False
        
        # Rerun per mostrare la risposta
        st.rerun()


def show_coach_stats():
    """
    Mostra le statistiche dell'uso del coach.
    """
    if hasattr(st.session_state, 'coach_manager'):
        try:
            stats = st.session_state.coach_manager.get_token_stats()
            
            # # Controlla se stats contiene i dati necessari
            # if stats and stats.get('usage', {}).get('message_count', 0) > 0:
            #     with st.expander("📊 Statistiche Coach"):
            #         col1, col2, col3 = st.columns(3)
                    
            #         with col1:
            #             st.metric("Messaggi Totali", stats.get('usage', {}).get('message_count', 0))
                    
            #         with col2:
            #             st.metric("Token Usati", f"{stats.get('tokens', {}).get('total', 0):,}")
                    
            #         with col3:
            #             st.metric("Costo Stimato", f"${stats.get('costs', {}).get('total_cost_usd', 0):.4f}")
        except Exception as e:
            logger.error(f"Errore nel mostrare le statistiche del coach: {str(e)}")
            # Non mostrare errore all'utente, semplicemente non mostrare le statistiche


def coach_interface():
    """
    Interfaccia principale del coach nutrizionale.
    """
    # Inizializza la sessione del coach
    initialize_coach_session()
    
    # Mostra il titolo
    st.markdown("# NutrAICoach")
    
    # Mostra una breve descrizione
    st.markdown("""
    **Il tuo Coach Nutrizionale 🚀**

    ⏰ Consigli su cosa mangiare ora  
    📸 Analisi istantanea del tuo piatto  
    ⚖️ Porzioni perfette ogni giorno  
    💬 Suggerimenti personalizzati, sempre per te!
    """)
    
    # Inizializza la conversazione del coach se non è stata inizializzata
    if not st.session_state.coach_initialized:
        with st.spinner("🤖 Inizializzo il tuo coach nutrizionale..."):
            try:
                welcome_msg = st.session_state.coach_manager.initialize_coach_conversation(
                    st.session_state.user_info
                )
                
                # Aggiungi il messaggio di benvenuto
                st.session_state.coach_messages.append({
                    "role": "assistant",
                    "content": welcome_msg
                })
                
                st.session_state.coach_initialized = True
                
            except Exception as e:
                logger.error(f"Errore nell'inizializzazione del coach: {str(e)}")
                st.error(f"Errore nell'inizializzazione: {str(e)}")
    
    # Mostra i messaggi della chat
    display_coach_messages()
    
    # Processa eventuali risposte pendenti
    process_coach_response()
    
    # Gestisci l'input dell'utente
    handle_coach_input()
    
    # Mostra le statistiche
    show_coach_stats()
    
    # Aggiungi alcuni suggerimenti utili
    with st.sidebar:      
        # Pulsante per resettare la conversazione
        if st.button("🔄 Nuova Conversazione"):
            st.session_state.coach_messages = []
            st.session_state.coach_initialized = False
            if hasattr(st.session_state, 'coach_thread_id'):
                del st.session_state.coach_thread_id
            st.rerun() 