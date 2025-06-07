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
                conversation_text = "\n\n".join([
                    f"UTENTE: {qa.question}\nAGENTE: {qa.answer}" 
                    for qa in conversation_history[-2:]  # Ultimi 3 scambi
                ])
                
                # Costruisci il prompt
                extraction_prompt = self._build_extraction_prompt(conversation_text, user_info)
                
                print(f"[DEEPSEEK_CLIENT] Tentativo {retry_count + 1}/{max_retries}")
                
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
                
                print(f"[DEEPSEEK_CLIENT] Dati estratti con successo: {list(extracted_data.keys())}")
                return extracted_data
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                print(f"[DEEPSEEK_CLIENT] Errore nel tentativo {retry_count}/{max_retries}: {error_msg}")
                
                if retry_count < max_retries:
                    wait_time = 5 * retry_count  # Attesa progressiva: 5s, 10s, 15s
                    print(f"[DEEPSEEK_CLIENT] Attendo {wait_time} secondi prima del prossimo tentativo...")
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
        return f"""
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
            "nome_pasto": "colazione/pranzo/cena/spuntino_mattutino/spuntino_pomeridiano o altri se specificati",
            "alimenti": [
                {{
                    "nome_alimento": "nome",
                    "quantita_g": numero_grammi_quando_possibile,
                    "stato": "crudo/cotto",
                    "metodo_cottura": "se_applicabile",
                    "misura_casalinga": "equivalenza_descrittiva_es_2_uova_1_tazza",
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

IMPORTANTE PER LE QUANTITÀ:
- "quantita_g": Inserisci il peso in grammi SOLO se menzionato esplicitamente in grammi
- Se sono menzionate unità diverse (es: "2 uova", "1 tazza", "3 fette"), NON convertire a grammi arbitrariamente
- Per unità non in grammi, metti 0 in "quantita_g" e spiega nella "misura_casalinga"
- "misura_casalinga": Descrivi sempre l'unità originale (es: "2 uova grandi", "1 tazza", "1 fetta di pane")

ESEMPI:
- "2 uova grandi" → quantita_g: 0, misura_casalinga: "2 uova grandi"
- "100g di pasta" → quantita_g: 100, misura_casalinga: "100g"
- "1 tazza di latte" → quantita_g: 0, misura_casalinga: "1 tazza"
- "3 fette di pane" → quantita_g: 0, misura_casalinga: "3 fette"

IMPORTANTE:
- Rileggi SEMPRE la conversazione e cerca di estrarre SEMPRE tutti i campi del JSON
- Le informazioni sono SEMPRE nella conversazione, quindi non inventare informazioni


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


ALTRE REGOLE:
- Restituisci SOLO il JSON, nessun altro testo
- Se un dato non è presente, ometti quella sezione
- I numeri devono essere numerici, non stringhe
- Cerca con attenzione i calcoli numerici nella conversazione
""" 