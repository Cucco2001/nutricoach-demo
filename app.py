import streamlit as st
import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI
from nutricoach_agent import available_tools, system_prompt
from nutridb_tool import nutridb_tool

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
    st.session_state.user_info = {}
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
        "id": "participation",
        "question": "Vuoi partecipare attivamente alla creazione del piano alimentare?",
        "type": "radio",
        "options": ["No", "Sì"]
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
        "follow_up": "Specifica quale sport e quante ore alla settimana:",
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
                
                # Esegui la funzione appropriata
                if function_name == "nutridb_tool":
                    result = nutridb_tool(**arguments)
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
    """Crea un nuovo thread per la conversazione."""
    try:
        thread = st.session_state.openai_client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state.current_run_id = None
        st.session_state.messages = []
        st.session_state.current_question = 0
        st.session_state.nutrition_answers = {}
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
        # Se non esiste un thread, creane uno nuovo
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
            # Se c'è un errore nel thread, creane uno nuovo e riprova
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
                progress_text = "Elaborazione in corso..."
                
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
                        
                        # Aggiorna il messaggio di progresso
                        elapsed = int(time.time() - start_time)
                        st.write(f"{progress_text} ({elapsed}s)")
                        
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

# Interfaccia principale
def main():
    st.title("🥗 NutriCoach")
    st.subheader("Il tuo assistente nutrizionale personale")
    
    # Crea l'assistente
    create_assistant()
    
    # Sidebar per le informazioni dell'utente
    with st.sidebar:
        st.subheader("Le tue informazioni")
        if not st.session_state.user_info:
            with st.form("user_info_form"):
                st.write("Per iniziare, inserisci i tuoi dati:")
                età = st.number_input("Età", 18, 100, 30)
                sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])
                peso = st.number_input("Peso (kg)", min_value=40, max_value=200, value=70, step=1)
                altezza = st.number_input("Altezza (cm)", 140, 220, 170)
                attività = st.selectbox("Livello di attività fisica (a parte sport praticato)",
                                      ["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"])
                obiettivo = st.selectbox("Obiettivo",
                                       ["Perdita di peso", "Mantenimento", "Aumento di massa"])
                
                if st.form_submit_button("Inizia"):
                    st.session_state.user_info = {
                        "età": età,
                        "sesso": sesso,
                        "peso": peso,
                        "altezza": altezza,
                        "attività": attività,
                        "obiettivo": obiettivo
                    }
                    # Crea un nuovo thread quando si inizia una nuova consulenza
                    create_new_thread()
                    st.rerun()
        else:
            # Mostra le informazioni dell'utente
            st.write("Dati inseriti:")
            for key, value in st.session_state.user_info.items():
                if key == "peso":
                    st.write(f"Peso: {int(value)} kg")
                else:
                    st.write(f"{key.capitalize()}: {value}")
            if st.button("Modifica dati"):
                st.session_state.user_info = {}
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
                st.rerun()
    
    # Area principale della chat
    if st.session_state.user_info:
        if st.session_state.current_question < len(NUTRITION_QUESTIONS):
            current_q = NUTRITION_QUESTIONS[st.session_state.current_question]
            
            # Verifica se la domanda deve essere mostrata in base alle condizioni
            show_question = True
            if "show_if" in current_q:
                show_question = current_q["show_if"](st.session_state.user_info)
            
            if show_question:
                st.write("### Domanda " + str(st.session_state.current_question + 1))
                
                # Gestisce la domanda in base al tipo
                if current_q["type"] == "radio":
                    # Mostra la domanda principale
                    answer = st.radio(current_q["question"], current_q["options"])
                    
                    # Gestisce eventuali follow-up
                    follow_up_answer = None
                    if "follow_up" in current_q and answer == current_q["show_follow_up_on"]:
                        follow_up_answer = st.text_input(current_q["follow_up"])
                    
                    if st.button("Avanti"):
                        # Salva la risposta
                        st.session_state.nutrition_answers[current_q["id"]] = {
                            "answer": answer,
                            "follow_up": follow_up_answer
                        }
                        st.session_state.current_question += 1
                        st.rerun()
                        
                elif current_q["type"] == "number_input":
                    # Per domande con campi numerici multipli
                    question_text = current_q["question"](st.session_state.user_info) if callable(current_q["question"]) else current_q["question"]
                    st.write(question_text)
                    
                    field_values = {}
                    for field in current_q["fields"]:
                        label = field["label"](st.session_state.user_info) if callable(field["label"]) else field["label"]
                        field_values[field["id"]] = st.number_input(
                            label,
                            min_value=field["min"],
                            max_value=field["max"],
                            value=field["default"]
                        )
                    
                    if st.button("Avanti"):
                        st.session_state.nutrition_answers[current_q["id"]] = field_values
                        st.session_state.current_question += 1
                        st.rerun()
        else:
            # Se non ci sono ancora messaggi, invia il prompt iniziale
            if not st.session_state.messages:
                initial_prompt = f"""
                Iniziamo una nuova consulenza nutrizionale.

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

                Basandoti su queste informazioni, procedi con:
                1. Analisi delle risposte fornite
                2. Calcolo del fabbisogno energetico considerando anche l'attività sportiva
                3. Creazione del piano alimentare personalizzato

                Puoi procedere con la prima fase?
                """
                
                # Crea un nuovo thread solo se non esiste già
                if not hasattr(st.session_state, 'thread_id'):
                    create_new_thread()
                
                # Invia il prompt iniziale
                response = chat_with_assistant(initial_prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
            # Mostra la cronologia dei messaggi
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Input per nuovi messaggi
            user_input = st.chat_input("Scrivi un messaggio...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.spinner("L'assistente sta elaborando la risposta..."):
                    response = chat_with_assistant(user_input)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    else:
        st.info("👈 Per iniziare, inserisci le tue informazioni nella barra laterale")

if __name__ == "__main__":
    main() 