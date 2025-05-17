from openai import OpenAI
import time
from nutridb_tool import nutridb_tool
import json
import logging
from typing import Dict, Any

# Specifica API: Assistants v2 (OpenAI)
# Assicurati di avere OPENAI_API_KEY nell'ambiente o setta client = OpenAI(api_key="...")
client = OpenAI()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_tool_result(fn_name: str, result: Dict[str, Any]) -> bool:
    """Valida il risultato di una chiamata al tool."""
    if "error" in result:
        logger.error(f"Errore nel tool {fn_name}: {result['error']}")
        return False
        
    # Validazione specifica per ogni tipo di funzione
    if fn_name == "get_LARN_energy":
        if "kcal" not in result:
            logger.error(f"Risultato mancante per {fn_name}: kcal non presente")
            return False
        kcal = result["kcal"]
        if not isinstance(kcal, (int, float)) or kcal <= 0 or kcal > 5000:
            logger.error(f"Valore kcal non valido in {fn_name}: {kcal}")
            return False
            
    elif fn_name == "get_LARN_fibre":
        if "fibra_min" not in result or "fibra_max" not in result:
            logger.error(f"Risultati mancanti per {fn_name}")
            return False
        if not all(isinstance(v, (int, float)) for v in [result["fibra_min"], result["fibra_max"]]):
            logger.error(f"Valori non numerici in {fn_name}")
            return False
            
    return True

# Funzione per lanciare una conversazione Nutricoach a partire da un messaggio utente
def run_nutricoach_conversation(user_message: str, assistant_id: str) -> str:
    """Avvia una conversazione con l'agente Nutricoach e restituisce la risposta."""
    try:
        # 1. Crea un nuovo thread
        thread = client.beta.threads.create()
        logger.info("Nuovo thread creato")

        # 2. Inserisci il messaggio dell'utente
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        logger.info("Messaggio utente inserito")

        # 3. Avvia la run dell'agente
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        logger.info("Run avviata")

        # 4. Polling fino a completamento
        start_time = time.time()
        max_duration = 180  # 3 minuti
        while True:
            if time.time() - start_time > max_duration:
                logger.error("Timeout nella run")
                return "Mi dispiace, l'operazione sta richiedendo troppo tempo. Per favore, prova a semplificare la richiesta."
            
            status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status
            if status in ["completed", "requires_action", "failed"]:
                break
            time.sleep(1)

        # 5. Gestione chiamata ai tool, se richiesta
        if status == "requires_action":
            tool_calls = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            ).required_action.submit_tool_outputs.tool_calls
            
            outputs = []
            all_valid = True
            
            for call in tool_calls:
                try:
                    fn_name = call.function.name
                    args = json.loads(call.function.arguments)
                    logger.info(f"Esecuzione {fn_name} con args: {args}")
                    
                    result = nutridb_tool(**args)
                    
                    # Valida il risultato
                    if not validate_tool_result(fn_name, result):
                        all_valid = False
                        outputs.append({
                            "tool_call_id": call.id,
                            "output": json.dumps({
                                "error": "Risultato non valido",
                                "details": result.get("error", "Errore sconosciuto")
                            })
                        })
                    else:
                        outputs.append({
                            "tool_call_id": call.id,
                            "output": json.dumps(result)
                        })
                        
                except Exception as e:
                    logger.error(f"Errore nell'esecuzione del tool {fn_name}: {str(e)}")
                    all_valid = False
                    outputs.append({
                        "tool_call_id": call.id,
                        "output": json.dumps({"error": str(e)})
                    })

            # Invia i risultati al modello
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=outputs
            )
            
            if not all_valid:
                logger.warning("Alcuni tool hanno restituito risultati non validi")
            
            # Attendi completamento finale
            while True:
                status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status
                if status == "completed":
                    break
                elif status == "failed":
                    logger.error("Run fallita dopo l'esecuzione dei tool")
                    return "Mi dispiace, si è verificato un errore durante l'elaborazione. Per favore, riprova."
                time.sleep(1)

        # 6. Estrai e ritorna risposta dell'assistente
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value

        return "Errore: nessuna risposta trovata."
        
    except Exception as e:
        logger.error(f"Errore nella conversazione: {str(e)}")
        return f"Mi dispiace, si è verificato un errore inaspettato: {str(e)}"
