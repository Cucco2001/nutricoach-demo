"""
Modulo per la gestione delle conversazioni chat.

Gestisce i thread OpenAI, le run dell'assistente e il flusso completo 
delle conversazioni con retry logic e gestione degli errori.
"""

import streamlit as st
import time
import io
from agent.tool_handler import handle_tool_calls
from frontend.nutrition_questions import NUTRITION_QUESTIONS
from agent.prompts import get_initial_prompt, get_initial_prompt_pdf_diet

# Try to import PDF processing libraries
try:
    import PyPDF2
    PDF_EXTRACTION_AVAILABLE = True
except ImportError:
    try:
        import pdfplumber
        PDF_EXTRACTION_AVAILABLE = True
    except ImportError:
        PDF_EXTRACTION_AVAILABLE = False


class ChatManager:
    """Gestisce le conversazioni chat con l'assistente"""
    
    def __init__(self, openai_client, user_data_manager):
        """
        Inizializza il gestore della chat.
        
        Args:
            openai_client: Client OpenAI configurato
            user_data_manager: Gestore dei dati utente
        """
        self.openai_client = openai_client
        self.user_data_manager = user_data_manager
    
    def _extract_pdf_content(self) -> str:
        """
        Estrae il contenuto testuale del PDF caricato dall'utente.
        
        Returns:
            str: Contenuto del PDF estratto o messaggio di errore
        """
        try:
            if "uploaded_diet_pdf" not in st.session_state or not st.session_state.uploaded_diet_pdf:
                return "[PDF non disponibile nel session state]"
            
            pdf_data = st.session_state.uploaded_diet_pdf
            file_content = pdf_data.get('content')
            
            if not file_content:
                return "[Contenuto PDF non disponibile]"
            
            # Prova ad estrarre il testo dal PDF
            if not PDF_EXTRACTION_AVAILABLE:
                return f"""
PDF CARICATO: {pdf_data['name']}
DIMENSIONE: {pdf_data['size']} bytes

[ERRORE: Librerie per estrazione PDF non disponibili. 
Installare PyPDF2 o pdfplumber: pip install PyPDF2 pdfplumber]

ISTRUZIONI PER L'AGENTE:
- Il PDF non può essere letto automaticamente
- Procedi come se il PDF contenesse una dieta settimanale completa
- Simula l'estrazione di alimenti tipici di una dieta mediterranea
- Organizza i 7 giorni con pasti bilanciati
- Usa il tool calculate_kcal_from_foods per tutti i calcoli
"""
            
            try:
                # Prova con PyPDF2
                if 'PyPDF2' in globals():
                    extracted_text = self._extract_with_pypdf2(file_content)
                else:
                    # Fallback a pdfplumber se disponibile
                    extracted_text = self._extract_with_pdfplumber(file_content)
                
                if extracted_text.strip():
                    return f"""
PDF CARICATO: {pdf_data['name']}
DIMENSIONE: {pdf_data['size']} bytes

CONTENUTO ESTRATTO DAL PDF:
{extracted_text}

ISTRUZIONI PER L'AGENTE:
- Analizza attentamente il contenuto sopra estratto dal PDF
- Estrai TUTTI gli alimenti menzionati nel testo
- Organizza una settimana completa di 7 giorni
- Se il PDF contiene meno di 7 giorni, espandi tu la settimana usando gli alimenti presenti
- Usa il tool calculate_kcal_from_foods per tutti i calcoli
"""
                else:
                    return f"""
PDF CARICATO: {pdf_data['name']}
DIMENSIONE: {pdf_data['size']} bytes

[AVVISO: Non è stato possibile estrarre testo leggibile dal PDF]

ISTRUZIONI PER L'AGENTE:
- Il PDF potrebbe essere un'immagine scansionata o protetto
- Procedi come se il PDF contenesse una dieta settimanale completa
- Simula l'estrazione di alimenti tipici di una dieta mediterranea
- Organizza i 7 giorni con pasti bilanciati
- Usa il tool calculate_kcal_from_foods per tutti i calcoli
"""
                
            except Exception as e:
                return f"""
PDF CARICATO: {pdf_data['name']}
DIMENSIONE: {pdf_data['size']} bytes

[ERRORE NELL'ESTRAZIONE: {str(e)}]

ISTRUZIONI PER L'AGENTE:
- Si è verificato un errore nell'estrazione del testo dal PDF
- Procedi come se il PDF contenesse una dieta settimanale completa
- Simula l'estrazione di alimenti tipici di una dieta mediterranea
- Organizza i 7 giorni con pasti bilanciati
- Usa il tool calculate_kcal_from_foods per tutti i calcoli
"""
                
        except Exception as e:
            return f"[Errore generale nell'elaborazione del PDF: {str(e)}]"
    
    def _extract_with_pypdf2(self, file_content: bytes) -> str:
        """
        Estrae il testo usando PyPDF2.
        
        Args:
            file_content: Contenuto binario del PDF
            
        Returns:
            str: Testo estratto
        """
        text_content = ""
        
        # Crea un file-like object dai bytes
        pdf_file = io.BytesIO(file_content)
        
        # Leggi il PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Estrai il testo da tutte le pagine
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            text_content += f"\n--- PAGINA {page_num + 1} ---\n"
            text_content += page_text
        
        return text_content.strip()
    
    def _extract_with_pdfplumber(self, file_content: bytes) -> str:
        """
        Estrae il testo usando pdfplumber (alternativa più robusta).
        
        Args:
            file_content: Contenuto binario del PDF
            
        Returns:
            str: Testo estratto
        """
        import pdfplumber
        
        text_content = ""
        
        # Crea un file-like object dai bytes
        pdf_file = io.BytesIO(file_content)
        
        # Leggi il PDF con pdfplumber
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content += f"\n--- PAGINA {page_num + 1} ---\n"
                    text_content += page_text
        
        return text_content.strip()
    
    def _is_pdf_diet_mode(self) -> bool:
        """
        Verifica se siamo in modalità analisi PDF.
        
        Returns:
            bool: True se l'utente ha caricato un PDF
        """
        if not hasattr(st.session_state, 'nutrition_answers'):
            return False
        
        upload_answer = st.session_state.nutrition_answers.get('existing_diet_upload', {})
        return (upload_answer.get('answer') == 'Sì' and 
                upload_answer.get('follow_up', {}).get('diet_pdf', {}).get('uploaded'))
    
    def create_new_thread(self):
        """
        Crea un nuovo thread per la conversazione, mantenendo la chat history e le risposte nutrizionali dell'utente.
        
        Carica dal file utente:
        - Chat history (messaggi precedenti)
        - Nutritional info (età, sesso, peso, altezza, attività, obiettivo, nutrition_answers, agent_qa)
        
        Returns:
            str: ID del thread creato o None in caso di errore
        """
        try:
            thread = self.openai_client.beta.threads.create()
            st.session_state.thread_id = thread.id
            st.session_state.current_run_id = None
            
            # Mantieni la chat history e le risposte nutrizionali presenti nel file utente
            if hasattr(st.session_state, 'user_info') and st.session_state.user_info and "id" in st.session_state.user_info:
                user_id = st.session_state.user_info["id"]
                
                # Recupera le informazioni nutrizionali salvate dall'utente
                # Include: età, sesso, peso, altezza, attività, obiettivo, nutrition_answers, agent_qa
                nutritional_info = self.user_data_manager.get_nutritional_info(user_id)
                if nutritional_info and nutritional_info.nutrition_answers:
                    # Carica le risposte nutrizionali esistenti
                    st.session_state.nutrition_answers = nutritional_info.nutrition_answers
                    st.session_state.current_question = len(NUTRITION_QUESTIONS)
                else:
                    # Se non ci sono risposte salvate, inizializza valori di default
                    st.session_state.current_question = st.session_state.get('current_question', 0)
                    st.session_state.nutrition_answers = st.session_state.get('nutrition_answers', {})
                
                # Recupera la chat history dell'utente
                chat_history = self.user_data_manager.get_chat_history(user_id)
                if chat_history:
                    # Se c'è una chat history e l'utente ha completato le domande nutrizionali,
                    # aggiungi l'initial prompt come primo messaggio
                    if nutritional_info and nutritional_info.nutrition_answers:
                        # Genera l'initial prompt appropriato (PDF o standard)
                        if self._is_pdf_diet_mode():
                            # Modalità PDF: usa prompt per analisi PDF
                            pdf_content = self._extract_pdf_content()
                            initial_prompt = get_initial_prompt_pdf_diet(
                                user_info=st.session_state.user_info,
                                nutrition_answers=st.session_state.nutrition_answers,
                                pdf_content=pdf_content
                            )
                        else:
                            # Modalità standard: usa prompt normale
                            initial_prompt = get_initial_prompt(
                                user_info=st.session_state.user_info,
                                nutrition_answers=st.session_state.nutrition_answers,
                                user_preferences=st.session_state.user_info.get('preferences', {})
                            )
                        
                        # Aggiungi l'initial prompt come primo messaggio
                        try:
                            self.openai_client.beta.threads.messages.create(
                                thread_id=st.session_state.thread_id,
                                role="user",
                                content=initial_prompt
                            )
                        except Exception as e:
                            st.warning(f"Impossibile aggiungere initial prompt al thread: {str(e)}")
                    
                    # Carica i messaggi esistenti nella session state
                    st.session_state.messages = [
                        {"role": msg.role, "content": msg.content}
                        for msg in chat_history
                    ]
                    
                    # Inserisci i messaggi esistenti nel nuovo thread OpenAI
                    for msg in chat_history:
                        try:
                            self.openai_client.beta.threads.messages.create(
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
                st.session_state.current_question = 0
                st.session_state.nutrition_answers = {}
            
            return thread.id
        except Exception as e:
            st.error(f"Errore nella creazione del thread: {str(e)}")
            return None
    
    def check_and_cancel_run(self):
        """Verifica se c'è una run attiva e la cancella se necessario."""
        if hasattr(st.session_state, 'current_run_id') and st.session_state.current_run_id:
            try:
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=st.session_state.current_run_id
                )
                if run.status in ['active', 'requires_action', 'failed', 'expired']:
                    self.openai_client.beta.threads.runs.cancel(
                        thread_id=st.session_state.thread_id,
                        run_id=st.session_state.current_run_id
                    )
            except Exception:
                pass
            finally:
                st.session_state.current_run_id = None
    
    def chat_with_assistant(self, user_input):
        """
        Gestisce la conversazione con l'assistente.
        
        Args:
            user_input: Messaggio dell'utente
            
        Returns:
            str: Risposta dell'assistente
        """
        try:
            # Se non esiste un thread, creane uno nuovo
            if not hasattr(st.session_state, 'thread_id'):
                self.create_new_thread()
            
            # Verifica e cancella eventuali run bloccate
            self.check_and_cancel_run()
            
            # Controlla se è necessario aggiungere il prompt delle preferenze
            if st.session_state.get('prompt_to_add_at_next_message', False):
                preferences_prompt = st.session_state.get('preferences_prompt', '')
                if preferences_prompt:
                    user_input = f"{preferences_prompt}. {user_input}"
                
                # Resetta il flag
                st.session_state.prompt_to_add_at_next_message = False
                st.session_state.preferences_prompt = ''

            # Aggiungi il messaggio dell'utente al thread
            try:
                self.openai_client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_input
                )
            except Exception as e:
                # Se c'è un errore nel thread, creane uno nuovo e riprova
                self.create_new_thread()
                self.openai_client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=user_input
                )
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Crea una run
                    run = self.openai_client.beta.threads.runs.create(
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
                                self.check_and_cancel_run()
                                self.create_new_thread()  # Crea un nuovo thread dopo il timeout
                                return "Mi dispiace, l'operazione è durata troppo a lungo. Per favore, riprova."
                            
                            try:
                                run_status = self.openai_client.beta.threads.runs.retrieve(
                                    thread_id=st.session_state.thread_id,
                                    run_id=run.id
                                )
                            except Exception:
                                self.check_and_cancel_run()
                                self.create_new_thread()
                                raise Exception("Errore nel recupero dello stato della run")
                            
                            if run_status.status == 'completed':
                                st.session_state.current_run_id = None
                                break
                            elif run_status.status in ['failed', 'expired', 'cancelled']:
                                self.check_and_cancel_run()
                                self.create_new_thread()
                                raise Exception(f"Run {run_status.status}")
                            elif run_status.status == 'requires_action':
                                # Gestisci le chiamate ai tool
                                tool_outputs = handle_tool_calls(run_status)
                                if tool_outputs:
                                    try:
                                        # Invia i risultati e continua
                                        self.openai_client.beta.threads.runs.submit_tool_outputs(
                                            thread_id=st.session_state.thread_id,
                                            run_id=run.id,
                                            tool_outputs=tool_outputs
                                        )
                                    except Exception:
                                        self.check_and_cancel_run()
                                        self.create_new_thread()
                                        raise Exception("Errore nell'invio dei risultati dei tool")
                                else:
                                    self.check_and_cancel_run()
                                    self.create_new_thread()
                                    raise Exception("Errore nella gestione dei tool")
                            
                            # Breve pausa prima del prossimo controllo
                            time.sleep(1)
                    
                    # Ottieni la risposta
                    try:
                        messages = self.openai_client.beta.threads.messages.list(
                            thread_id=st.session_state.thread_id
                        )
                        return messages.data[0].content[0].text.value
                    except Exception:
                        self.check_and_cancel_run()
                        self.create_new_thread()
                        raise Exception("Errore nel recupero dei messaggi")
                    
                except Exception as e:
                    retry_count += 1
                    self.check_and_cancel_run()
                    if retry_count >= max_retries:
                        self.create_new_thread()  # Crea un nuovo thread dopo troppi tentativi falliti
                        st.error(f"Errore dopo {max_retries} tentativi: {str(e)}")
                        return "Mi dispiace, si è verificato un errore. Riprova."
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
        except Exception as e:
            self.check_and_cancel_run()
            self.create_new_thread()  # Crea un nuovo thread dopo un errore generale
            st.error(f"Errore nella conversazione: {str(e)}")
            return "Mi dispiace, si è verificato un errore inaspettato. Riprova."


def create_new_thread(openai_client, user_data_manager):
    """
    Funzione di convenienza per creare un nuovo thread.
    
    Args:
        openai_client: Client OpenAI configurato
        user_data_manager: Gestore dei dati utente
        
    Returns:
        str: ID del thread creato
    """
    manager = ChatManager(openai_client, user_data_manager)
    return manager.create_new_thread()


def check_and_cancel_run(openai_client):
    """
    Funzione di convenienza per verificare e cancellare run attive.
    
    Args:
        openai_client: Client OpenAI configurato
    """
    manager = ChatManager(openai_client, None)
    manager.check_and_cancel_run()


def chat_with_assistant(user_input, openai_client, user_data_manager):
    """
    Funzione di convenienza per gestire la chat con l'assistente.
    
    Args:
        user_input: Messaggio dell'utente
        openai_client: Client OpenAI configurato
        user_data_manager: Gestore dei dati utente
        
    Returns:
        str: Risposta dell'assistente
    """
    manager = ChatManager(openai_client, user_data_manager)
    return manager.chat_with_assistant(user_input) 