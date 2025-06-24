"""
Client per l'integrazione con DeepSeek AI.

Questo modulo gestisce la connessione, l'autenticazione e le chiamate API
verso il servizio DeepSeek per l'estrazione di dati nutrizionali.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env
load_dotenv()


class DeepSeekClient:
    """Client per le chiamate API a DeepSeek."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inizializza il client DeepSeek.
        
        Args:
            api_key: Chiave API DeepSeek. Se None, verrà caricata da variabile d'ambiente.
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com"
                )
            except Exception as e:
                print(f"[DEEPSEEK_CLIENT] Errore nell'inizializzazione: {str(e)}")
                
    def is_available(self) -> bool:
        """Verifica se il client DeepSeek è disponibile."""
        return self.client is not None and self.api_key is not None
    
    def extract_nutritional_data(
        self, 
        conversation_history: List[Any], 
        user_info: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Estrae dati nutrizionali dalla conversazione usando DeepSeek.
        
        Args:
            conversation_history: Lista delle conversazioni dell'agente
            user_info: Informazioni dell'utente
            max_retries: Numero massimo di tentativi
            
        Returns:
            Dict con i dati nutrizionali estratti
        """
        if not self.is_available():
            return {}
            
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Prepara il contesto della conversazione
                # NOTA: La cronologia passata qui contiene GIA' solo le nuove interazioni
                # grazie alla logica nel DeepSeekManager.
                conversation_text = "\n\n".join([
                    f"UTENTE: {qa['question'] if isinstance(qa, dict) else qa.question}\nAGENTE: {qa['answer'] if isinstance(qa, dict) else qa.answer}" 
                    for qa in conversation_history
                ])
                
                # Costruisci il prompt
                extraction_prompt = self._build_extraction_prompt(conversation_text, user_info)
                
                
                # Chiamata a DeepSeek
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Sei un esperto estrattore di dati nutrizionali. Estrai accuratamente i dati dalle conversazioni nutrizionali e restituisci solo JSON valido."
                        },
                        {"role": "user", "content": extraction_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=8192,  # Massimo supportato da DeepSeek
                    timeout=120  # Timeout di 2 minuti
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
                
                # Restituisce sia i dati estratti che la raw response per il debug
                return {
                    "extracted_data": extracted_data,
                    "raw_response": response_text,
                    "conversation_history": conversation_history,
                    "extraction_keys": list(extracted_data.keys()) if extracted_data else []
                }
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                print(f"[DEEPSEEK_CLIENT] Errore nel tentativo {retry_count}/{max_retries}: {error_msg}")
                
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # Attesa progressiva: 5s, 10s, 15s
                    time.sleep(wait_time)
                else:
                    print(f"[DEEPSEEK_CLIENT] Tutti i tentativi falliti. Ultimo errore: {error_msg}")
                    return {}
    
    def _build_extraction_prompt(self, conversation_text: str, user_info: Dict[str, Any]) -> str:
        """
        Costruisce il prompt per l'estrazione dei dati nutrizionali.
        
        Args:
            conversation_text: Testo della conversazione
            user_info: Informazioni dell'utente
            
        Returns:
            Prompt formattato per DeepSeek
        """
        # Costruiamo il prompt manualmente per evitare problemi con f-string e parentesi graffe
        eta = user_info.get('età', 'N/A')
        sesso = user_info.get('sesso', 'N/A')
        peso = user_info.get('peso', 'N/A')
        altezza = user_info.get('altezza', 'N/A')
        obiettivo = user_info.get('obiettivo', 'N/A')
        
        prompt = """
Stai per analizzare una singola o più interazioni, parte di una conversazione più ampia tra un nutrizionista AI e un utente.
Il tuo compito è quello di estrarre solamente i dati nutrizionali calcolati o forniti in questa specifica interazione, senza cercare di completare o immaginare dati mancanti e senza restituire l'intero schema JSON completo.

Se nell'interazione sono presenti uno o più dei seguenti campi, restituiscili nel formato JSON riportato sotto, includendo solo i campi effettivamente rilevati.
CONVERSAZIONE:
""" + conversation_text + """

ESTRAI E RESTITUISCI UN JSON NEL SEGUENTE FORMATO OUTPUT CITANDO SOLO I CAMPI PRESENTI NELL'INTERAZIONE ED ESCLUDENDO GLI ALTRI:

"caloric_needs": {
    "bmr": numero_metabolismo_basale,
    "fabbisogno_base": numero_fabbisogno_senza_sport,
    "dispendio_sportivo": numero_calorie_da_sport,
    "fabbisogno_totale": numero_fabbisogno_totale,
    "aggiustamento_obiettivo": numero_deficit_o_surplus,
    "fabbisogno_finale": numero_calorie_finali,
    "laf_utilizzato": numero_fattore_attivita
}

"macros_total": {
    "kcal_finali": numero, (uguali al fabbisogno_finale)
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
}

"daily_macros": {
    "numero_pasti": numero,
    "distribuzione_pasti": {
        "nome_pasto": {
            "kcal": numero,
            "percentuale_kcal": numero,
            "proteine_g": numero,
            "carboidrati_g": numero,
            "grassi_g": numero
        }
    }
}

"weekly_diet_day_1": [
    {
        "nome_pasto": "colazione/pranzo/cena/spuntino_mattutino/spuntino_pomeridiano o altri se specificati",
        "alimenti": [
            {
                "nome_alimento": "nome",
                "quantita_g": numero_grammi_quando_possibile,
                "stato": "crudo/cotto",
                "metodo_cottura": "se_applicabile",
                "misura_casalinga": "equivalenza_descrittiva_es_2_uova_1_tazza",
                "sostituti": "100g di riso basmati, 90g di pasta integrale",
                "macronutrienti": {
                    "proteine": numero,
                    "carboidrati": numero, 
                    "grassi": numero,
                    "kcal": numero
                }
            }
        ],
        "totali_pasto": {
            "kcal_finali": numero,
            "proteine_totali": numero,
            "carboidrati_totali": numero,
            "grassi_totali": numero
        }
    }
]
"weekly_diet_days_2_7": {
    "giorno_2": {
        "colazione": {
            "alimenti": {"nome_alimento": nome_alimento, "quantita_g": quantita_g, "misura_casalinga": misura_casalinga, "sostituti": "100g di riso basmati, 90g di pasta integrale"}
        },
        "pranzo": {"...simile..."},
        "cena": {"...simile..."},
        "spuntino_mattutino": {"...simile..."},
        "spuntino_pomeridiano": {"...simile..."}
    },
    "giorno_3": {"...struttura identica..."},
    "giorno_4": {"...struttura identica..."},
    "giorno_5": {"...struttura identica..."},
    "giorno_6": {"...struttura identica..."},
    "giorno_7": {"...struttura identica..."}
}

"weekly_diet_partial_days_2_7": {
    "day": "giorno_X",
    "meal": "nome_pasto",
    "data": {
        "alimenti": {"nome_alimento": nome_alimento, "quantita_g": quantita_g, "misura_casalinga": misura_casalinga, "sostituti": "100g di riso basmati, 90g di pasta integrale"}
    }
}

IMPORTANTE PER CALORIC_NEEDS:
- Il "fabbisogno_totale" = "fabbisogno_base"*"laf_utilizzato"+"dispendio_sportivo"
- "aggiustamento_obiettivo" è la quantità di calorie da aggiungere al fabbisogno totale per raggiungere l'obiettivo
- "fabbisogno_finale" = "fabbisogno_totale" + "aggiustamento_obiettivo"
- Cerca di estrarre sempre questi campi nella conversazione

IMPORTANTE PER LE QUANTITÀ:
- "quantita_g": Inserisci il peso in grammi SOLO se menzionato esplicitamente in grammi
- Se sono menzionate unità diverse (es: "2 uova", "1 tazza", "3 fette"), OMETTI il campo "quantita_g" completamente
- "misura_casalinga": Descrivi sempre l'unità originale (es: "2 uova grandi", "1 tazza", "1 fetta di pane")

**FONDAMENTALE - DISTINZIONE TRA GIORNO 1 E GIORNI 2-7**:
- USA "weekly_diet_day_1" SOLO per i pasti del PRIMO GIORNO (GIORNO 1)
- USA "weekly_diet_days_2_7" per i pasti dei GIORNI 2-7
- USA "weekly_diet_partial_days_2_7" per modifiche specifiche di un singolo pasto dei giorni 2-7

**PATTERN DI RICONOSCIMENTO**:
- "🗓️ GIORNO 2", "GIORNO 2", "giorno 2" → weekly_diet_days_2_7.giorno_2  
- "🗓️ GIORNO 3", "GIORNO 3", "giorno 3" → weekly_diet_days_2_7.giorno_3
- "🗓️ GIORNO 4", "GIORNO 4", "giorno 4" → weekly_diet_days_2_7.giorno_4
- "🗓️ GIORNO 5", "GIORNO 5", "giorno 5" → weekly_diet_days_2_7.giorno_5
- "🗓️ GIORNO 6", "GIORNO 6", "giorno 6" → weekly_diet_days_2_7.giorno_6
- "🗓️ GIORNO 7", "GIORNO 7", "giorno 7" → weekly_diet_days_2_7.giorno_7

**MODIFICHE SPECIFICHE**:
- "rifai colazione giorno 3" → weekly_diet_partial_days_2_7 con day="giorno_3", meal="colazione"
- "cambia pranzo giorno 4" → weekly_diet_partial_days_2_7 con day="giorno_4", meal="pranzo"
- "rifai cena giorno 2" → weekly_diet_partial_days_2_7 con day="giorno_2", meal="cena"

**DEFAULT**:
- SE NON C'È INDICAZIONE DI GIORNO → USA "weekly_diet_day_1" (è il giorno 1)
- ESEMPIO: "🌅 COLAZIONE (550 kcal)" senza giorno → weekly_diet_day_1


IMPORTANTE PER I TIPI DI PASTO:
- "nome_pasto" deve essere SPECIFICO:
  * "colazione" per il primo pasto della giornata
  * "spuntino_mattutino" per lo spuntino del mattino (tra colazione e pranzo)
  * "pranzo" per il pasto principale di mezzogiorno
  * "spuntino_pomeridiano" per merenda/spuntino pomeridiano (tra pranzo e cena)
  * "cena" per il pasto serale
  * altri nomi se specificati nella conversazione in maniera diversa
- NON usare "spuntino" generico - specifica sempre se è mattutino o pomeridiano
- Se il testo parla di "merenda" senza specificare, considera "spuntino_pomeridiano"
- Analizza il contesto temporale per determinare il tipo di spuntino

IMPORTANTE PER LA DIETA SETTIMANALE:
- Se nella conversazione è presente una dieta settimanale completa (giorni 2-7), estrai TUTTI i dati
- La sezione "weekly_diet_days_2_7" deve contenere SOLO i giorni 2-7 (il giorno 1 è già nei "weekly_diet_day_1")
- Per ogni giorno, estrai tutti i pasti con i loro alimenti e grammature con sostituti se specificati nella conversazione
- Se ci sono informazioni sui target nutrizionali e valori effettivi, includili
- Se l'agente ha fornito dettagli sui macronutrienti per pasto, estraili accuratamente
- Cerca pattern come "GIORNO 2:", "GIORNO 3:", etc. nella conversazione
- Ogni pasto deve avere la struttura completa con alimenti e valori nutrizionali

ESEMPI DI ESTRAZIONE DIETA SETTIMANALE:
- "GIORNO 2 - Colazione: Avena 45g, Banana 120g" → 
  "giorno_2": {"colazione": {"alimenti": [{"nome_alimento": "Avena", "quantita_g": 45, "misura_casalinga": "due pugni di avena", "sostituti": "50g di fiocchi di cereali, 40g di muesli"}, {"nome_alimento": "Banana", "quantita_g": 120, "misura_casalinga": "1 banana piccola", "sostituti": "150g di mela, 100g di pera"}]}}
- "Target: 400 kcal, 15g proteine" → 
  "target_nutrients": {"kcal": 400, "proteine": 15}

MODIFICHE PARZIALI DELLA DIETA SETTIMANALE:
- Usa "weekly_diet_partial_days_2_7" quando viene richiesta la modifica di un singolo pasto specifico tra giorno 2 e giorno 7.
- RICONOSCIMENTO AUTOMATICO: "rifai [pasto] giorno [numero]", "cambia [pasto] giorno [numero]", "modifica [pasto] giorno [numero]"

**ESEMPI DI RICONOSCIMENTO**:
- "rifai cena giorno 4" → weekly_diet_partial_days_2_7 con day="giorno_4", meal="cena"
- "cambia pranzo giorno 3" → weekly_diet_partial_days_2_7 con day="giorno_3", meal="pranzo"  
- "rifai colazione giorno 2" → weekly_diet_partial_days_2_7 con day="giorno_2", meal="colazione"
- "modifica spuntino giorno 5" → weekly_diet_partial_days_2_7 con day="giorno_5", meal="spuntino_pomeridiano"

**FORMATO OUTPUT**:
"weekly_diet_partial_days_2_7": {
  "day": "giorno_X",
  "meal": "nome_pasto",
  "data": {
    "alimenti": [{"nome_alimento": "...", "quantita_g": X, "misura_casalinga": "...", "sostituti": "..."}]
  }
}

**REGOLE**:
- Se utente chiede più di un pasto, ma non per un giorno intero, usa "weekly_diet_partial_days_2_7" per ciascun pasto
- NON USARE "weekly_diet_partial_days_2_7" se utente chiede di modificare un giorno intero di dieta o più giorni, usa "weekly_diet_days_2_7" in quel caso
- weekly_diet_partial_days_2_7 preserva tutti gli altri pasti del giorno invariati

REGOLE FONDAMENTALI PER GLI AGGIORNAMENTI - MOLTO IMPORTANTE:
- **NON AZZERARE MAI CAMPI CHE NON SONO MENZIONATI NELLA CONVERSAZIONE CORRENTE**
- **ESTRAI E AGGIORNA SOLO I CAMPI EFFETTIVAMENTE DISCUSSI NELLE INTERAZIONI CORRENTI**
- **NON INSERIRE MAI 0 COME VALORE PREDEFINITO**: Se un valore non è presente, OMETTI il campo
- Se nella conversazione si parla solo di "caloric_needs", NON restituire campi vuoti per "macros_total", "weekly_diet_day_1", etc.
- Se si modifica solo un pasto specifico, usa "weekly_diet_partial_days_2_7" e NON modificare altri pasti
- Se si aggiorna solo la distribuzione calorica, NON azzerare i pasti registrati
- **PRINCIPIO DI INCREMENTALITÀ**: Ogni estrazione deve aggiungere o modificare solo ciò che è esplicitamente discusso
- **MAI RIMUOVERE DATI**: Se un campo esisteva prima e non è menzionato ora, NON includerlo nel JSON di output

ALTRE REGOLE:
- Restituisci SOLO il JSON, nessun altro testo
- Se un dato non è presente nella conversazione corrente, ometti completamente quella sezione
- I numeri devono essere numerici, non stringhe
- Cerca con attenzione i calcoli numerici nella conversazione
- **RICORDA**: È meglio restituire meno campi (solo quelli discussi) che restituire campi vuoti o azzerati
"""
        
        return prompt
    
