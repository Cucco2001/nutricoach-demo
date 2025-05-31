import streamlit as st
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from nutricoach_agent import available_tools, system_prompt
from agent_tools.user_data_manager import UserDataManager
from datetime import datetime
from agent_tools.nutridb_tool import (
    get_macros, get_LARN_protein, get_standard_portion, 
    get_weight_from_volume, get_fattore_cottura, get_LARN_fibre, 
    get_LARN_lipidi_percentuali, get_LARN_vitamine, 
    compute_Harris_Benedict_Equation, get_protein_multiplier,
    calculate_sport_expenditure, calculate_weight_goal_calories, 
    analyze_bmi_and_goals, check_vitamins, get_food_substitutes, check_ultraprocessed_foods
)
from agent_tools.user_data_tool import (
    get_user_preferences, get_progress_history, get_agent_qa, get_nutritional_info
)
# Import dai nuovi moduli frontend
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from frontend.sports_frontend import load_sports_data, get_sports_by_category, on_sport_category_change
import threading
import queue

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

# Variabili per gestione generazione agente in background
if "agent_generating" not in st.session_state:
    st.session_state.agent_generating = False
if "agent_response_ready" not in st.session_state:
    st.session_state.agent_response_ready = False
if "agent_response_text" not in st.session_state:
    st.session_state.agent_response_text = None
if "agent_user_input" not in st.session_state:
    st.session_state.agent_user_input = None
if "agent_thread_id" not in st.session_state:
    st.session_state.agent_thread_id = None

# Inizializzazione DeepSeek client per estrazione dati nutrizionali
if "deepseek_client" not in st.session_state:
    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            st.warning("⚠️ DEEPSEEK_API_KEY non trovata nel file .env. Il sistema di estrazione automatica dei dati nutrizionali sarà disabilitato.")
            st.session_state.deepseek_client = None
        else:
            st.session_state.deepseek_client = OpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com"
            )
    except Exception as e:
        st.error(f"Errore nell'inizializzazione del client DeepSeek: {str(e)}")
        st.session_state.deepseek_client = None
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "last_extraction_count" not in st.session_state:
    st.session_state.last_extraction_count = 0
if "deepseek_queue" not in st.session_state:
    st.session_state.deepseek_queue = queue.Queue()
if "deepseek_results" not in st.session_state:
    st.session_state.deepseek_results = {}

# Variabili globali per la comunicazione tra thread (non possono usare session_state)
deepseek_results_queue = queue.Queue()
deepseek_lock = threading.Lock()
file_access_lock = threading.Lock()  # Lock per accesso ai file utente

