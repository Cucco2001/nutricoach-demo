"""
Modulo per la gestione del login e registrazione utenti.

Contiene tutte le funzioni per l'autenticazione, registrazione,
logout e caricamento delle informazioni utente salvate.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS

# Import del nuovo state manager
from services.state_service import app_state, UserInfo


def handle_login_form(user_data_manager):
    """
    Gestisce il form di login dell'utente.
    
    Args:
        user_data_manager: Gestore dei dati utente per l'autenticazione
        
    Returns:
        bool: True se il login è stato effettuato con successo, False altrimenti
    """
    with st.form("login_form"):
        st.write("Accedi al tuo account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Accedi"):
            # Converti l'username in minuscolo per il confronto case-insensitive
            success, result = user_data_manager.login_user(username.lower(), password)
            if success:
                # Carica le informazioni nutrizionali salvate
                nutritional_info = user_data_manager.get_nutritional_info(result)
                
                # Carica la chat history per verificare se ci sono messaggi salvati
                chat_history = user_data_manager.get_chat_history(result)
                has_chat_messages = len(chat_history) > 0
                
                # Imposta le informazioni dell'utente nel nostro state manager
                user_info_data = {
                    "id": result,
                    "username": username
                }
                
                # Sincronizza con entrambi per ora (compatibilità)
                st.session_state.user_info = user_info_data
                app_state.set_user_info(UserInfo(**user_info_data))
                
                # Se ci sono informazioni nutrizionali salvate, caricale
                if nutritional_info:
                    # Aggiorna le informazioni dell'utente
                    user_info_data.update({
                        "età": nutritional_info.età,
                        "sesso": nutritional_info.sesso,
                        "peso": nutritional_info.peso,
                        "altezza": nutritional_info.altezza,
                        "attività": nutritional_info.attività,
                        "obiettivo": nutritional_info.obiettivo,
                        "preferences": user_data_manager.get_user_preferences(result)
                    })
                    
                    # Sincronizza con entrambi
                    st.session_state.user_info = user_info_data
                    app_state.set_user_info(UserInfo(**user_info_data))
                    
                    # Se ha messaggi in chat, carica normalmente e salta il tutorial
                    if has_chat_messages:
                        # Carica le risposte nutrizionali se presenti
                        if nutritional_info.nutrition_answers:
                            st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                            st.session_state.current_question = len(NUTRITION_QUESTIONS)
                        
                        # Salta il tutorial perché l'utente ha già una conversazione
                        tutorial_key = f"tutorial_completed_{result}"
                        st.session_state[tutorial_key] = True
                    else:
                        # Se non ha messaggi in chat ma ha nutrition_answers,
                        # significa che era nelle domande iniziali, quindi resetta
                        if nutritional_info.nutrition_answers and len(nutritional_info.nutrition_answers) > 0:
                            # Resetta solo i dati utente relativi alle domande
                            st.session_state.current_question = 0
                            st.session_state.nutrition_answers = {}
                            
                            # Resetta le informazioni nutrizionali ai valori di default
                            user_data_manager.save_nutritional_info(
                                result,
                                {
                                    "età": 30,
                                    "sesso": "Maschio", 
                                    "peso": 70,
                                    "altezza": 170,
                                    "attività": "Sedentario",
                                    "obiettivo": "Mantenimento",
                                    "nutrition_answers": {},
                                    "agent_qa": []
                                }
                            )
                            
                            # Cancella la chat history e le domande/risposte dell'agente
                            user_data_manager.clear_chat_history(result)
                            user_data_manager.clear_agent_qa(result)
                            
                            # Resetta le preferenze utente
                            user_data_manager.clear_user_preferences(result)
                            
                            # Cancella eventuali variabili di sessione delle preferenze
                            if 'excluded_foods_list' in st.session_state:
                                del st.session_state.excluded_foods_list
                            if 'preferred_foods_list' in st.session_state:
                                del st.session_state.preferred_foods_list
                            if 'preferences_prompt' in st.session_state:
                                del st.session_state.preferences_prompt
                            if 'prompt_to_add_at_next_message' in st.session_state:
                                del st.session_state.prompt_to_add_at_next_message
                            
                            # Resetta il tutorial per farlo ripartire
                            from frontend.tutorial import reset_tutorial
                            reset_tutorial(result)
                
                st.rerun()
                return True
            else:
                st.error(result)
                return False
    
    return False


def handle_registration_form(user_data_manager):
    """
    Gestisce il form di registrazione dell'utente.
    
    Args:
        user_data_manager: Gestore dei dati utente per la registrazione
        
    Returns:
        bool: True se la registrazione è stata effettuata con successo, False altrimenti
    """
    with st.form("register_form"):
        st.write("Crea un nuovo account")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Conferma password", type="password")
        st.write("I dati inseriti non saranno mai condivisi con terze parti.")
        if st.form_submit_button("Registrati"):
            if new_password != confirm_password:
                st.error("Le password non coincidono")
                return False
            else:
                # Converti l'username in minuscolo prima di registrarlo
                success, result = user_data_manager.register_user(new_username.lower(), new_email, new_password)
                if success:
                    st.success("Registrazione completata! Ora puoi accedere.")
                    # Imposta il flag per il redirect via JS e fai un rerun
                    st.session_state.registration_successful = True
                    st.rerun()
                else:
                    st.error(result)
                    return False
    
    return False


def handle_login_registration(user_data_manager):
    """
    Gestisce l'interfaccia completa di login e registrazione.
    
    Args:
        user_data_manager: Gestore dei dati utente
        
    Returns:
        bool: True se l'utente è autenticato, False altrimenti
    """
    # Se la registrazione è appena avvenuta, esegui JS per switchare al tab di login
    if st.session_state.get('registration_successful', False):
        from streamlit_js_eval import streamlit_js_eval
        
        js_to_click_tab = """
        setTimeout(() => {
            const allTabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
            const loginTab = Array.from(allTabs).find(tab => tab.innerText.includes("Accedi"));
            if (loginTab) {
                loginTab.click();
            }
        }, 100);
        """
        streamlit_js_eval(js_expressions=js_to_click_tab, key="click_login_tab")
        del st.session_state.registration_successful # Rimuovi il flag

    # Inizializza user_info se non esiste
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

    # Se l'utente non è autenticato, mostra form di login/registrazione
    if not app_state.is_user_authenticated():
        
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)

        # Titolo veloce senza logo
        st.markdown(
            '''
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="font-size: 3rem; margin: 0; color: #27ae60;">🥗 NutrAICoach</h1>
                <p style="color: #666; margin-top: 1rem;">
                    Il tuo assistente nutrizionale personale basato su AI
                </p>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Tabs per Login/Registrazione con stile migliorato
        tab1, tab2 = st.tabs(["🔐 Accedi", "✨ Registrati"])
        
        with tab1:
            handle_login_form(user_data_manager)
        
        with tab2:
            handle_registration_form(user_data_manager)
            
        st.markdown('</div>', unsafe_allow_html=True)

        return False
    
    return True


def handle_logout():
    """
    Gestisce il logout dell'utente resettando tutte le variabili di sessione.
    Se l'utente stava ancora rispondendo alle domande iniziali, effettua prima un "Ricomincia".
    """
    # Controlla se l'utente era ancora nel mezzo delle domande iniziali
    # (se non aveva ancora iniziato la conversazione con l'agente)
    user_was_in_questions = (
        st.session_state.get("current_question", 0) < len(NUTRITION_QUESTIONS) and
        len(st.session_state.get("messages", [])) == 0
    )
    
    # Se era ancora nelle domande, effettua prima un "Ricomincia"
    if user_was_in_questions and st.session_state.get("user_info"):
        from frontend.buttons import ButtonHandler
        
        # Crea un handler dei bottoni e chiama la funzione di reset
        handler = ButtonHandler(
            st.session_state.user_data_manager,
            st.session_state.deepseek_manager,
            st.session_state.chat_manager.create_new_thread
        )
        handler._reset_user_session()
    
    # Poi effettua il logout normale - sincronizza entrambi
    st.session_state.user_info = None
    app_state.set_user_info(None)
    
    st.session_state.messages = []
    app_state.clear_messages()
    
    st.session_state.current_question = 0
    app_state.set_current_question(0)
    
    st.session_state.nutrition_answers = {}
    app_state.set_nutrition_answers({})
    
    # Reset anche altri stati che potrebbero essere presenti
    if "thread_id" in st.session_state:
        del st.session_state.thread_id
    if "current_run_id" in st.session_state:
        st.session_state.current_run_id = None
    
    st.rerun()


def show_logout_button():
    """
    Mostra il pulsante di logout nella sidebar.
    
    Returns:
        bool: True se il logout è stato cliccato, False altrimenti
    """
    if st.button("Logout"):
        handle_logout()
        return True
    return False


def get_current_user():
    """
    Restituisce le informazioni dell'utente corrente.
    
    Returns:
        dict or None: Informazioni dell'utente se autenticato, None altrimenti
    """
    user_info = app_state.get_user_info()
    return user_info.__dict__ if user_info else None


def is_user_authenticated():
    """
    Verifica se l'utente è attualmente autenticato.
    
    Returns:
        bool: True se l'utente è autenticato, False altrimenti
    """
    return app_state.is_user_authenticated()


def get_user_id():
    """
    Restituisce l'ID dell'utente corrente.
    
    Returns:
        str or None: ID dell'utente se autenticato, None altrimenti
    """
    user_info = app_state.get_user_info()
    return user_info.id if user_info else None


def get_username():
    """
    Restituisce l'username dell'utente corrente.
    
    Returns:
        str or None: Username se autenticato, None altrimenti
    """
    user_info = app_state.get_user_info()
    return user_info.username if user_info else None 