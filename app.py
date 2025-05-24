import streamlit as st
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from nutricoach_agent import available_tools, system_prompt
from user_data_manager import UserDataManager
from datetime import datetime

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="NutriCoach - Il tuo assistente nutrizionale personale",
    page_icon="🥗",
    layout="wide"
)

# Inizializzazione delle variabili di sessione
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "diet_plan" not in st.session_state:
    st.session_state.diet_plan = None
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI()
if "current_run_id" not in st.session_state:
    st.session_state.current_run_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "nutrition_answers" not in st.session_state:
    st.session_state.nutrition_answers = {}
if "user_data_manager" not in st.session_state:
    st.session_state.user_data_manager = UserDataManager()

# Carica i dati degli sport
def load_sports_data():
    """Carica i dati degli sport dal file JSON e li organizza per categoria."""
    try:
        with open(os.path.join("Dati_processed", "sport_calories.json"), 'r', encoding='utf-8') as file:
            sports_data = json.load(file)
        
        # Organizza gli sport per categoria
        sports_by_category = {}
        for sport_name, sport_info in sports_data["sports"].items():
            category = sport_info["category"]
            if category not in sports_by_category:
                sports_by_category[category] = []
            
            # Formatta il nome dello sport (sostituisci '_' con spazi e prima lettera di ogni parola maiuscola)
            words = sport_name.split('_')
            formatted_name = ' '.join(word.capitalize() for word in words)
            
            sports_by_category[category].append({
                "name": formatted_name,
                "key": sport_name,
                "kcal_per_hour": sport_info["kcal_per_hour"],
                "description": sport_info["description"]
            })
        
        # Ordina alfabeticamente gli sport in ogni categoria
        for category in sports_by_category:
            sports_by_category[category] = sorted(sports_by_category[category], key=lambda x: x["name"])
        
        return sports_data["sports"], sports_by_category
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati degli sport: {str(e)}")
        return {}, {}

# Funzione per ottenere gli sport di una categoria specifica
def get_sports_by_category(category_name):
    """Restituisce la lista degli sport per una categoria specifica."""
    # Mappa i nomi delle categorie del menu a quelli del file JSON
    category_map = {
        "Fitness - Allenamento medio (principianti e livello intermedio)": "Fitness - Allenamento medio",
        "Fitness - Bodybuilding Massa (solo esperti >2 anni di allenamento)": "Fitness - Bodybuilding Massa",
        "Fitness - Bodybuilding Definizione (solo esperti >2 anni di allenamento)": "Fitness - Bodybuilding Definizione",
        "Sport di forza (es: powerlifting, sollevamento pesi, strongman)": "Sport di forza",
        "Sport di resistenza (es: corsa, ciclismo, nuoto, triathlon)": "Sport di resistenza",
        "Sport aciclici (es: tennis, pallavolo, arti marziali, calcio)": "Sport aciclici",
        "Altro": None
    }
    
    # Carica i dati degli sport se non sono già in session_state
    if "sports_data" not in st.session_state or "sports_by_category" not in st.session_state:
        st.session_state.sports_data, st.session_state.sports_by_category = load_sports_data()
    
    mapped_category = category_map.get(category_name)
    
    # Debug: stampa le categorie disponibili
    print(f"Categoria selezionata: {category_name}")
    print(f"Categoria mappata: {mapped_category}")
    print(f"Categorie disponibili: {list(st.session_state.sports_by_category.keys())}")
    
    if mapped_category and mapped_category in st.session_state.sports_by_category:
        return st.session_state.sports_by_category[mapped_category]
    else:
        # Se la categoria non esiste o è "Altro", mostra tutti gli sport
        all_sports = []
        for category, sports in st.session_state.sports_by_category.items():
            all_sports.extend(sports)
        # Rimuovi duplicati e ordina
        return sorted(all_sports, key=lambda x: x["name"])

# Callback quando cambia la selezione della categoria sport
def on_sport_category_change(i):
    """
    Callback per reagire al cambio di categoria sport.
    Rimuove la selezione precedente dello sport specifico per forzare una nuova selezione.
    
    Args:
        i: indice dello sport nella lista
    """
    print(f"Categoria sport cambiata per sport index {i}")
    
    # Rimuovi la selezione precedente dello sport specifico per forzare una nuova selezione
    if f"specific_sport_{i}" in st.session_state:
        del st.session_state[f"specific_sport_{i}"]
    
    # Assicurati che i dati degli sport siano caricati
    if "sports_data" not in st.session_state or "sports_by_category" not in st.session_state:
        st.session_state.sports_data, st.session_state.sports_by_category = load_sports_data()
    
    # Aggiorna la lista degli sport in session_state
    if "sports_list" in st.session_state and i < len(st.session_state.sports_list):
        selected_category = st.session_state[f"sport_type_{i}"]
        print(f"Nuova categoria selezionata: {selected_category}")
        
        # Aggiorna la categoria nello sports_list
        st.session_state.sports_list[i]["sport_type"] = selected_category
        
        # Rimuovi lo sport specifico selezionato precedentemente
        if "specific_sport" in st.session_state.sports_list[i]:
            del st.session_state.sports_list[i]["specific_sport"]