def extract_nutritional_data_with_deepseek(conversation_history, user_info):
    """
    Usa DeepSeek per estrarre automaticamente i dati nutrizionali dalla conversazione.
    
    Args:
        conversation_history: Lista delle domande/risposte dell'agente
        user_info: Informazioni dell'utente
        
    Returns:
        Dict con i dati nutrizionali estratti
    """
    try:
        # Prepara il contesto della conversazione
        conversation_text = "\n\n".join([
            f"UTENTE: {qa.question}\nAGENTE: {qa.answer}" 
            for qa in conversation_history[-10:]  # Ultimi 10 scambi
        ])
        
        # Prompt per DeepSeek
        extraction_prompt = f"""
Analizza questa conversazione tra un nutrizionista AI e un utente per estrarre i dati nutrizionali calcolati.

INFORMAZIONI UTENTE:
- Età: {user_info.get('età', 'N/A')} anni
- Sesso: {user_info.get('sesso', 'N/A')}
- Peso: {user_info.get('peso', 'N/A')} kg
- Altezza: {user_info.get('altezza', 'N/A')} cm
- Obiettivo: {user_info.get('obiettivo', 'N/A')}

CONVERSAZIONE:
{conversation_text}

ESTRAI E RESTITUISCI SOLO UN JSON CON I SEGUENTI DATI (se presenti nella conversazione):

{{
    "caloric_needs": {{
        "bmr": numero_metabolismo_basale,
        "fabbisogno_base": numero_fabbisogno_senza_sport,
        "dispendio_sportivo": numero_calorie_da_sport,
        "aggiustamento_obiettivo": numero_deficit_o_surplus,
        "fabbisogno_totale": numero_calorie_finali,
        "laf_utilizzato": numero_fattore_attivita
    }},
    "macros_total": {{
        "kcal_totali": numero,
        "proteine_g": numero,
        "proteine_kcal": numero,
        "proteine_percentuale": numero,
        "grassi_g": numero,
        "grassi_kcal": numero, 
        "grassi_percentuale": numero,
        "carboidrati_g": numero,
        "carboidrati_kcal": numero,
        "carboidrati_percentuale": numero,
        "fibre_g": numero
    }},
    "daily_macros": {{
        "numero_pasti": numero,
        "distribuzione_pasti": {{
            "nome_pasto": {{
                "orario": "HH:MM",
                "kcal": numero,
                "percentuale_kcal": numero,
                "proteine_g": numero,
                "carboidrati_g": numero,
                "grassi_g": numero
            }}
        }}
    }},
    "registered_meals": [
        {{
            "nome_pasto": "colazione/pranzo/cena/spuntino",
            "orario": "HH:MM",
            "alimenti": [
                {{
                    "nome_alimento": "nome",
                    "quantita_g": numero,
                    "stato": "crudo/cotto",
                    "metodo_cottura": "se_applicabile",
                    "misura_casalinga": "equivalenza",
                    "macronutrienti": {{
                        "proteine": numero,
                        "carboidrati": numero, 
                        "grassi": numero,
                        "kcal": numero
                    }}
                }}
            ],
            "totali_pasto": {{
                "kcal_totali": numero,
                "proteine_totali": numero,
                "carboidrati_totali": numero,
                "grassi_totali": numero
            }}
        }}
    ]
}}

IMPORTANTE:
- Restituisci SOLO il JSON, nessun altro testo
- Se un dato non è presente, ometti quella sezione
- I numeri devono essere numerici, non stringhe
- Cerca con attenzione i calcoli numerici nella conversazione
"""

        # Chiamata a DeepSeek
        response = st.session_state.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Sei un esperto estrattore di dati nutrizionali. Estrai accuratamente i dati dalle conversazioni nutrizionali e restituisci solo JSON valido."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        # Estrai il JSON dalla risposta
        response_text = response.choices[0].message.content.strip()
        
        # Pulisci la risposta per estrarre solo il JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
            
        # Parse del JSON
        extracted_data = json.loads(response_text)
        
        print(f"[DEEPSEEK] Dati estratti con successo: {list(extracted_data.keys())}")
        return extracted_data
        
    except Exception as e:
        print(f"[DEEPSEEK] Errore nell'estrazione: {str(e)}")
        return {}

