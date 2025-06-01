"""
Modulo frontend per NutriCoach.

Contiene tutti i componenti dell'interfaccia utente e l'inizializzazione
dell'applicazione organizzati in moduli separati.
"""

# Configurazione delle domande nutrizionali
from .nutrition_questions import NUTRITION_QUESTIONS

# Gestione delle domande nutrizionali
from .handle_nutrition_questions import handle_nutrition_questions

# Gestione delle informazioni utente
from .handle_initial_info import handle_user_info_form, handle_user_info_display

# Gestione dei bottoni
from .buttons import handle_restart_button

# Gestione del piano nutrizionale
from .Piano_nutrizionale import handle_user_data

# Gestione degli sport
from .sports_frontend import (
    load_sports_data,
    get_sports_by_category,
    on_sport_category_change
)

# Inizializzazione dell'applicazione
from .initialization import initialize_app, initialize_global_variables

# Gestione del login e autenticazione
from .login import (
    handle_login_form,
    handle_registration_form,
    handle_login_registration,
    handle_logout,
    show_logout_button,
    get_current_user,
    is_user_authenticated,
    get_user_id,
    get_username
)

__all__ = [
    'NUTRITION_QUESTIONS',
    'handle_nutrition_questions',
    'handle_user_info_form',
    'handle_user_info_display',
    'handle_restart_button',
    'handle_user_data',
    'load_sports_data',
    'get_sports_by_category',
    'on_sport_category_change',
    'initialize_app',
    'initialize_global_variables',
    'handle_login_form',
    'handle_registration_form',
    'handle_login_registration',
    'handle_logout',
    'show_logout_button',
    'get_current_user',
    'is_user_authenticated',
    'get_user_id',
    'get_username'
] 