# Definizione delle domande nutrizionali iniziali
NUTRITION_QUESTIONS = [
    {
        "id": "allergies",
        "question": "Hai qualche intolleranza o allergia alimentare?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": "Specifica quali:",
        "show_follow_up_on": "Sì"
    },
    {
        "id": "weight_goal",
        "question": lambda user_info: f"Quanti kg vuoi {'perdere' if user_info['obiettivo'] == 'Perdita di peso' else 'aumentare'} e in quanto tempo (in mesi)?",
        "type": "number_input",
        "show_if": lambda user_info: user_info["obiettivo"] in ["Perdita di peso", "Aumento di massa"],
        "fields": [
            {
                "id": "kg",
                "label": lambda user_info: f"Kg da {'perdere' if user_info['obiettivo'] == 'Perdita di peso' else 'aumentare'}",
                "min": 1,
                "max": 30,
                "default": 5
            },
            {
                "id": "months",
                "label": "In quanti mesi",
                "min": 1,
                "max": 24,
                "default": 3
            }
        ]
    },
    {
        "id": "sports",
        "question": "Pratichi sport?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": {
            "type": "multiple_sports",
            "fields": [
                {
                    "id": "sport_type",
                    "label": "Che tipo di attività sportiva pratichi?",
                    "type": "select",
                    "options": [
                        "Fitness - Allenamento medio (principianti e livello intermedio)",
                        "Fitness - Bodybuilding Massa (solo esperti >2 anni di allenamento)",
                        "Fitness - Bodybuilding Definizione (solo esperti >2 anni di allenamento)",
                        "Sport di forza (es: powerlifting, sollevamento pesi, strongman)",
                        "Sport di resistenza (es: corsa, ciclismo, nuoto, triathlon)",
                        "Sport aciclici (es: tennis, pallavolo, arti marziali, calcio)",
                        "Altro"
                    ]
                },
                {
                    "id": "specific_sport",
                    "label": "Specifica lo sport",
                    "type": "select",
                    "dynamic_options": True,
                    "options": []
                },
                {
                    "id": "intensity",
                    "label": "Intensità dell'attività",
                    "type": "select",
                    "options": ["easy", "medium", "hard"],
                    "descriptions": {
                        "easy": "Attività leggera (-20% calorie)",
                        "medium": "Attività moderata (calorie standard)",
                        "hard": "Attività intensa (+20% calorie)"
                    }
                },
                {
                    "id": "hours_per_week",
                    "label": "Quante ore alla settimana?",
                    "type": "number",
                    "min": 1,
                    "max": 30,
                    "default": 3
                }
            ]
        },
        "show_follow_up_on": "Sì"
    },
    {
        "id": "meal_preferences",
        "question": "Vuoi decidere tu il numero di pasti giornalieri?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": {
            "type": "meal_schedule",
            "fields": [
                {
                    "id": "num_meals",
                    "label": "Quanti pasti vuoi fare al giorno?",
                    "type": "number",
                    "min": 1,
                    "max": 6,
                    "default": 5
                },
                {
                    "id": "meal_times",
                    "label": "A che ora vorresti fare i pasti? (opzionale)",
                    "type": "dynamic_time",
                    "optional": True,
                    "dynamic_count": "num_meals",
                    "meal_labels": [
                        "Colazione",
                        "Spuntino mattutino",
                        "Pranzo",
                        "Spuntino pomeridiano",
                        "Cena",
                        "Spuntino serale",
                        "Altro pasto"
                    ]
                }
            ]
        },
        "show_follow_up_on": "Sì"
    }
]

# Funzione per creare l'assistente
def create_assistant():
    """Crea o recupera l'assistente dalla sessione."""
    if "assistant" not in st.session_state:
        try:
            st.session_state.assistant = st.session_state.openai_client.beta.assistants.create(
                name="Nutricoach Assistant",
                instructions=system_prompt,
                tools=available_tools,
                model="gpt-4o"  # Usa lo stesso modello di nutricoach_agent.py
            )
            st.session_state.assistant_created = True
        except Exception as e:
            st.error(f"Errore nella creazione dell'assistente: {str(e)}")
            st.session_state.assistant_created = False
            return None
    return st.session_state.assistant

def handle_tool_calls(run_status):
    """Gestisce le chiamate ai tool dell'assistente."""
    try:
        tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []
        
        for tool_call in tool_calls:
            try:
                # Estrai i parametri della chiamata
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Importa le funzioni necessarie
                from nutridb_tool import (
                    get_macros, get_LARN_protein, get_standard_portion, 
                    get_weight_from_volume, get_fattore_cottura, get_LARN_fibre, 
                    get_LARN_lipidi_percentuali, get_LARN_vitamine, 
                    compute_Harris_Benedict_Equation, get_protein_multiplier, 
                    calculate_sport_expenditure, check_ultraprocessed_foods
                )
                from user_data_tool import (
                    get_user_preferences, get_progress_history, get_agent_qa, get_nutritional_info
                )
                
                # Mappa dei nomi delle funzioni alle funzioni effettive
                function_map = {
                    # Funzioni per accedere al database nutrizionale
                    "get_macros": get_macros,
                    "get_LARN_protein": get_LARN_protein,
                    "get_standard_portion": get_standard_portion,
                    "get_weight_from_volume": get_weight_from_volume,
                    "get_fattore_cottura": get_fattore_cottura,
                    "get_LARN_fibre": get_LARN_fibre,
                    "get_LARN_lipidi_percentuali": get_LARN_lipidi_percentuali,
                    "get_LARN_vitamine": get_LARN_vitamine,
                    "compute_Harris_Benedict_Equation": compute_Harris_Benedict_Equation,
                    "get_protein_multiplier": get_protein_multiplier,
                    "calculate_sport_expenditure": calculate_sport_expenditure,
                    "check_ultraprocessed_foods": check_ultraprocessed_foods,
                    
                    # Funzioni per accedere ai dati dell'utente
                    "get_user_preferences": get_user_preferences,
                    "get_progress_history": get_progress_history,
                    "get_agent_qa": get_agent_qa,
                    "get_nutritional_info": get_nutritional_info,
                    
                    # Per retrocompatibilità
                    "nutridb_tool": lambda **args: nutridb_tool(**args),
                    "user_data_tool": lambda **args: user_data_tool(**args)
                }
                
                # Esegui la funzione appropriata
                if function_name in function_map:
                    result = function_map[function_name](**arguments)
                else:
                    result = {"error": f"Tool {function_name} non supportato"}
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
                
            except Exception as e:
                st.error(f"Errore nell'esecuzione del tool {function_name}: {str(e)}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"error": str(e)})
                })
        
        return tool_outputs
    except Exception as e:
        st.error(f"Errore nella gestione dei tool: {str(e)}")
        return None

def create_new_thread():
    """Crea un nuovo thread per la conversazione, mantenendo la chat history dell'utente."""
    try:
        thread = st.session_state.openai_client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state.current_run_id = None
        
        # Mantieni la chat history presente nello user JSON invece di azzerarla
        if hasattr(st.session_state, 'user_info') and st.session_state.user_info and "id" in st.session_state.user_info:
            # Recupera la chat history dell'utente
            chat_history = st.session_state.user_data_manager.get_chat_history(st.session_state.user_info["id"])
            if chat_history:
                # Carica i messaggi esistenti nella session state
                st.session_state.messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in chat_history
                ]
                
                # Inserisci i messaggi esistenti nel nuovo thread OpenAI
                for msg in chat_history:
                    try:
                        st.session_state.openai_client.beta.threads.messages.create(
                            thread_id=st.session_state.thread_id,
                            role=msg.role,
                            content=msg.content
                        )
                    except Exception as e:
                        st.warning(f"Impossibile aggiungere messaggio al thread: {str(e)}")
            else:
                # Se non c'è history, inizializza array vuoto
                st.session_state.messages = []
        else:
            # Se non c'è un utente loggato, inizializza array vuoto
            st.session_state.messages = []
        
        # Mantieni le domande nutrizionali
        st.session_state.current_question = st.session_state.get('current_question', 0)
        st.session_state.nutrition_answers = st.session_state.get('nutrition_answers', {})
    except Exception as e:
        st.error(f"Errore nella creazione del thread: {str(e)}")
        return None