def save_extracted_nutritional_data(user_id, extracted_data):
    """
    Salva i dati nutrizionali estratti nel file utente facendo un merge con i dati esistenti.
    
    Args:
        user_id: ID dell'utente
        extracted_data: Dati estratti da DeepSeek
    """
    try:
        # Usa lock globale per evitare conflitti con il user_data_manager
        with file_access_lock:
            print(f"[DEEPSEEK_SAVE] Inizio salvataggio per user {user_id}")
            
            # Carica il file utente
            user_file_path = f"user_data/{user_id}.json"
            
            if not os.path.exists(user_file_path):
                print(f"[DEEPSEEK_SAVE] File utente {user_id} non trovato")
                return False
            
            # Operazione atomica: leggi, modifica, scrivi tutto sotto lock
            with open(user_file_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # Crea una copia di backup dei dati nutrizionali esistenti
            existing_nutritional_data = user_data.get("nutritional_info_extracted", {}).copy()
            print(f"[DEEPSEEK_SAVE] Backup dati esistenti: {list(existing_nutritional_data.keys())}")
            
            # Inizializza la sezione nutritional_info_extracted se non esiste
            if "nutritional_info_extracted" not in user_data:
                user_data["nutritional_info_extracted"] = {}
            
            # Ripristina i dati esistenti dalla copia di backup
            user_data["nutritional_info_extracted"] = existing_nutritional_data.copy()
            
            # Merge/update dei dati invece di sostituirli completamente
            changes_made = False
            for data_type, data_content in extracted_data.items():
                if data_content:  # Solo se ci sono dati
                    if data_type in user_data["nutritional_info_extracted"]:
                        # Se il tipo di dato esiste già, fai un merge intelligente
                        if isinstance(data_content, dict) and isinstance(user_data["nutritional_info_extracted"][data_type], dict):
                            # Conta le chiavi prima e dopo per vedere se ci sono cambiamenti
                            keys_before = set(user_data["nutritional_info_extracted"][data_type].keys())
                            user_data["nutritional_info_extracted"][data_type].update(data_content)
                            keys_after = set(user_data["nutritional_info_extracted"][data_type].keys())
                            if keys_before != keys_after or any(k in data_content for k in keys_before):
                                changes_made = True
                                print(f"[DEEPSEEK_SAVE] Aggiornato (merge) {data_type} per utente {user_id}")
                        elif isinstance(data_content, list) and isinstance(user_data["nutritional_info_extracted"][data_type], list):
                            # Per le liste (come registered_meals), sostituisci solo se i nuovi dati sono più completi
                            if len(data_content) >= len(user_data["nutritional_info_extracted"][data_type]):
                                user_data["nutritional_info_extracted"][data_type] = data_content
                                changes_made = True
                                print(f"[DEEPSEEK_SAVE] Sostituito (lista più completa) {data_type} per utente {user_id}")
                            else:
                                print(f"[DEEPSEEK_SAVE] Mantenuto {data_type} esistente (più completo) per utente {user_id}")
                        else:
                            # Sostituisci per altri tipi o se i tipi non corrispondono
                            user_data["nutritional_info_extracted"][data_type] = data_content
                            changes_made = True
                            print(f"[DEEPSEEK_SAVE] Sostituito {data_type} per utente {user_id}")
                    else:
                        # Se il tipo di dato non esiste, aggiungilo
                        user_data["nutritional_info_extracted"][data_type] = data_content
                        changes_made = True
                        print(f"[DEEPSEEK_SAVE] Aggiunto nuovo {data_type} per utente {user_id}")
            
            # Aggiorna il timestamp dell'ultimo aggiornamento solo se ci sono stati dei cambiamenti
            if changes_made:
                user_data["nutritional_info_extracted"]["last_updated"] = datetime.now().isoformat()
                print(f"[DEEPSEEK_SAVE] Timestamp aggiornato per utente {user_id}")
            
            # Verifica finale che i dati non siano vuoti prima del salvataggio
            if not user_data["nutritional_info_extracted"]:
                print(f"[DEEPSEEK_SAVE] ERRORE: Dati nutritional_info_extracted vuoti prima del salvataggio!")
                user_data["nutritional_info_extracted"] = existing_nutritional_data  # Ripristina backup
            
            final_keys = list(user_data["nutritional_info_extracted"].keys())
            print(f"[DEEPSEEK_SAVE] Dati finali da salvare: {final_keys}")
            
            # Salva il file aggiornato SOLO se ci sono stati cambiamenti
            if changes_made or not existing_nutritional_data:
                with open(user_file_path, 'w', encoding='utf-8') as f:
                    json.dump(user_data, f, indent=2, ensure_ascii=False)
                print(f"[DEEPSEEK_SAVE] File salvato con successo per utente {user_id}")
            else:
                print(f"[DEEPSEEK_SAVE] Nessun cambiamento, file non modificato per utente {user_id}")
                
            print(f"[DEEPSEEK_SAVE] Completato salvataggio per user {user_id}")
            return True
        
    except Exception as e:
        print(f"[DEEPSEEK_SAVE] Errore nel salvataggio per utente {user_id}: {str(e)}")
        return False

def check_and_extract_nutritional_data_async(user_id):
    """
    Versione asincrona che avvia l'estrazione DeepSeek in un thread separato
    per non bloccare l'interfaccia utente.
    
    Args:
        user_id: ID dell'utente
    """
    try:
        # Verifica se DeepSeek è disponibile
        if not st.session_state.deepseek_client:
            return
        
        # Incrementa il contatore delle interazioni
        st.session_state.interaction_count += 1
        
        # Controlla se sono passate 2 interazioni dall'ultima estrazione
        interactions_since_last = st.session_state.interaction_count - st.session_state.last_extraction_count
        
        if interactions_since_last >= 2:
            print(f"[MONITOR] Avvio estrazione dati asincrona dopo {interactions_since_last} interazioni")
            
            # Ottieni la storia delle conversazioni
            conversation_history = st.session_state.user_data_manager.get_agent_qa(user_id)
            
            if conversation_history and len(conversation_history) >= 2:  # Almeno 2 scambi
                # Crea una copia locale dei dati utente per il thread (non può usare session_state)
                user_info_copy = dict(st.session_state.user_info) if st.session_state.user_info else {}
                current_interaction_count = st.session_state.interaction_count
                
                # Avvia thread per estrazione DeepSeek
                def extract_in_background():
                    try:
                        # Crea client DeepSeek locale (non può usare session_state)
                        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
                        if not deepseek_api_key:
                            print("[BACKGROUND] DEEPSEEK_API_KEY non trovata")
                            return
                            
                        local_client = OpenAI(
                            api_key=deepseek_api_key,
                            base_url="https://api.deepseek.com"
                        )
                        
                        # Estrai i dati (usa client locale e copia dei dati utente)
                        extracted_data = extract_nutritional_data_with_deepseek_local(
                            conversation_history, 
                            user_info_copy,  # Usa la copia invece del session_state
                            local_client
                        )
                        
                        if extracted_data:
                            success = save_extracted_nutritional_data(user_id, extracted_data)
                            
                            # Usa la coda globale invece del session_state
                            with deepseek_lock:
                                deepseek_results_queue.put({
                                    "success": success,
                                    "user_id": user_id,
                                    "interaction_count": current_interaction_count
                                })
                    except Exception as e:
                        print(f"[BACKGROUND] Errore nell'estrazione: {str(e)}")
                        with deepseek_lock:
                            deepseek_results_queue.put({
                                "success": False,
                                "error": str(e)
                            })
                
                # Avvia il thread
                thread = threading.Thread(target=extract_in_background, daemon=True)
                thread.start()
                
                # Mostra notifica che l'estrazione è iniziata
                st.info("📊 Estrazione dati nutrizionali avviata in background...")
                
                # Aggiungi info discreta per debugging
                print(f"[MONITOR] Thread DeepSeek avviato per user {user_id}")
                
    except Exception as e:
        print(f"[MONITOR] Errore nel monitoraggio asincrono: {str(e)}")

def extract_nutritional_data_with_deepseek_local(conversation_history, user_info, client):
    """
    Versione locale di extract_nutritional_data_with_deepseek che usa un client passato come parametro
    invece di session_state (per uso nei thread).
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Prepara il contesto della conversazione
            conversation_text = "\n\n".join([
                f"UTENTE: {qa.question}\nAGENTE: {qa.answer}" 
                for qa in conversation_history[-10:]  # Ultimi 10 scambi
            ])
            
            # Prompt per DeepSeek
            extraction_prompt = f"""
Analizza questa conversazione tra un nutrizionista AI e un utente per estrarre i dati nutrizionali calcolati.

INFORMAZIONI UTENTE:
- Età: {user_info.get('età', 'N/A')} anni
- Sesso: {user_info.get('sesso', 'N/A')}
- Peso: {user_info.get('peso', 'N/A')} kg
- Altezza: {user_info.get('altezza', 'N/A')} cm
- Obiettivo: {user_info.get('obiettivo', 'N/A')}

CONVERSAZIONE:
{conversation_text}

ESTRAI E RESTITUISCI SOLO UN JSON CON I SEGUENTI DATI (se presenti nella conversazione):

{{
    "caloric_needs": {{
        "bmr": numero_metabolismo_basale,
        "fabbisogno_base": numero_fabbisogno_senza_sport,
        "dispendio_sportivo": numero_calorie_da_sport,
        "aggiustamento_obiettivo": numero_deficit_o_surplus,
        "fabbisogno_totale": numero_calorie_finali,
        "laf_utilizzato": numero_fattore_attivita
    }},
    "macros_total": {{
        "kcal_totali": numero,
        "proteine_g": numero,
        "proteine_kcal": numero,
        "proteine_percentuale": numero,
        "grassi_g": numero,
        "grassi_kcal": numero, 
        "grassi_percentuale": numero,
        "carboidrati_g": numero,
        "carboidrati_kcal": numero,
        "carboidrati_percentuale": numero,
        "fibre_g": numero
    }},
    "daily_macros": {{
        "numero_pasti": numero,
        "distribuzione_pasti": {{
            "nome_pasto": {{
                "orario": "HH:MM",
                "kcal": numero,
                "percentuale_kcal": numero,
                "proteine_g": numero,
                "carboidrati_g": numero,
                "grassi_g": numero
            }}
        }}
    }},
    "registered_meals": [
        {{
            "nome_pasto": "colazione/pranzo/cena/spuntino",
            "orario": "HH:MM",
            "alimenti": [
                {{
                    "nome_alimento": "nome",
                    "quantita_g": numero,
                    "stato": "crudo/cotto",
                    "metodo_cottura": "se_applicabile",
                    "misura_casalinga": "equivalenza",
                    "macronutrienti": {{
                        "proteine": numero,
                        "carboidrati": numero, 
                        "grassi": numero,
                        "kcal": numero
                    }}
                }}
            ],
            "totali_pasto": {{
                "kcal_totali": numero,
                "proteine_totali": numero,
                "carboidrati_totali": numero,
                "grassi_totali": numero
            }}
        }}
    ]
}}

IMPORTANTE:
- Restituisci SOLO il JSON, nessun altro testo
- Se un dato non è presente, ometti quella sezione
- I numeri devono essere numerici, non stringhe
- Cerca con attenzione i calcoli numerici nella conversazione
"""

            print(f"[DEEPSEEK] Tentativo {retry_count + 1}/{max_retries}")
            
            # Chiamata a DeepSeek
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Sei un esperto estrattore di dati nutrizionali. Estrai accuratamente i dati dalle conversazioni nutrizionali e restituisci solo JSON valido."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=8192,  # Massimo supportato da DeepSeek
                timeout=120  # Timeout aumentato a 2 minuti
            )
            
            # Estrai il JSON dalla risposta
            response_text = response.choices[0].message.content.strip()
            
            # Pulisci la risposta per estrarre solo il JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
                
            # Parse del JSON
            extracted_data = json.loads(response_text)
            
            print(f"[DEEPSEEK] Dati estratti con successo: {list(extracted_data.keys())}")
            return extracted_data
            
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            print(f"[DEEPSEEK] Errore nel tentativo {retry_count}/{max_retries}: {error_msg}")
            
            if retry_count < max_retries:
                import time
                wait_time = 5 * retry_count  # Attesa progressiva: 5s, 10s, 15s
                print(f"[DEEPSEEK] Attendo {wait_time} secondi prima del prossimo tentativo...")
                time.sleep(wait_time)
            else:
                print(f"[DEEPSEEK] Tutti i tentativi falliti. Ultimo errore: {error_msg}")
                return {}

def check_deepseek_results():
    """
    Controlla se ci sono risultati pronti dall'estrazione DeepSeek in background.
    """
    try:
        # Controlla se ci sono risultati nella coda globale
        with deepseek_lock:
            while not deepseek_results_queue.empty():
                result = deepseek_results_queue.get_nowait()
                
                if result.get("success"):
                    # Aggiorna il contatore dell'ultima estrazione
                    st.session_state.last_extraction_count = result.get("interaction_count", st.session_state.interaction_count)
                    
                    # Salva flag per mostrare notifica senza forzare rerun
                    st.session_state.deepseek_notification = {
                        "type": "success",
                        "message": "✅ Dati nutrizionali aggiornati automaticamente!",
                        "show": True
                    }
                    
                    print("[DEEPSEEK] Risultati salvati, notifica pronta")
                    
                elif "error" in result:
                    # Salva notifica di errore
                    st.session_state.deepseek_notification = {
                        "type": "warning", 
                        "message": f"⚠️ Errore nell'estrazione automatica: {result['error']}",
                        "show": True
                    }
                    
    except queue.Empty:
        pass
    except Exception as e:
        print(f"[RESULTS] Errore nel controllo risultati: {str(e)}")

def show_deepseek_notification():
    """
    Mostra notifiche DeepSeek se presenti, senza bloccare l'interfaccia.
    """
    if hasattr(st.session_state, 'deepseek_notification') and st.session_state.deepseek_notification.get("show"):
        notification = st.session_state.deepseek_notification
        
        if notification["type"] == "success":
            st.success(notification["message"])
        elif notification["type"] == "warning":
            st.warning(notification["message"])
        elif notification["type"] == "info":
            st.info(notification["message"])
            
        # Marca come mostrata
        st.session_state.deepseek_notification["show"] = False

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
                    "calculate_weight_goal_calories": calculate_weight_goal_calories,
                    "analyze_bmi_and_goals": analyze_bmi_and_goals,
                    "check_vitamins": check_vitamins,
                    "get_food_substitutes": get_food_substitutes,
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

def handle_user_data():
    """Gestisce la visualizzazione dei dati utente estratti da DeepSeek"""
    
    # CSS personalizzato per font più piccoli e più colori
    st.markdown("""
    <style>
    .main-title {
        font-size: 28px;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 10px;
    }
    .section-content {
        font-size: 14px;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 10px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 5px 0;
    }
    .macro-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .meal-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .ingredient-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 8px;
        border-radius: 8px;
        margin: 5px 0;
        color: #333;
        font-size: 13px;
    }
    .info-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        color: #333;
        font-size: 13px;
    }
    .stExpander > div > div > div > div {
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">📊 Dati Nutrizionali Estratti</h1>', unsafe_allow_html=True)
    st.markdown('<div class="section-content">Questi dati vengono estratti automaticamente dalla conversazione ogni 2 interazioni usando DeepSeek.</div>', unsafe_allow_html=True)
    
    try:
        # Carica il file utente per leggere i dati estratti
        user_file_path = f"user_data/{st.session_state.user_info['id']}.json"
        
        if not os.path.exists(user_file_path):
            st.warning("📝 File utente non trovato.")
            return
            
        with open(user_file_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        extracted_data = user_data.get("nutritional_info_extracted", {})
        
        if not extracted_data:
            st.info("🤖 Nessun dato nutrizionale estratto ancora. Continua la conversazione con l'agente per raccogliere dati.")
            return
            
        # Header con info ultimo aggiornamento
        last_updated = extracted_data.get("last_updated", "Sconosciuto")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Dati aggiornati automaticamente")
        with col2:
            if last_updated != "Sconosciuto":
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                    st.caption(f"🕒 {formatted_date}")
                except:
                    st.caption(f"🕒 {last_updated}")
        
        st.divider()
        
        # Sezione Fabbisogno Calorico in expander
        if "caloric_needs" in extracted_data:
            with st.expander("🔥 Fabbisogno Energetico Giornaliero", expanded=False):
                caloric_data = extracted_data["caloric_needs"]
                
                # Metrics principali con stile colorato
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    bmr = caloric_data.get('bmr', 0)
                    st.markdown(f'''
                    <div class="metric-container">
                        <h4>⚡ Metabolismo Basale</h4>
                        <h2>{bmr} kcal</h2>
                        <small>Energia per le funzioni vitali</small>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                with col2:
                    fabbisogno_base = caloric_data.get('fabbisogno_base', 0)
                    st.markdown(f'''
                    <div class="metric-container">
                        <h4>🏃 Fabbisogno Base</h4>
                        <h2>{fabbisogno_base} kcal</h2>
                        <small>Con attività quotidiana</small>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                with col3:
                    dispendio_sport = caloric_data.get('dispendio_sportivo', 0)
                    st.markdown(f'''
                    <div class="metric-container">
                        <h4>💪 Dispendio Sportivo</h4>
                        <h2>{dispendio_sport} kcal</h2>
                        <small>Calorie dall'attività sportiva</small>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                with col4:
                    fabbisogno_totale = caloric_data.get('fabbisogno_totale', 0)
                    st.markdown(f'''
                    <div class="metric-container">
                        <h4>🎯 Fabbisogno Totale</h4>
                        <h2>{fabbisogno_totale} kcal</h2>
                        <small>Calorie totali giornaliere</small>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Info aggiuntive
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    laf = caloric_data.get('laf_utilizzato', 'N/A')
                    st.write(f"**📈 Fattore Attività (LAF):** {laf}")
                with col2:
                    aggiustamento = caloric_data.get('aggiustamento_obiettivo', 0)
                    if aggiustamento != 0:
                        simbolo = "+" if aggiustamento > 0 else ""
                        st.write(f"**🎯 Aggiustamento Obiettivo:** {simbolo}{aggiustamento} kcal")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Sezione Macronutrienti in expander
        if "macros_total" in extracted_data:
            with st.expander("🥗 Distribuzione Calorica Giornaliera", expanded=False):
                macros_data = extracted_data["macros_total"]
                
                # Creo dati per grafico
                import pandas as pd
                
                macro_df = pd.DataFrame({
                    'Macronutriente': ['Proteine', 'Carboidrati', 'Grassi'],
                    'Grammi': [
                        macros_data.get('proteine_g', 0),
                        macros_data.get('carboidrati_g', 0),
                        macros_data.get('grassi_g', 0)
                    ],
                    'Kcal': [
                        macros_data.get('proteine_kcal', 0),
                        macros_data.get('carboidrati_kcal', 0),
                        macros_data.get('grassi_kcal', 0)
                    ],
                    'Percentuale': [
                        macros_data.get('proteine_percentuale', 0),
                        macros_data.get('carboidrati_percentuale', 0),
                        macros_data.get('grassi_percentuale', 0)
                    ]
                })
                
                # Layout a 2 colonne
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Grafico a barre colorato
                    st.bar_chart(macro_df.set_index('Macronutriente')['Kcal'])
                    
                with col2:
                    # Cards dei macronutrienti colorate
                    macros_info = [
                        ('Proteine', '🥩', '#FF6B6B'),
                        ('Carboidrati', '🍞', '#4ECDC4'), 
                        ('Grassi', '🥑', '#45B7D1')
                    ]
                    
                    for i, (macro, emoji, color) in enumerate(macros_info):
                        row = macro_df.iloc[i]
                        st.markdown(f'''
                        <div style="background: linear-gradient(135deg, {color} 0%, {color}88 100%); 
                                    padding: 12px; border-radius: 10px; margin: 8px 0; color: white;">
                            <h4>{emoji} {macro}</h4>
                            <p><strong>{row['Grammi']}g</strong> ({row['Kcal']} kcal)</p>
                            <p style="font-size: 12px; opacity: 0.9;">{row['Percentuale']}% del totale</p>
                        </div>
                        ''', unsafe_allow_html=True)
                
                # Fibre e calorie totali
                col1, col2 = st.columns(2)
                with col1:
                    fibre = macros_data.get('fibre_g', 0)
                    if fibre > 0:
                        st.markdown(f'''
                        <div class="info-card">
                            <strong>🌾 Fibre giornaliere:</strong> {fibre}g
                        </div>
                        ''', unsafe_allow_html=True)
                with col2:
                    kcal_totali = macros_data.get('kcal_totali', 0)
                    st.markdown(f'''
                    <div class="info-card">
                        <strong>🔥 Calorie Totali:</strong> {kcal_totali} kcal
                    </div>
                    ''', unsafe_allow_html=True)
        
        # Piano pasti in expander
        if "daily_macros" in extracted_data:
            with st.expander("🍽️ Piano Pasti Giornaliero", expanded=False):
                daily_data = extracted_data["daily_macros"]
                
                num_pasti = daily_data.get('numero_pasti', 0)
                st.markdown(f'<div class="info-card"><strong>📅 Piano giornaliero:</strong> {num_pasti} pasti</div>', 
                           unsafe_allow_html=True)
                
                if "distribuzione_pasti" in daily_data:
                    # Timeline dei pasti colorata
                    meal_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
                    
                    for i, (pasto_nome, pasto_data) in enumerate(daily_data["distribuzione_pasti"].items()):
                        color = meal_colors[i % len(meal_colors)]
                        orario = pasto_data.get('orario', 'N/A')
                        kcal = pasto_data.get('kcal', 0)
                        percentuale = pasto_data.get('percentuale_kcal', 0)
                        
                        st.markdown(f'''
                        <div style="background: linear-gradient(135deg, {color} 0%, {color}88 100%); 
                                    padding: 15px; border-radius: 12px; margin: 10px 0; color: white;">
                            <h3>🕐 {pasto_nome.title()} - {orario}</h3>
                            <p style="font-size: 16px;"><strong>{kcal} kcal</strong> ({percentuale}% del totale)</p>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        # Macros del pasto in cards piccole
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            proteine = pasto_data.get('proteine_g', 0)
                            st.markdown(f'<div class="ingredient-card">🥩 <strong>Proteine:</strong> {proteine}g</div>', 
                                       unsafe_allow_html=True)
                        with col2:
                            carbs = pasto_data.get('carboidrati_g', 0)
                            st.markdown(f'<div class="ingredient-card">🍞 <strong>Carboidrati:</strong> {carbs}g</div>', 
                                       unsafe_allow_html=True)
                        with col3:
                            grassi = pasto_data.get('grassi_g', 0)
                            st.markdown(f'<div class="ingredient-card">🥑 <strong>Grassi:</strong> {grassi}g</div>', 
                                       unsafe_allow_html=True)
        
        # Pasti creati in expander
        if "registered_meals" in extracted_data:
            with st.expander("👨‍🍳 Ricette e Pasti Creati", expanded=False):
                meals_data = extracted_data["registered_meals"]
                
                for i, meal in enumerate(meals_data):
                    nome_pasto = meal.get('nome_pasto', 'Pasto').title()
                    orario = meal.get('orario', 'N/A')
                    
                    # Container per ogni pasto invece di sub-expander
                    st.markdown(f'''
                    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
                                padding: 15px; border-radius: 12px; margin: 15px 0; color: white;">
                        <h3>🍽️ {nome_pasto} - {orario}</h3>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # Lista alimenti
                    if "alimenti" in meal and meal["alimenti"]:
                        st.markdown("**🛒 Ingredienti:**")
                        
                        for j, alimento in enumerate(meal["alimenti"]):
                            nome = alimento.get('nome_alimento', 'N/A')
                            quantita = alimento.get('quantita_g', 'N/A')
                            stato = alimento.get('stato', 'N/A')
                            misura = alimento.get('misura_casalinga', 'N/A')
                            metodo = alimento.get('metodo_cottura', '')
                            
                            st.markdown(f'''
                            <div class="ingredient-card">
                                <strong>{nome}</strong><br>
                                📏 {quantita}g ({stato})<br>
                                🥄 {misura}
                                {f'<br>🔥 {metodo}' if metodo else ''}
                            </div>
                            ''', unsafe_allow_html=True)
                    
                    # Totali nutrizionali con colori
                    if "totali_pasto" in meal:
                        totali = meal["totali_pasto"]
                        st.markdown("**📊 Valori Nutrizionali Totali:**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        nutrition_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                        nutrition_data = [
                            ('🔥 Calorie', f"{totali.get('kcal_totali', 0)} kcal"),
                            ('🥩 Proteine', f"{totali.get('proteine_totali', 0)}g"),
                            ('🍞 Carboidrati', f"{totali.get('carboidrati_totali', 0)}g"),
                            ('🥑 Grassi', f"{totali.get('grassi_totali', 0)}g")
                        ]
                        
                        for k, (col, (label, value)) in enumerate(zip([col1, col2, col3, col4], nutrition_data)):
                            with col:
                                color = nutrition_colors[k]
                                st.markdown(f'''
                                <div style="background: {color}; padding: 10px; border-radius: 8px; 
                                            text-align: center; color: white; margin: 2px;">
                                    <div style="font-size: 12px;">{label}</div>
                                    <div style="font-size: 14px; font-weight: bold;">{value}</div>
                                </div>
                                ''', unsafe_allow_html=True)
                    
                    # Separatore tra i pasti
                    if i < len(meals_data) - 1:
                        st.markdown('<hr style="margin: 20px 0; border: 1px solid #ddd;">', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Errore nel caricamento dei dati: {str(e)}")

def chat_interface():
    """Interfaccia principale della chat"""
    # Controlla risultati DeepSeek in background
    check_deepseek_results()
    show_deepseek_notification()
    
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
                                     ["Perdita di peso", "Mantenimento", "Aumento di peso"],
                                     index=["Perdita di peso", "Mantenimento", "Aumento di peso"].index(nutritional_info.obiettivo) if nutritional_info else 0)
                
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
                    
                    # Reset completo DeepSeek
                    st.session_state.interaction_count = 0
                    st.session_state.last_extraction_count = 0
                    if hasattr(st.session_state, 'deepseek_notification'):
                        del st.session_state.deepseek_notification
                    
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
                    
                    # Cancella i dati DeepSeek estratti dal file JSON
                    try:
                        user_file_path = f"user_data/{st.session_state.user_info['id']}.json"
                        if os.path.exists(user_file_path):
                            with open(user_file_path, 'r', encoding='utf-8') as f:
                                user_data = json.load(f)
                            
                            # Rimuovi completamente la sezione nutritional_info_extracted
                            if "nutritional_info_extracted" in user_data:
                                del user_data["nutritional_info_extracted"]
                                
                            with open(user_file_path, 'w', encoding='utf-8') as f:
                                json.dump(user_data, f, indent=2, ensure_ascii=False)
                                
                            print(f"[RESET] Dati DeepSeek cancellati per utente {st.session_state.user_info['id']}")
                    except Exception as e:
                        print(f"[RESET] Errore nella cancellazione dati DeepSeek: {str(e)}")
                    
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

                    COMUNICAZIONE E PROGRESSIONE:
                    1. Segui SEMPRE il processo fase per fase, svolgendo una fase per volta, partendo dalla FASE 0
                    2. Elenca le fonti utilizzate in ciascuna fase
                    3. Chiedi feedback quando necessario
                    4. Concludi sempre con un messaggio di chiusura con:
                        - Un invito a chiedere se ha domande riguardo i calcoli o le scelte fatte
                        - Una domanda per chiedere all'utente se vuole continuare o se ha altre domande

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

                    FASE 0: Analisi BMI e coerenza obiettivi:
                    - Calcola il BMI e la categoria di appartenenza
                    - Valuta la coerenza dell'obiettivo con il BMI
                        - Se l'obiettivo non è coerente, chiedi all'utente se intende modificare l'obiettivo
                        - Se l'obiettivo è coerente, avvisa l'utente e poi procedi con la FASE 1

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

                    FASE 7: Controllo vitaminico e ultraprocessati
                    - Controlla l'apporto vitaminico totale della dieta e lo confronta con i LARN per identificare carenze o eccessi
                    - Verifica che gli alimenti ultraprocessati (NOVA 4) non superino il 10% delle calorie totali, secondo le più recenti evidenze scientifiche
                    - Aggiorna i pasti in base alle carenze o eccessi identificati

                    Puoi procedere con la FASE 0?
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
            
            # Mostra notifiche DeepSeek se presenti
            show_deepseek_notification()
            
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
                    
                    # Controlla se è il momento di estrarre i dati nutrizionali con DeepSeek
                    check_and_extract_nutritional_data_async(st.session_state.user_info["id"])
                    
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
                ["Chat", "Progressi", "Preferenze", "Piano Nutrizionale"]
            )
            
            # Aggiungi pulsante logout
            if st.button("Logout"):
                st.session_state.user_info = None
                st.session_state.messages = []
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
                st.rerun()
        
        if page == "Chat":
            chat_interface()
        elif page == "Progressi":
            track_user_progress()
            show_progress_history()
        elif page == "Preferenze":
            handle_preferences()
        elif page == "Piano Nutrizionale":
            handle_user_data()

if __name__ == "__main__":
    main() 