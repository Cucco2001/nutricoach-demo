"""
Modulo per la gestione del login e registrazione utenti.

Contiene tutte le funzioni per l'autenticazione, registrazione,
logout e caricamento delle informazioni utente salvate.
"""

import streamlit as st
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from services.login_persistence_service import get_login_persistence_service


def load_user_from_cookie(user_data_manager):
    """
    Carica l'utente dal cookie se esiste una sessione persistente valida.
    
    Args:
        user_data_manager: Gestore dei dati utente
        
    Returns:
        bool: True se l'utente è stato caricato dal cookie, False altrimenti
    """
    try:
        persistence_service = get_login_persistence_service()
        session_data = persistence_service.load_login_session(user_data_manager)
        
        if not session_data:
            return False
            
        user_id, auth_type = session_data
        
        # IMPORTANTE: Carica i dati dell'utente nella memoria del manager
        # come fa il login normale - questo era quello che mancava!
        user_data_manager._load_user_data(user_id)
        
        # Carica le informazioni utente
        nutritional_info = user_data_manager.get_nutritional_info(user_id)
        chat_history = user_data_manager.get_chat_history(user_id)
        has_chat_messages = len(chat_history) > 0
        
        # Ottieni informazioni base dell'utente
        user = user_data_manager.get_user_by_id(user_id)
        if not user:
            return False
            
        # Imposta le informazioni dell'utente in base al tipo di auth
        if auth_type == "google":
            # Per utenti Google, prova a ottenere info aggiuntive
            st.session_state.user_info = {
                "id": user_id,
                "username": user.username,
                "email": user.email if hasattr(user, 'email') else None,
                "auth_type": "google"
            }
        else:
            # Per utenti standard
            st.session_state.user_info = {
                "id": user_id,
                "username": user.username,
                "auth_type": "standard"
            }
        
        # Carica dati nutrizionali se esistono
        if nutritional_info:
            st.session_state.user_info.update({
                "età": nutritional_info.età,
                "sesso": nutritional_info.sesso,
                "peso": nutritional_info.peso,
                "altezza": nutritional_info.altezza,
                "attività": nutritional_info.attività,
                "obiettivo": nutritional_info.obiettivo,
                "preferences": user_data_manager.get_user_preferences(user_id)
            })
            
            # Gestisci tutorial e chat history
            if has_chat_messages:
                if nutritional_info.nutrition_answers:
                    st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                    st.session_state.current_question = len(NUTRITION_QUESTIONS)
                
                tutorial_key = f"tutorial_completed_{user_id}"
                st.session_state[tutorial_key] = True
        
        return True
        
    except Exception as e:
        st.error(f"Errore nel caricamento sessione dal cookie: {e}")
        return False


def handle_google_auth(user_data_manager):
    """
    Gestisce l'autenticazione con Google.
    
    Args:
        user_data_manager: Gestore dei dati utente
        
    Returns:
        bool: True se l'autenticazione è riuscita, False altrimenti
    """
    try:
        from services.google_auth_service import get_google_auth_service
        
        google_auth = get_google_auth_service()
        
        if not google_auth.is_available():
            st.warning("⚠️ Autenticazione Google non configurata")
            return False
        
        # Controlla se c'è un callback da processare
        query_params = st.query_params
        
        if 'code' in query_params:
            # Processa il callback OAuth2
            # Usa la variabile d'ambiente GOOGLE_REDIRECT_URI
            import os
            current_url = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8501')
            
            # Costruisci l'URL completo con tutti i parametri
            params = []
            for key, value in query_params.items():
                if isinstance(value, list):
                    for v in value:
                        params.append(f"{key}={v}")
                else:
                    params.append(f"{key}={value}")
            
            if params:
                current_url += "?" + "&".join(params)
            
            user_info = google_auth.handle_callback(current_url)
            
            if user_info:
                # Registra o effettua login dell'utente
                success, result = google_auth.register_or_login_google_user(user_info, user_data_manager)
                
                if success:
                    # Carica le informazioni utente
                    user_id = result
                    nutritional_info = user_data_manager.get_nutritional_info(user_id)
                    chat_history = user_data_manager.get_chat_history(user_id)
                    has_chat_messages = len(chat_history) > 0
                    
                    # Imposta le informazioni dell'utente
                    st.session_state.user_info = {
                        "id": user_id,
                        "username": user_info.get('name', user_info.get('email', 'Utente Google')),
                        "email": user_info.get('email'),
                        "auth_type": "google"
                    }
                    
                    # Carica dati nutrizionali se esistono
                    if nutritional_info:
                        st.session_state.user_info.update({
                            "età": nutritional_info.età,
                            "sesso": nutritional_info.sesso,
                            "peso": nutritional_info.peso,
                            "altezza": nutritional_info.altezza,
                            "attività": nutritional_info.attività,
                            "obiettivo": nutritional_info.obiettivo,
                            "preferences": user_data_manager.get_user_preferences(user_id)
                        })
                        
                        # Gestisci tutorial e chat history
                        if has_chat_messages:
                            if nutritional_info.nutrition_answers:
                                st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                                st.session_state.current_question = len(NUTRITION_QUESTIONS)
                            
                            tutorial_key = f"tutorial_completed_{user_id}"
                            st.session_state[tutorial_key] = True
                    
                    # Salva la sessione nei cookies per la persistenza
                    try:
                        persistence_service = get_login_persistence_service()
                        persistence_service.save_login_session(user_id, "google")
                    except Exception as e:
                        st.error(f"Errore nel salvare sessione persistente: {e}")
                    
                    # Pulisci i parametri della query
                    st.query_params.clear()
                    st.success(f"✅ Accesso effettuato con Google: {user_info.get('name', user_info.get('email'))}")
                    st.rerun()
                    return True
                else:
                    st.error(f"Errore nell'autenticazione Google: {result}")
                    return False
            else:
                st.error("Errore nell'ottenere informazioni da Google")
                return False
        
        return False
        
    except ImportError as e:
        st.warning(f"⚠️ Servizio Google Auth non disponibile: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Errore nell'autenticazione Google: {str(e)}")
        return False