def check_and_cancel_run():
    """Verifica se c'è una run attiva e la cancella se necessario."""
    if hasattr(st.session_state, 'current_run_id') and st.session_state.current_run_id:
        try:
            run = st.session_state.openai_client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=st.session_state.current_run_id
            )
            if run.status in ['active', 'requires_action', 'failed', 'expired']:
                st.session_state.openai_client.beta.threads.runs.cancel(
                    thread_id=st.session_state.thread_id,
                    run_id=st.session_state.current_run_id
                )
        except Exception:
            pass
        finally:
            st.session_state.current_run_id = None

def chat_with_assistant(user_input):
    """Gestisce la conversazione con l'assistente."""
    try:
        # Se non esiste un thread, crene uno nuovo
        if not hasattr(st.session_state, 'thread_id'):
            create_new_thread()
        
        # Verifica e cancella eventuali run bloccate
        check_and_cancel_run()
        
        # Aggiungi il messaggio dell'utente al thread
        try:
            st.session_state.openai_client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_input
            )
        except Exception as e:
            # Se c'è un errore nel thread, crene uno nuovo e riprova
            create_new_thread()
            st.session_state.openai_client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_input
            )
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Crea una run
                run = st.session_state.openai_client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant.id
                )
                st.session_state.current_run_id = run.id
                
                # Attendi il completamento con timeout più lungo
                start_time = time.time()
                timeout = 180  # aumentato a 180 secondi (3 minuti)
                
                with st.empty():
                    while True:
                        if time.time() - start_time > timeout:
                            check_and_cancel_run()
                            create_new_thread()  # Crea un nuovo thread dopo il timeout
                            return "Mi dispiace, l'operazione è durata troppo a lungo. Per favore, riprova."
                        
                        try:
                            run_status = st.session_state.openai_client.beta.threads.runs.retrieve(
                                thread_id=st.session_state.thread_id,
                                run_id=run.id
                            )
                        except Exception:
                            check_and_cancel_run()
                            create_new_thread()
                            raise Exception("Errore nel recupero dello stato della run")
                        
                        if run_status.status == 'completed':
                            st.session_state.current_run_id = None
                            break
                        elif run_status.status in ['failed', 'expired', 'cancelled']:
                            check_and_cancel_run()
                            create_new_thread()
                            raise Exception(f"Run {run_status.status}")
                        elif run_status.status == 'requires_action':
                            # Gestisci le chiamate ai tool
                            tool_outputs = handle_tool_calls(run_status)
                            if tool_outputs:
                                try:
                                    # Invia i risultati e continua
                                    st.session_state.openai_client.beta.threads.runs.submit_tool_outputs(
                                        thread_id=st.session_state.thread_id,
                                        run_id=run.id,
                                        tool_outputs=tool_outputs
                                    )
                                except Exception:
                                    check_and_cancel_run()
                                    create_new_thread()
                                    raise Exception("Errore nell'invio dei risultati dei tool")
                            else:
                                check_and_cancel_run()
                                create_new_thread()
                                raise Exception("Errore nella gestione dei tool")
                        
                        # Breve pausa prima del prossimo controllo
                        time.sleep(1)
                
                # Ottieni la risposta
                try:
                    messages = st.session_state.openai_client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )
                    return messages.data[0].content[0].text.value
                except Exception:
                    check_and_cancel_run()
                    create_new_thread()
                    raise Exception("Errore nel recupero dei messaggi")
                
            except Exception as e:
                retry_count += 1
                check_and_cancel_run()
                if retry_count >= max_retries:
                    create_new_thread()  # Crea un nuovo thread dopo troppi tentativi falliti
                    st.error(f"Errore dopo {max_retries} tentativi: {str(e)}")
                    return "Mi dispiace, si è verificato un errore. Riprova."
                time.sleep(2 ** retry_count)  # Exponential backoff
        
    except Exception as e:
        check_and_cancel_run()
        create_new_thread()  # Crea un nuovo thread dopo un errore generale
        st.error(f"Errore nella conversazione: {str(e)}")
        return "Mi dispiace, si è verificato un errore inaspettato. Riprova."


def track_user_progress():
    """Gestisce il tracking dei progressi dell'utente"""
    with st.expander("Traccia i tuoi progressi"):
        weight = st.number_input("Peso attuale (kg)", min_value=30.0, max_value=200.0, step=0.1, format="%.1f")
        date = st.date_input("Data misurazione")
        measurements = {}
        
        col1, col2 = st.columns(2)
        with col1:
            measurements["circonferenza_vita"] = st.number_input("Circonferenza vita (cm)", min_value=0.0, step=0.1, format="%.1f")
            measurements["circonferenza_fianchi"] = st.number_input("Circonferenza fianchi (cm)", min_value=0.0, step=0.1, format="%.1f")
        
        with col2:
            measurements["circonferenza_braccio"] = st.number_input("Circonferenza braccio (cm)", min_value=0.0, step=0.1, format="%.1f")
            measurements["circonferenza_coscia"] = st.number_input("Circonferenza coscia (cm)", min_value=0.0, step=0.1, format="%.1f")
        
        if st.button("Salva progressi"):
            # Arrotonda tutti i valori a una cifra decimale
            weight = round(weight, 1)
            measurements = {k: round(v, 1) for k, v in measurements.items()}
            
            # Salva i progressi
            st.session_state.user_data_manager.track_progress(
                user_id=st.session_state.user_info["id"],
                weight=weight,
                date=date.strftime("%Y-%m-%d"),
                measurements=measurements
            )
            
            # Verifica se è passato abbastanza tempo per una valutazione
            progress_history = st.session_state.user_data_manager.get_progress_history(st.session_state.user_info["id"])
            if len(progress_history) >= 2:
                last_entry = progress_history[-1]
                first_entry = progress_history[0]
                
                # Calcola le settimane passate
                last_date = datetime.strptime(last_entry.date, "%Y-%m-%d")
                first_date = datetime.strptime(first_entry.date, "%Y-%m-%d")
                weeks_passed = (last_date - first_date).days / 7
                
                if weeks_passed >= 3:
                    # Calcola la variazione di peso
                    weight_change = last_entry.weight - first_entry.weight
                    
                    # Prepara il prompt per l'agente
                    evaluation_prompt = f"""
                    È passato un periodo di {weeks_passed:.1f} settimane dall'inizio del piano alimentare.
                    È necessario valutare i progressi e adattare il piano.

                    DATI INIZIALI:
                    • Peso iniziale: {first_entry.weight} kg
                    • Data iniziale: {first_entry.date}

                    DATI ATTUALI:
                    • Peso attuale: {last_entry.weight} kg
                    • Data attuale: {last_entry.date}
                    • Variazione peso: {weight_change:+.1f} kg

                    MISURAZIONI INIZIALI:
                    {json.dumps(first_entry.measurements, indent=2)}

                    MISURAZIONI ATTUALI:
                    {json.dumps(last_entry.measurements, indent=2)}

                    OBIETTIVO ORIGINALE:
                    • {st.session_state.user_info['obiettivo']}

                    Per favore:
                    1. Valuta i progressi rispetto all'obiettivo
                    2. Ricalcola il metabolismo basale e il fabbisogno calorico
                    3. Aggiorna le quantità dei macronutrienti
                    4. Modifica il piano alimentare in base ai nuovi calcoli
                    5. Fornisci raccomandazioni specifiche per il prossimo periodo

                    IMPORTANTE: Inizia la tua risposta con "📊 VALUTAZIONE PERIODICA" e poi procedi con l'analisi.
                    Assicurati di includere:
                    - Un riepilogo dei progressi
                    - I nuovi calcoli del metabolismo e delle calorie
                    - Le modifiche al piano alimentare
                    - Le raccomandazioni per il prossimo periodo

                    Procedi con la valutazione e l'aggiornamento del piano.
                    """
                    
                    # Invia il prompt all'agente
                    response = chat_with_assistant(evaluation_prompt)
                    
                    # Aggiungi un messaggio di notifica
                    notification = "🔄 Il piano alimentare è stato aggiornato in base ai tuoi progressi. Controlla la chat per i dettagli."
                    st.session_state.messages.append({"role": "assistant", "content": notification})
                    st.session_state.user_data_manager.save_chat_message(
                        st.session_state.user_info["id"],
                        "assistant",
                        notification
                    )
                    
                    # Aggiungi la valutazione completa
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.session_state.user_data_manager.save_chat_message(
                        st.session_state.user_info["id"],
                        "assistant",
                        response
                    )
                    
                    # Salva la domanda e risposta dell'agente
                    st.session_state.user_data_manager.save_agent_qa(
                        st.session_state.user_info["id"],
                        evaluation_prompt,
                        response
                    )
                    
                    # Mostra un messaggio di successo con avviso dell'aggiornamento
                    st.success("Progressi salvati con successo! Il piano alimentare è stato aggiornato in base ai tuoi progressi.")
                else:
                    st.success("Progressi salvati con successo!")
            else:
                st.success("Progressi salvati con successo!")
            
            st.rerun()

