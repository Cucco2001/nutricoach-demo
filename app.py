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
if "thread_id" not in st.session_state:
    # Crea un nuovo thread per la conversazione
    thread = st.session_state.openai_client.beta.threads.create()
    st.session_state.thread_id = thread.id

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

def chat_with_assistant(user_input):
    """Gestisce la conversazione con l'assistente."""
    try:
        # Aggiungi il messaggio dell'utente al thread
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
                
                # Attendi il completamento con timeout più lungo
                start_time = time.time()
                timeout = 180  # aumentato a 180 secondi (3 minuti)
                progress_text = "Elaborazione in corso..."
                
                with st.empty():
                    while True:
                        if time.time() - start_time > timeout:
                            st.error("L'operazione sta impiegando troppo tempo. Riprova con una richiesta più semplice o dividi la richiesta in parti più piccole.")
                            return "Mi dispiace, l'operazione è durata troppo a lungo. Per favore, prova a:\n1. Dividere la richiesta in parti più piccole\n2. Fare una domanda alla volta\n3. Specificare meglio cosa ti serve"
                        
                        run_status = st.session_state.openai_client.beta.threads.runs.retrieve(
                            thread_id=st.session_state.thread_id,
                            run_id=run.id
                        )
                        
                        # Aggiorna il messaggio di progresso
                        elapsed = int(time.time() - start_time)
                        st.write(f"{progress_text} ({elapsed}s)")
                        
                        if run_status.status == 'completed':
                            break
                        elif run_status.status == 'failed':
                            raise Exception("Run failed")
                        elif run_status.status == 'expired':
                            raise Exception("Run expired")
                        elif run_status.status == 'requires_action':
                            # Gestisci le chiamate ai tool
                            tool_outputs = handle_tool_calls(run_status)
                            if tool_outputs:
                                # Invia i risultati e continua
                                st.session_state.openai_client.beta.threads.runs.submit_tool_outputs(
                                    thread_id=st.session_state.thread_id,
                                    run_id=run.id,
                                    tool_outputs=tool_outputs
                                )
                            else:
                                raise Exception("Errore nella gestione dei tool")
                        
                        # Breve pausa prima del prossimo controllo
                        time.sleep(1)
                
                # Ottieni la risposta
                messages = st.session_state.openai_client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                return messages.data[0].content[0].text.value
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    st.error(f"Errore dopo {max_retries} tentativi: {str(e)}")
                    return "Mi dispiace, si è verificato un errore. Riprova tra qualche momento."
                time.sleep(2 ** retry_count)  # Exponential backoff
        
    except Exception as e:
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
                    # Invia le informazioni all'assistente
                    initial_prompt = f"""
                    Ho un nuovo cliente con le seguenti caratteristiche:
                    - Età: {età} anni
                    - Sesso: {sesso}
                    - Peso: {peso} kg
                    - Altezza: {altezza} cm
                    - Livello di attività: {attività}
                    - Obiettivo: {obiettivo}
                    
                    Per favore, fai le domande necessarie per creare un piano alimentare personalizzato.
                    """
                    response = chat_with_assistant(initial_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
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
                st.rerun()
    
    # Area principale della chat
    if st.session_state.user_info:
        # Mostra la cronologia dei messaggi
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Input per nuovi messaggi
        user_input = st.chat_input("Scrivi un messaggio...")
        if user_input:
            # Aggiungi il messaggio dell'utente alla cronologia
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Ottieni la risposta dall'assistente
            with st.spinner("L'assistente sta elaborando la risposta..."):
                response = chat_with_assistant(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Aggiorna l'interfaccia
            st.rerun()
    else:
        st.info("👈 Per iniziare, inserisci le tue informazioni nella barra laterale")

if __name__ == "__main__":
    main() 