def show_google_auth_button():
    """
    Mostra il bottone per l'autenticazione Google.
    """
    try:
        from services.google_auth_service import get_google_auth_service
        
        google_auth = get_google_auth_service()
        
        if not google_auth.is_available():
            return
        
        # Stile per il bottone Google
        st.markdown("""
        <style>
        .google-auth-button {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #4285f4;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            margin: 10px 0;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .google-auth-button:hover {
            background: #357ae8;
            color: white;
            text-decoration: none;
        }
        .google-auth-button svg {
            margin-right: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Genera URL di autorizzazione
        auth_url = google_auth.get_authorization_url()
        
        if auth_url:
            st.markdown(f"""
            <div style="text-align: center; margin: 15px 0;">
                <div style="margin: 10px 0; color: #666; font-size: 14px;">oppure</div>
                <a href="{auth_url}" class="google-auth-button" target="_self">
                    <svg width="18" height="18" viewBox="0 0 18 18">
                        <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"/>
                        <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.04a4.8 4.8 0 0 1-2.7.75 4.8 4.8 0 0 1-4.52-3.36H1.83v2.07A8 8 0 0 0 8.98 17z"/>
                        <path fill="#FBBC05" d="M4.46 10.41a4.8 4.8 0 0 1 0-2.82V5.52H1.83a8 8 0 0 0 0 7.17l2.63-2.07z"/>
                        <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 0 0 1.83 5.52L4.46 7.6a4.8 4.8 0 0 1 4.52-3.42z"/>
                    </svg>
                    Continua con Google
                </a>
            </div>
            """, unsafe_allow_html=True)
        
    except ImportError as e:
        st.warning(f"⚠️ Servizio Google Auth non disponibile: {str(e)}")
        pass
    except Exception as e:
        st.error(f"Errore nel mostrare bottone Google: {str(e)}")


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
                
                # Imposta le informazioni dell'utente
                st.session_state.user_info = {
                    "id": result,
                    "username": username,
                    "auth_type": "standard"
                }
                
                # Se ci sono informazioni nutrizionali salvate, caricale
                if nutritional_info:
                    # Aggiorna le informazioni dell'utente
                    st.session_state.user_info.update({
                        "età": nutritional_info.età,
                        "sesso": nutritional_info.sesso,
                        "peso": nutritional_info.peso,
                        "altezza": nutritional_info.altezza,
                        "attività": nutritional_info.attività,
                        "obiettivo": nutritional_info.obiettivo,
                        "preferences": user_data_manager.get_user_preferences(result)
                    })
                    
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
                
                # Salva la sessione nei cookies per la persistenza
                try:
                    persistence_service = get_login_persistence_service()
                    persistence_service.save_login_session(result, "standard")
                except Exception as e:
                    st.error(f"Errore nel salvare sessione persistente: {e}")
                
                st.rerun()
                return True
            else:
                st.error(result)
                return False
    
    # Mostra il bottone Google Auth sotto il form
    show_google_auth_button()
    
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
    
    # Mostra il bottone Google Auth sotto il form
    show_google_auth_button()
    
    return False


def handle_login_registration(user_data_manager):
    """
    Gestisce l'interfaccia completa di login e registrazione.
    
    Args:
        user_data_manager: Gestore dei dati utente
        
    Returns:
        bool: True se l'utente è autenticato, False altrimenti
    """
    # Controlla prima se c'è un callback Google da processare
    if handle_google_auth(user_data_manager):
        return True
    
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

    # Controlla prima se c'è una sessione persistente nei cookies
    if not st.session_state.user_info:
        if load_user_from_cookie(user_data_manager):
            st.success("✅ Accesso automatico dal cookie completato!")
            st.rerun()
            return True

    # Se l'utente non è autenticato, mostra form di login/registrazione
    if not st.session_state.user_info:
        
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
    
    # Poi effettua il logout normale
    st.session_state.user_info = None
    st.session_state.messages = []
    st.session_state.current_question = 0
    st.session_state.nutrition_answers = {}
    
    # Reset anche altri stati che potrebbero essere presenti
    if "thread_id" in st.session_state:
        del st.session_state.thread_id
    if "current_run_id" in st.session_state:
        st.session_state.current_run_id = None
    
    # Pulisci anche la sessione persistente nei cookies
    try:
        persistence_service = get_login_persistence_service()
        persistence_service.clear_login_session()
    except Exception as e:
        st.error(f"Errore nella pulizia sessione persistente: {e}")
    
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
    return st.session_state.get("user_info", None)


def is_user_authenticated():
    """
    Verifica se l'utente è attualmente autenticato.
    
    Returns:
        bool: True se l'utente è autenticato, False altrimenti
    """
    return st.session_state.get("user_info", None) is not None


def get_user_id():
    """
    Restituisce l'ID dell'utente corrente.
    
    Returns:
        str or None: ID dell'utente se autenticato, None altrimenti
    """
    user_info = get_current_user()
    return user_info.get("id") if user_info else None


def get_username():
    """
    Restituisce l'username dell'utente corrente.
    
    Returns:
        str or None: Username se autenticato, None altrimenti
    """
    user_info = get_current_user()
    return user_info.get("username") if user_info else None 