def show_progress_history():
    """Mostra la storia dei progressi dell'utente"""
    if "user_info" in st.session_state and "id" in st.session_state.user_info:
        history = st.session_state.user_data_manager.get_progress_history(
            st.session_state.user_info["id"]
        )
        
        if history:
            progress_df = pd.DataFrame([
                {
                    "Data": entry.date,
                    "Peso": entry.weight,
                    **entry.measurements
                }
                for entry in history
            ])
            
            # Formatta i numeri con una cifra decimale
            numeric_columns = progress_df.select_dtypes(include=['float64']).columns
            progress_df[numeric_columns] = progress_df[numeric_columns].round(1)
            
            st.line_chart(progress_df.set_index("Data")["Peso"])
            
            with st.expander("Dettaglio misurazioni"):
                # Aggiungi selettore per il tipo di visualizzazione
                view_type = st.radio(
                    "Formato visualizzazione:",
                    ["Tabella", "Dettagliato"],
                    horizontal=True,
                    key="view_type"
                )
                
                if view_type == "Tabella":
                    # Visualizzazione tabella con pulsante elimina
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.dataframe(progress_df, hide_index=True)
                    with col2:
                        # Aggiungi pulsanti di eliminazione allineati con la tabella
                        for idx in range(len(progress_df)):
                            if st.button("🗑️", key=f"delete_table_{idx}", help=f"Elimina voce del {progress_df.iloc[idx]['Data']}"):
                                if st.session_state.user_data_manager.delete_progress_entry(
                                    st.session_state.user_info["id"],
                                    progress_df.iloc[idx]['Data']
                                ):
                                    st.success(f"Voce del {progress_df.iloc[idx]['Data']} eliminata con successo!")
                                    st.rerun()
                                else:
                                    st.error("Errore durante l'eliminazione della voce.")
                else:
                    # Visualizzazione dettagliata
                    for idx, (index, row) in enumerate(progress_df.iterrows()):
                        col1, col2 = st.columns([0.9, 0.1])
                        with col1:
                            # Mostra i dati della riga
                            st.write(f"Data: {row['Data']}")
                            st.write(f"Peso: {row['Peso']} kg")
                            measurements = {k: v for k, v in row.items() if k not in ['Data', 'Peso']}
                            if measurements:
                                st.write("Misurazioni:")
                                for k, v in measurements.items():
                                    st.write(f"- {k}: {v} cm")
                        with col2:
                            # Aggiungi il pulsante di eliminazione con chiave univoca
                            if st.button("🗑️", key=f"delete_detailed_{row['Data']}_{idx}", help=f"Elimina voce del {row['Data']}"):
                                if st.session_state.user_data_manager.delete_progress_entry(
                                    st.session_state.user_info["id"],
                                    row['Data']
                                ):
                                    st.success(f"Voce del {row['Data']} eliminata con successo!")
                                    st.rerun()
                                else:
                                    st.error("Errore durante l'eliminazione della voce.")
                        st.divider()  # Aggiunge una linea di separazione tra le voci
        else:
            st.info("Nessun dato di progresso disponibile")

def handle_preferences():
    """Gestisce le preferenze dell'utente"""
    with st.expander("Gestisci le tue preferenze alimentari"):
        # Carica le preferenze esistenti
        user_preferences = st.session_state.user_data_manager.get_user_preferences(st.session_state.user_info["id"])
        
        # Alimenti esclusi
        if 'excluded_foods_list' not in st.session_state:
            st.session_state.excluded_foods_list = user_preferences.get("excluded_foods", []) if user_preferences else []
        
        st.subheader("Alimenti da escludere")
        
        # Mostra gli alimenti esclusi esistenti
        for i, food in enumerate(st.session_state.excluded_foods_list):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.text(food)
            with col2:
                if st.button("🗑️", key=f"del_excluded_{i}"):
                    st.session_state.excluded_foods_list.pop(i)
                    st.rerun()
        
        # Aggiungi nuovo alimento da escludere
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            excluded_foods = st.text_input("Inserisci un alimento da escludere", key="excluded_foods")
        with col2:
            if st.button("Aggiungi", key="add_excluded"):
                if excluded_foods and excluded_foods not in st.session_state.excluded_foods_list:
                    st.session_state.excluded_foods_list.append(excluded_foods)
                    st.rerun()
        
        # Alimenti preferiti
        if 'preferred_foods_list' not in st.session_state:
            st.session_state.preferred_foods_list = user_preferences.get("preferred_foods", []) if user_preferences else []
            
        st.subheader("Alimenti preferiti")
        
        # Mostra gli alimenti preferiti esistenti
        for i, food in enumerate(st.session_state.preferred_foods_list):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.text(food)
            with col2:
                if st.button("🗑️", key=f"del_preferred_{i}"):
                    st.session_state.preferred_foods_list.pop(i)
                    st.rerun()
        
        # Aggiungi nuovo alimento preferito
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            preferred_foods = st.text_input("Inserisci un alimento preferito", key="preferred_foods")
        with col2:
            if st.button("Aggiungi", key="add_preferred"):
                if preferred_foods and preferred_foods not in st.session_state.preferred_foods_list:
                    st.session_state.preferred_foods_list.append(preferred_foods)
                    st.rerun()
        
        
        
        st.subheader("Necessità particolari o preferenze:")
        note_default = user_preferences.get("notes", "") if user_preferences else ""
        user_notes = st.text_area(
            "Scrivi qualsiasi informazione aggiuntiva da tenere a mente (es. vegetariano, pranzi al lavoro, ecc.)",
            value=note_default,
            height=120
        )

        
        if st.button("Salva preferenze"):
            preferences = {
                "excluded_foods": st.session_state.excluded_foods_list,
                "preferred_foods": st.session_state.preferred_foods_list,
                "user_notes": user_notes.strip(),
            }
            
            st.session_state.user_data_manager.update_user_preferences(
                user_id=st.session_state.user_info["id"],
                preferences=preferences
            )
            st.success("Preferenze salvate con successo!")

# Funzione per convertire i dati degli sport nel formato richiesto dal tool
def prepare_sports_data_for_tool(sports_data):
    """
    Converte i dati degli sport dal formato del form al formato richiesto dal tool calculate_sport_expenditure.
    
    Args:
        sports_data: Lista di sport dal form
        
    Returns:
        Lista di sport nel formato richiesto dal tool
    """
    result = []
    
    print(f"Dati sport ricevuti: {sports_data}")
    
    if not sports_data or not isinstance(sports_data, list):
        print(f"Dati sport non validi: {sports_data}")
        return result
    
    for i, sport in enumerate(sports_data):
        print(f"Elaborazione sport {i+1}: {sport}")
        
        if "specific_sport" not in sport or not sport["specific_sport"]:
            print(f"Sport {i+1} senza specific_sport, salto")
            continue
            
        try:
            # Verifica che ci siano tutte le chiavi necessarie
            if isinstance(sport["specific_sport"], dict) and "key" in sport["specific_sport"]:
                sport_name = sport["specific_sport"]["key"]
            else:
                print(f"Sport {i+1} ha un formato non valido: {sport['specific_sport']}")
                continue
                
            # Assicurati che hours_per_week sia presente e sia un numero
            if "hours_per_week" not in sport or not sport["hours_per_week"]:
                print(f"Sport {i+1} senza ore settimanali, salto")
                continue
                
            try:
                hours = float(sport["hours_per_week"])
                if hours <= 0:
                    print(f"Sport {i+1} ha ore non positive: {hours}")
                    continue
            except (ValueError, TypeError):
                print(f"Sport {i+1} ha ore non valide: {sport['hours_per_week']}")
                continue
            
            sport_info = {
                "sport_name": sport_name,
                "hours": hours
            }
            
            # Aggiungi l'intensità se specificata
            if "intensity" in sport and sport["intensity"] and sport["intensity"] in ["easy", "medium", "hard"]:
                sport_info["intensity"] = sport["intensity"]
                
            print(f"Sport {i+1} elaborato: {sport_info}")
            result.append(sport_info)
        except Exception as e:
            # Gestisci eventuali errori di conversione
            print(f"Errore nella preparazione del sport {i+1}: {str(e)}")
            continue
    
    print(f"Risultato finale: {result}")
    return result

def chat_interface():
    """Interfaccia principale della chat"""
    # Crea l'assistente
    create_assistant()
    
    # Sidebar per le informazioni dell'utente
    with st.sidebar:
        st.subheader("Le tue informazioni")
        if not st.session_state.user_info.get("età"):
            # Carica le informazioni nutrizionali salvate
            nutritional_info = st.session_state.user_data_manager.get_nutritional_info(st.session_state.user_info["id"])
            # Carica le preferenze utente
            user_preferences = st.session_state.user_data_manager.get_user_preferences(st.session_state.user_info["id"])
            
            with st.form("user_info_form"):
                st.write("Per iniziare, inserisci i tuoi dati:")
                età = st.number_input("Età", 18, 100, nutritional_info.età if nutritional_info else 30)
                sesso = st.selectbox("Sesso", ["Maschio", "Femmina"], index=0 if not nutritional_info else (0 if nutritional_info.sesso == "Maschio" else 1))
                peso = st.number_input("Peso (kg)", min_value=40, max_value=200, value=nutritional_info.peso if nutritional_info else 70, step=1)
                altezza = st.number_input("Altezza (cm)", 140, 220, nutritional_info.altezza if nutritional_info else 170)
                attività = st.selectbox("Livello di attività fisica (a parte sport praticato)",
                                    ["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"],
                                    index=["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"].index(nutritional_info.attività) if nutritional_info else 0)
                obiettivo = st.selectbox("Obiettivo",
                                     ["Perdita di peso", "Mantenimento", "Aumento di massa"],
                                     index=["Perdita di peso", "Mantenimento", "Aumento di massa"].index(nutritional_info.obiettivo) if nutritional_info else 0)
                
                if st.form_submit_button("Inizia"):
                    # Aggiorna le informazioni dell'utente
                    user_info = {
                        "età": età,
                        "sesso": sesso,
                        "peso": peso,
                        "altezza": altezza,
                        "attività": attività,
                        "obiettivo": obiettivo,
                        "preferences": user_preferences  # Aggiungi le preferenze
                    }
                    st.session_state.user_info.update(user_info)
                    
                    # Salva le informazioni nutrizionali
                    st.session_state.user_data_manager.save_nutritional_info(
                        st.session_state.user_info["id"],
                        user_info
                    )
                    
                    # Se ci sono risposte nutrizionali salvate, caricale
                    if nutritional_info and nutritional_info.nutrition_answers:
                        st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                        st.session_state.current_question = len(NUTRITION_QUESTIONS)
                    
                    # Crea un nuovo thread quando si inizia una nuova consulenza
                    create_new_thread()
                    st.rerun()
        else:
            # Mostra le informazioni dell'utente
            st.write("Dati inseriti:")
            for key, value in st.session_state.user_info.items():
                if key == "peso":
                    st.write(f"Peso: {int(value)} kg")
                elif key not in ["id", "username", "preferences"]:  # Non mostrare ID, username e preferences
                    st.write(f"{key.capitalize()}: {value}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ricomincia"):
                    # Resetta tutte le informazioni
                    st.session_state.user_info = {"id": st.session_state.user_info["id"], 
                                                "username": st.session_state.user_info["username"]}
                    st.session_state.current_question = 0
                    st.session_state.nutrition_answers = {}
                    st.session_state.messages = []
                    
                    # Cancella la chat history e le domande/risposte dell'agente
                    st.session_state.user_data_manager.clear_chat_history(st.session_state.user_info["id"])
                    st.session_state.user_data_manager.clear_agent_qa(st.session_state.user_info["id"])
                    
                    # Resetta le informazioni nutrizionali
                    st.session_state.user_data_manager.save_nutritional_info(
                        st.session_state.user_info["id"],
                        {
                            "età": 30,  # Valori di default
                            "sesso": "Maschio",
                            "peso": 70,
                            "altezza": 170,
                            "attività": "Sedentario",
                            "obiettivo": "Mantenimento",
                            "nutrition_answers": {},
                            "agent_qa": []
                        }
                    )
                    
                    # Resetta le preferenze utente
                    st.session_state.user_data_manager.clear_user_preferences(st.session_state.user_info["id"])
                    
                    # Crea un nuovo thread
                    create_new_thread()
                    st.rerun()
    
    # Area principale della chat
    if st.session_state.user_info.get("età"):
        if st.session_state.current_question < len(NUTRITION_QUESTIONS):
            current_q = NUTRITION_QUESTIONS[st.session_state.current_question]
            
            # Verifica se la domanda deve essere mostrata in base alle condizioni
            show_question = True
            if "show_if" in current_q:
                show_question = current_q["show_if"](st.session_state.user_info)
            
            if show_question:
                st.write("## Domanda " + str(st.session_state.current_question + 1))
                
                # Gestisce la domanda in base al tipo
                if current_q["type"] == "radio":
                    # Mostra la domanda principale
                    st.markdown(f"### {current_q['question']}")
                    answer = st.radio("", current_q["options"])
                    
                    # Gestisce eventuali follow-up
                    follow_up_answer = None
                    if "follow_up" in current_q and answer == current_q["show_follow_up_on"]:
                        if isinstance(current_q["follow_up"], str):
                            # Gestione vecchio formato stringa
                            st.markdown(f"### {current_q['follow_up']}")
                            follow_up_answer = st.text_input("")
                        elif isinstance(current_q["follow_up"], dict):
                            if current_q["follow_up"].get("type") == "multiple_sports":
                                # Gestione sport multipli
                                if "sports_list" not in st.session_state:
                                    st.session_state.sports_list = [{}]
                                
                                follow_up_answer = []
                                
                                for i, sport in enumerate(st.session_state.sports_list):
                                    st.markdown(f"### Sport {i+1}")
                                    sport_data = {}
                                    
                                    # Precarica i dati degli sport
                                    if "sports_data" not in st.session_state or "sports_by_category" not in st.session_state:
                                        st.session_state.sports_data, st.session_state.sports_by_category = load_sports_data()
                                    
                                    for field in current_q["follow_up"]["fields"]:
                                        show_field = True
                                        if "show_if" in field and "show_if_value" in field:
                                            ref_value = sport.get(field["show_if"])
                                            show_field = ref_value == field["show_if_value"]
                                        
                                        if show_field:
                                            st.markdown(f"### {field['label']}")
                                            if field["type"] == "select":
                                                if field["id"] == "sport_type":
                                                    # Quando cambia la categoria, usa il callback
                                                    sport_data[field["id"]] = st.selectbox(
                                                        "Seleziona",
                                                        options=field["options"],
                                                        key=f"{field['id']}_{i}",
                                                        label_visibility="collapsed",
                                                        on_change=on_sport_category_change,
                                                        args=(i,)
                                                    )
                                                elif field["id"] == "specific_sport" and "dynamic_options" in field and field["dynamic_options"]:
                                                    # Seleziona gli sport in base alla categoria scelta
                                                    selected_category = sport.get("sport_type", "")
                                                    if not selected_category and f"sport_type_{i}" in st.session_state:
                                                        selected_category = st.session_state[f"sport_type_{i}"]
                                                    
                                                    # Debug
                                                    print(f"Selected category for dropdown: {selected_category}")
                                                    
                                                    sports_options = get_sports_by_category(selected_category)
                                                    
                                                    # Mostra i nomi ma salva le chiavi
                                                    sport_names = [s["name"] for s in sports_options]
                                                    
                                                    # Debug
                                                    print(f"Available sports: {sport_names}")
                                                    
                                                    # Se non ci sono sport disponibili, mostra un messaggio
                                                    if not sport_names:
                                                        st.warning("Nessuno sport disponibile per questa categoria. Seleziona prima una categoria.")
                                                        sport_data[field["id"]] = None
                                                    else:
                                                        # Crea un dizionario di riferimento sport_name -> sport_data
                                                        sport_data_map = {s["name"]: s for s in sports_options}
                                                        
                                                        selected_sport_name = st.selectbox(
                                                            "Seleziona",
                                                            options=sport_names,
                                                            key=f"{field['id']}_{i}",
                                                            label_visibility="collapsed"
                                                        )
                                                        
                                                        # Memorizza sia il nome che la chiave dello sport
                                                        if selected_sport_name:
                                                            sport_data[field["id"]] = {
                                                                "name": selected_sport_name,
                                                                "key": sport_data_map[selected_sport_name]["key"],
                                                                "kcal_per_hour": sport_data_map[selected_sport_name]["kcal_per_hour"],
                                                                "description": sport_data_map[selected_sport_name]["description"]
                                                            }
                                                        else:
                                                            sport_data[field["id"]] = None
                                                elif field["id"] == "intensity":
                                                    # Mostra le descrizioni per l'intensità
                                                    intensity_options = field["options"]
                                                    intensity_descriptions = field.get("descriptions", {})
                                                    
                                                    # Crea opzioni formattate con descrizioni
                                                    formatted_options = [f"{opt} - {intensity_descriptions.get(opt, '')}" 
                                                                        for opt in intensity_options]
                                                    
                                                    # Mostra il selectbox con le descrizioni
                                                    formatted_selection = st.selectbox(
                                                        "Seleziona",
                                                        options=formatted_options,
                                                        key=f"{field['id']}_{i}",
                                                        label_visibility="collapsed"
                                                    )
                                                    
                                                    # Estrai solo il valore dell'intensità (prima del trattino)
                                                    selected_intensity = formatted_selection.split(' - ')[0] if formatted_selection else None
                                                    sport_data[field["id"]] = selected_intensity
                                                else:
                                                    sport_data[field["id"]] = st.selectbox(
                                                        "Seleziona",
                                                        options=field["options"],
                                                        key=f"{field['id']}_{i}",
                                                        label_visibility="collapsed"
                                                    )
                                            elif field["type"] == "number":
                                                sport_data[field["id"]] = st.number_input(
                                                    "Numero",
                                                    min_value=field["min"],
                                                    max_value=field["max"],
                                                    value=field["default"],
                                                    key=f"{field['id']}_{i}",
                                                    label_visibility="collapsed"
                                                )
                                            elif field["type"] == "text":
                                                sport_data[field["id"]] = st.text_input(
                                                    "Testo",
                                                    "",
                                                    key=f"{field['id']}_{i}",
                                                    label_visibility="collapsed"
                                                )
                                    
                                    # Aggiorna lo sport con i dati attuali
                                    for key, value in sport_data.items():
                                        sport[key] = value
                                    
                                    follow_up_answer.append(sport_data)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("Aggiungi altro sport"):
                                        st.session_state.sports_list.append({})
                                        st.rerun()
                                with col2:
                                    if len(st.session_state.sports_list) > 1 and st.button("Rimuovi ultimo sport"):
                                        st.session_state.sports_list.pop()
                                        st.rerun()
                            else:
                                # Gestione vecchio formato strutturato
                                follow_up_answer = {}
                                for field in current_q["follow_up"]["fields"]:
                                    show_field = True
                                    if "show_if" in field and "show_if_value" in field:
                                        ref_value = follow_up_answer.get(field["show_if"])
                                        show_field = ref_value == field["show_if_value"]
                                    
                                    if show_field:
                                        st.markdown(f"### {field['label']}")
                                        if field["type"] == "select":
                                            follow_up_answer[field["id"]] = st.selectbox(
                                                "",
                                                options=field["options"]
                                            )
                                        elif field["type"] == "number":
                                            follow_up_answer[field["id"]] = st.number_input(
                                                "",
                                                min_value=field["min"],
                                                max_value=field["max"],
                                                value=field["default"]
                                            )
                                        elif field["type"] == "text":
                                            follow_up_answer[field["id"]] = st.text_input("")
                                        elif field["type"] == "dynamic_time":
                                            # Get the number of meals from the previous field
                                            num_meals = follow_up_answer.get("num_meals", 3)
                                            meal_times = {}
                                            
                                            # Define meal order and labels based on number of meals
                                            meal_order = {
                                                1: ["Pranzo"],
                                                2: ["Pranzo", "Cena"],
                                                3: ["Colazione", "Pranzo", "Cena"],
                                                4: ["Colazione", "Pranzo", "Cena", "Spuntino pomeridiano"],
                                                5: ["Colazione", "Spuntino mattutino", "Pranzo", "Spuntino pomeridiano", "Cena"],
                                                6: ["Colazione", "Spuntino mattutino", "Pranzo", "Spuntino pomeridiano", "Cena", "Altro Spuntino"]
                                            }
                                            
                                            # Get the appropriate meal labels for the selected number of meals
                                            meal_labels = meal_order.get(num_meals, [])
                                            
                                            # Create time input for each meal
                                            for i, label in enumerate(meal_labels):
                                                st.markdown(f"### {label}")
                                                # Create time input with full day range (00:00 - 23:59)
                                                # Set default times based on meal type
                                                default_times = {
                                                    "Colazione": "07:30",
                                                    "Spuntino mattutino": "10:30",
                                                    "Pranzo": "13:00",
                                                    "Spuntino pomeridiano": "16:30",
                                                    "Cena": "20:00",
                                                    "Altro Spuntino": "22:00"
                                                }
                                                
                                                # Convert default time string to datetime.time object
                                                default_time = datetime.strptime(default_times[label], "%H:%M").time()
                                                
                                                time_value = st.time_input(
                                                    "",
                                                    value=default_time,
                                                    key=f"meal_time_{current_q['id']}_{label}_{i}",
                                                    label_visibility="collapsed"
                                                )
                                                meal_times[label] = time_value
                                            
                                            follow_up_answer[field["id"]] = {
                                                label: time_val.strftime("%H:%M") if time_val else None 
                                                for label, time_val in meal_times.items()
                                            }
                    
                    if st.button("Avanti"):
                        # Salva la risposta
                        st.session_state.nutrition_answers[current_q["id"]] = {
                            "answer": answer,
                            "follow_up": follow_up_answer
                        }
                        
                        # Salva le risposte nutrizionali
                        st.session_state.user_data_manager.save_nutritional_info(
                            st.session_state.user_info["id"],
                            {
                                **{k: v for k, v in st.session_state.user_info.items() if k not in ["id", "username"]},
                                "nutrition_answers": st.session_state.nutrition_answers
                            }
                        )
                        
                        st.session_state.current_question += 1
                        st.rerun()
                        
                elif current_q["type"] == "number_input":
                    # Per domande con campi numerici multipli
                    question_text = current_q["question"](st.session_state.user_info) if callable(current_q["question"]) else current_q["question"]
                    st.markdown(f"### {question_text}")
                    
                    field_values = {}
                    for field in current_q["fields"]:
                        label = field["label"](st.session_state.user_info) if callable(field["label"]) else field["label"]
                        st.markdown(f"### {label}")
                        field_values[field["id"]] = st.number_input(
                            "",
                            min_value=field["min"],
                            max_value=field["max"],
                            value=field["default"]
                        )
                    
                    if st.button("Avanti"):
                        st.session_state.nutrition_answers[current_q["id"]] = field_values
                        
                        # Salva le risposte nutrizionali
                        st.session_state.user_data_manager.save_nutritional_info(
                            st.session_state.user_info["id"],
                            {
                                **{k: v for k, v in st.session_state.user_info.items() if k not in ["id", "username"]},
                                "nutrition_answers": st.session_state.nutrition_answers
                            }
                        )
                        
                        st.session_state.current_question += 1
                        st.rerun()
            else:
                # Salta la domanda se non deve essere mostrata
                st.session_state.current_question += 1
                st.rerun()
        else:
            # Se non ci sono ancora messaggi, carica la history esistente
            if not st.session_state.messages:
                chat_history = st.session_state.user_data_manager.get_chat_history(st.session_state.user_info["id"])
                if chat_history:
                    st.session_state.messages = [
                        {"role": msg.role, "content": msg.content}
                        for msg in chat_history
                    ]
                else:
                    # Se non c'è history, invia il prompt iniziale
                    initial_prompt = f"""
                    Iniziamo una nuova consulenza nutrizionale.

                    Mostra SEMPRE i calcoli in questo formato semplice:

                    Uso simboli:
                    - MAI: \times  → USA SEMPRE: *
                    - MAI: \\text{{}} → USA SEMPRE: testo normale
                    - MAI: [ ]     → USA SEMPRE: parentesi tonde ( )
                    - MAI: \\      → USA SEMPRE: testo normale
                    - MAI: \\frac{{}} → USA SEMPRE: divisione con /
                    - MAI: \ g, \ kcal, \ ml, \ cm → NON USARE mai il backslash prima delle unità di misura
                    → Scrivi SEMPRE "g", "kcal", "ml", "cm" senza alcun simbolo speciale

                    DATI DEL CLIENTE:
                    • Età: {st.session_state.user_info['età']} anni
                    • Sesso: {st.session_state.user_info['sesso']}
                    • Peso attuale: {st.session_state.user_info['peso']} kg
                    • Altezza: {st.session_state.user_info['altezza']} cm
                    • Livello attività quotidiana: {st.session_state.user_info['attività']}
                      (esclusa attività sportiva che verrà valutata separatamente)
                    • Obiettivo principale: {st.session_state.user_info['obiettivo']}

                    RISPOSTE ALLE DOMANDE INIZIALI:
                    {json.dumps(st.session_state.nutrition_answers, indent=2)}

                    PREFERENZE ALIMENTARI:
                    {json.dumps(st.session_state.user_info['preferences'], indent=2)}
                    Basandoti su queste informazioni, procedi con le seguenti fasi:

                    FASE 1: Analisi delle risposte fornite
                    - Valuta dati del cliente iniziali 
                    - Valuta le preferenze alimentari
                    - Valuta le intolleranze/allergie
                    - Considera gli obiettivi di peso e il tempo
                    - Valuta le attività sportive praticate
                    - Definisci il numero di pasti preferito e orari (se specificati)

                    FASE 2: Calcolo del fabbisogno energetico
                    - Calcola il metabolismo basale
                    - Considera il livello di attività fisica
                    - Aggiungi il dispendio energetico degli sport
                    - Determina il fabbisogno calorico totale

                    FASE 3: Calcolo macronutrienti
                    - Distribuisci le calorie tra i macronutrienti

                    FASE 4: Distribuzione calorie tra i pasti
                    - Verifica se l'utente ha specificato un numero di pasti e orari
                    - In base al numero di pasti e orari, distribuisci le calorie tra i pasti
                    - Non inserire alcun alimento specifico o macronutrienti in questa fase, solo la distribuzione delle calorie

                    FASE 5: Distribuzione macronutrienti tra i pasti
                    - Controlla i macronutrienti totali giornalieri e la distribuzione calorica ottenuta nella fase 4
                    - Distribuisci i macronutrienti tra i pasti in base ai principi base
                    - Applica i principi di modifica in base ai tipi di pasti e sport praticati
                    - Non inserire alcun alimento specifico, solo la distribuzione delle calorie e dei macronutrienti in questa fase

                    FASE 6: Creazione singoli pasti
                    - Adatta il piano alle preferenze alimentari
                    - Crea un pasto alla volta
                    - Prenditi il tempo necessario per realizzare un pasto completo
                    - Verifica il pasto 

                    Puoi procedere con la FASE 1?
                    """
                    
                    # Crea un nuovo thread solo se non esiste già
                    if not hasattr(st.session_state, 'thread_id'):
                        create_new_thread()
                    
                    # Invia il prompt iniziale
                    response = chat_with_assistant(initial_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Salva il messaggio nella history
                    st.session_state.user_data_manager.save_chat_message(
                        st.session_state.user_info["id"],
                        "assistant",
                        response
                    )
                    st.rerun()
            
            # Mostra la cronologia dei messaggi
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Input per nuovi messaggi
            user_input = st.chat_input("Scrivi un messaggio...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                # Salva il messaggio dell'utente nella history
                st.session_state.user_data_manager.save_chat_message(
                    st.session_state.user_info["id"],
                    "user",
                    user_input
                )
                with st.spinner("L'assistente sta elaborando la risposta..."):
                    response = chat_with_assistant(user_input)
                    st.session_state.messages.append({"role": "assistant", "content": response})
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
                st.rerun()
    else:
        st.info("👈 Per iniziare, inserisci le tue informazioni nella barra laterale")

def main():
    st.title("NutriCoach - Il tuo assistente nutrizionale personale 🥗")
    
    # Gestione login/registrazione
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    if not st.session_state.user_info:
        tab1, tab2 = st.tabs(["Login", "Registrazione"])
        
        with tab1:
            with st.form("login_form"):
                st.write("Accedi al tuo account")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Accedi"):
                    success, result = st.session_state.user_data_manager.login_user(username, password)
                    if success:
                        # Carica le informazioni nutrizionali salvate
                        nutritional_info = st.session_state.user_data_manager.get_nutritional_info(result)
                        
                        # Imposta le informazioni dell'utente
                        st.session_state.user_info = {
                            "id": result,
                            "username": username
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
                                "preferences": st.session_state.user_data_manager.get_user_preferences(result)  # Aggiungi le preferenze
                            })
                            
                            # Carica le risposte nutrizionali
                            if nutritional_info.nutrition_answers:
                                st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                                st.session_state.current_question = len(NUTRITION_QUESTIONS)
                        
                        st.rerun()
                    else:
                        st.error(result)
        
        with tab2:
            with st.form("register_form"):
                st.write("Crea un nuovo account")
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Conferma password", type="password")
                
                if st.form_submit_button("Registrati"):
                    if new_password != confirm_password:
                        st.error("Le password non coincidono")
                    else:
                        success, result = st.session_state.user_data_manager.register_user(new_username, new_password)
                        if success:
                            st.success("Registrazione completata! Ora puoi accedere.")
                        else:
                            st.error(result)
    
    # Se l'utente è autenticato, mostra l'interfaccia principale
    if st.session_state.user_info:
        # Sidebar per le funzionalità utente
        with st.sidebar:
            st.header("Menu")
            page = st.radio(
                "Seleziona una sezione",
                ["Piano Nutrizionale", "Progressi", "Preferenze"]
            )
            
            # Aggiungi pulsante logout
            if st.button("Logout"):
                st.session_state.user_info = None
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
                st.rerun()
        
        if page == "Piano Nutrizionale":
            chat_interface()
        elif page == "Progressi":
            track_user_progress()
            show_progress_history()
        elif page == "Preferenze":
            handle_preferences()

if __name__ == "__main__":
    main() 