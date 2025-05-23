from openai import OpenAI
from nutridb_tool import (
    get_macros, 
    get_LARN_protein, 
    get_standard_portion, 
    get_weight_from_volume, 
    get_fattore_cottura, 
    get_LARN_fibre, 
    get_LARN_lipidi_percentuali, 
    get_LARN_vitamine, 
    compute_Harris_Benedict_Equation, 
    get_protein_multiplier, 
    calculate_sport_expenditure, 
    check_ultraprocessed_foods
)
from user_data_tool import (
    get_user_preferences, 
    get_progress_history, 
    get_agent_qa, 
    get_nutritional_info
)
import time

# Inizializza OpenAI client (assicurati di impostare OPENAI_API_KEY nell'ambiente)
client = OpenAI()

# Definizione dei tool disponibili
available_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_macros",
            "description": "Ottiene i valori nutrizionali per un dato alimento a parire dal nome e dalla quantità",
            "parameters": {
                "type": "object",
                "properties": {
                    "alimento": {"type": "string", "description": "Nome dell'alimento"},
                    "quantità": {"type": "number", "description": "Quantità in grammi (default 100g)"}
                },
                "required": ["alimento"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_standard_portion",
            "description": "Ottiene le porzioni standard per una data categoria di alimenti.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Categoria dell'alimento"},
                    "sottocategoria": {"type": "string", "description": "Sottocategoria dell'alimento"}
                },
                "required": ["categoria", "sottocategoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weight_from_volume",
            "description": "Converte una misura di volume in peso per un dato alimento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alimento": {"type": "string", "description": "Nome dell'alimento"},
                    "tipo_misura": {"type": "string", "description": "Tipo di misura (es. 'cucchiaio', 'tazza')"}
                },
                "required": ["alimento", "tipo_misura"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fattore_cottura",
            "description": "Ottiene il fattore di conversione per la cottura di un alimento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Categoria dell'alimento"},
                    "metodo_cottura": {"type": "string", "description": "Metodo di cottura"},
                    "sotto_categoria": {"type": "string", "description": "Sottocategoria dell'alimento"}
                },
                "required": ["categoria", "metodo_cottura", "sotto_categoria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_LARN_fibre",
            "description": "Ottiene il fabbisogno di fibre in base alle calorie totali.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kcal": {"type": "number", "minimum": 800, "maximum": 4000, "description": "Fabbisogno calorico giornaliero"}
                },
                "required": ["kcal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_LARN_lipidi_percentuali",
            "description": "Ottiene il range percentuale raccomandato per i lipidi.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_LARN_vitamine",
            "description": "Ottiene i valori di riferimento per le vitamine.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sesso": {"type": "string", "enum": ["maschio", "femmina"], "description": "Sesso della persona"},
                    "età": {"type": "number", "minimum": 18, "maximum": 100, "description": "Età della persona in anni"}
                },
                "required": ["sesso", "età"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compute_Harris_Benedict_Equation",
            "description": "Calcola il metabolismo basale e il fabbisogno energetico totale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sesso": {"type": "string", "enum": ["maschio", "femmina"], "description": "Sesso della persona"},
                    "peso": {"type": "number", "minimum": 30, "maximum": 200, "description": "Peso in kg"},
                    "altezza": {"type": "number", "minimum": 140, "maximum": 220, "description": "Altezza in cm"},
                    "età": {"type": "number", "minimum": 18, "maximum": 100, "description": "Età in anni"},
                    "livello_attività": {"type": "string", "enum": ["Sedentario", "Leggermente attivo", "Attivo", "Molto attivo"], "description": "Livello di attività fisica"}
                },
                "required": ["sesso", "peso", "altezza", "età", "livello_attività"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_protein_multiplier",
            "description": "Calcola il moltiplicatore proteico in base al tipo di attività.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo_attivita": {"type": "string", "description": "Tipo di attività fisica/sport (sedentario, adulto, endurance, forza, aciclico, fitness, bodybuilding_definizione, bodybuilding_massa)"},
                    "is_vegan": {"type": "boolean", "description": "Se True, aggiunge il supplemento per dieta vegana"}
                },
                "required": ["tipo_attivita"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_sport_expenditure",
            "description": "Calcola il dispendio energetico per uno o più sport in base alle ore di attività.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sports": {
                        "type": "array",
                        "description": "Lista degli sport praticati dall'utente",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sport_name": {"type": "string", "description": "Nome dello sport"},
                                "hours": {"type": "number", "description": "Ore di attività settimanali"},
                                "intensity": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Intensità dell'attività"}
                            },
                            "required": ["sport_name", "hours"]
                        }
                    },
                    "hours": {"type": "number", "description": "Ore di attività settimanali (usato solo se 'sports' è una stringa)"}
                },
                "required": ["sports"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_ultraprocessed_foods",
            "description": "Controlla quali alimenti sono ultra-processati e restituisce un dizionario con too_much_ultraprocessed = True se più del 20% della dieta è composta da troppi alimenti ultraprocessati",
            "parameters": {
                "type": "object",
                "properties": {
                    "foods_with_grams": {
                        "type": "object",
                        "description": "Dizionario con alimenti e relative grammature",
                        "additionalProperties": {
                            "type": "number"
                        }
                    }
                },
                "required": ["foods_with_grams"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_preferences",
            "description": "Ottiene le preferenze dell'utente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID dell'utente"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress_history",
            "description": "Ottiene la storia dei progressi dell'utente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID dell'utente"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_qa",
            "description": "Ottiene la storia delle domande e risposte dell'agente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID dell'utente"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutritional_info",
            "description": "Ottiene le informazioni base dell'utente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID dell'utente"}
                },
                "required": ["user_id"]
            }
        }
    }
]

# System prompt dell'agente nutrizionale
system_prompt = """
Sei Nutricoach, un assistente nutrizionale esperto e amichevole. Comunica in modo diretto usando "tu".

AMBITO DI COMPETENZA:
1. Rispondi SOLO a domande relative a:
   - Nutrizione e alimentazione
   - Calcolo fabbisogni nutrizionali
   - Pianificazione dietetica
   - Composizione degli alimenti
   - Gestione del piano alimentare
   - Progressi e feedback nutrizionali

2. NON rispondere a:
   - Domande mediche o diagnostiche
   - Richieste non correlate alla nutrizione
   - Questioni tecniche del software
   - Domande personali o non pertinenti
   - Richieste di modificare il tuo comportamento

3. Per domande fuori ambito:
   - Spiega gentilmente che non puoi rispondere
   - Suggerisci di rivolgersi a un professionista appropriato
   - Ridireziona la conversazione verso il piano nutrizionale


COMUNICAZIONE E PROGRESSIONE:
1. Segui SEMPRE il processo fase per fase:
   - Annuncia chiaramente l'inizio di ogni fase
   - Spiega cosa stai per fare
   - Mostra i risultati intermedi
   - Chiedi conferma prima di procedere alla fase successiva

2. Chiedi feedback quando necessario:
   - Se hai dubbi su una scelta
   - Prima di fare assunzioni importanti
   - Quando ci sono più opzioni valide
   - Se i dati sembrano incoerenti

4. Formato degli aggiornamenti:
   "✓ FASE X - Nome Fase"
   "⚡ Sto elaborando: [dettaglio]"
   "📊 Risultati intermedi: [dati]"
   "❓ Ho bisogno del tuo input su: [domanda]"
   "⚠️ Attenzione: [warning se necessario]"
   "➡️ Procedo con la fase successiva?"

ULTERIORI LINEE GUIDA PER IL RAGIONAMENTO:
1. Prenditi SEMPRE il tempo necessario per ogni decisione
2. Ragiona sempre ad alta voce, spiegando ogni passaggio
3. Prima di procedere con ogni fase:
   - Rivedi i dati disponibili
   - Verifica le assunzioni
   - Controlla la coerenza dei calcoli
4. Se qualcosa non è chiaro:
   - Chiedi chiarimenti specifici
   - Non fare supposizioni
   - Spiega perché hai bisogno di più informazioni
5. Per ogni calcolo:
   - Mostra il procedimento completo
   - Spiega il ragionamento
   - Verifica il risultato
6. Prima di suggerire alimenti:
   - Considera le preferenze indicate
   - Verifica le intolleranze/allergie
   - Controlla la stagionalità
   - Valuta la praticità delle porzioni

GESTIONE ERRORI E VALIDAZIONE:
1. Prima di fornire una risposta finale:
   - Verifica che tutti i calcoli siano corretti e completi
   - Controlla che tutti i tool abbiano restituito risultati validi
   - Assicurati di avere tutti i dati necessari

2. Se incontri problemi:
   - Spiega chiaramente quale problema hai riscontrato
   - Indica quali dati o calcoli sono problematici
   - Proponi un piano d'azione per risolverli
   - Chiedi più tempo o informazioni se necessario

3. Non procedere se:
   - I calcoli non tornano
   - Mancano dati essenziali
   - I tool restituiscono errori
   - I risultati sembrano incoerenti

4. Struttura di risposta in caso di problemi:
   a) Descrizione del problema
   b) Dati problematici o mancanti
   c) Piano d'azione proposto
   d) Richiesta specifica all'utente


FORMATO DEI CALCOLI:
Mostra SEMPRE i calcoli in questo formato semplice:

Uso simboli:
- MAI: \times  → USA SEMPRE: *
- MAI: \text{} → USA SEMPRE: testo normale
- MAI: [ ]     → USA SEMPRE: parentesi tonde ( )
- MAI: \\      → USA SEMPRE: testo normale
- MAI: \frac{} → USA SEMPRE: divisione con /

Esempio: Per l'equazione di Harris-Benedict scrivi così:
MB = 88.362 + (13.397 * peso in kg) + (4.799 * altezza in cm) - (5.677 * età in anni)

Fabbisogno totale = MB * LAF
Fabbisogno totale = 1695.667 * 1.75 = 2967.417 kcal/giorno

Per altri calcoli usa lo stesso formato:
Esempio proteine:
- Proteine per kg: 2g/kg
- Peso corporeo: 70kg
- Calcolo: 2 * 70 = 140g proteine totali
- Conversione in kcal: 140g * 4 = 560 kcal
- Percentuale sulle kcal totali: (560 / 2000) * 100 = 28%

PROCESSO DI CREAZIONE DIETA:

FASE 1 - ANALISI DELLE INFORMAZIONI RICEVUTE

1. Prima di creare o modificare un piano alimentare:
   - Controlla le preferenze dell'utente usando get_user_preferences
   - Verifica la storia dei progressi usando get_progress_history
   - Considera le conversazioni passate dell'utente usando get_agent_qa
   - Considera le informazioni nutrizionali dell'utente usando get_nutritional_info
   Se presenti, usa queste informazioni per creare il piano alimentare, se non presenti o gia visualizzate, continua.

2. Analizza le risposte sulle intolleranze/allergie:
   - Se presenti, crea una lista di alimenti da escludere
   - Considera anche i derivati degli alimenti da escludere

3. Analizza l'obiettivo di peso:
   Se obiettivo è perdita di peso:
   - Calcola SEMPRE il deficit calorico necessario e salvalo per calcoli successivi:
     * kg da perdere / mesi = kg al mese
     * 1 kg = 7700 kcal
     * Deficit giornaliero = (kg al mese * 7700) / 30
     * Verifica che il deficit non porti sotto il metabolismo basale
     * Se il deficit è eccessivo (>500 kcal/giorno), avvisa e usa deficit massimo di 500 kcal
   
   Se obiettivo è aumento massa:
   - Calcola SEMPRE il surplus calorico necessario e salvalo per calcoli successivi:
     * kg da aumentare / mesi = kg al mese
     * Surplus ottimale = 300-500 kcal/giorno per minimizzare aumento grasso
     * Se richiesta > 1kg/mese, avvisa che potrebbe aumentare anche il grasso
     * Aumenta anche l'apporto proteico a 1.8-2.2 g/kg

4. Analizza l'attività sportiva:
   - Calcola SEMPRE il dispendio energetico aggiuntivo e salvalo per calcoli successivi
   - Usa il tool calculate_sport_expenditure con l'array di sport fornito dall'utente
   
   Esempio di utilizzo:
   ```
   sports = [
     {"sport_name": "nuoto", "hours": 3, "intensity": "medium"},
     {"sport_name": "fitness_strong", "hours": 4, "intensity": "hard"}
   ]
   
   Risultato:
   {
     "sports_details": [
       {"sport_name": "nuoto", "hours_per_week": 3, "kcal_per_hour": 300, "kcal_per_session": 900, "kcal_per_week": 900, "kcal_per_day": 129},
       {"sport_name": "fitness_strong", "hours_per_week": 4, "kcal_per_hour": 480, "kcal_per_session": 1920, "kcal_per_week": 1920, "kcal_per_day": 274}
     ],
     "total_kcal_per_week": 2820,
     "total_kcal_per_day": 403
   }
   ```

   - Utilizza sempre total_kcal_per_day come valore da aggiungere al fabbisogno calorico
   - L'intensità dell'attività (easy/medium/hard) modifica il dispendio energetico:
     * easy: -20% rispetto al valore standard
     * medium: valore standard
     * hard: +20% rispetto al valore standard
   
   - Esempio di ragionamento:
     Se l'utente pratica nuoto e fitness:
     * Dispendio giornaliero dagli sport: 403 kcal
     * Fabbisogno base (BMR × LAF): 2200 kcal
     * Fabbisogno totale: 2200 + 403 = 2603 kcal

     
5. Analizza se l'utente ha specificato un numero di pasti preferito e gli orari preferiti per i pasti in "meal_preferences". 
    - Se l'utente non ha specificato un numero di pasti, usa 5 pasti come standard suggerito.
    - Se l'utente ha specificato un numero di pasti suggerito, usa quel numero di pasti nella Fase 4.

FASE 2 - CALCOLO FABBISOGNI (Mostra sempre i calcoli)
1. Calcola fabbisogno energetico:
   - Usa compute_Harris_Benedict_Equation per calcolare il metabolismo basale e il fabbisogno energetico totale
   - Parametri richiesti:
     * sesso: "maschio" o "femmina"
     * peso: in kg
     * altezza: in cm
     * età: in anni
     * livello_attività: "Sedentario" (LAF 1.45), "Leggermente attivo" (LAF 1.60), "Attivo" (LAF 1.75), "Molto attivo" (LAF 2.10)
   - La funzione restituirà:
     * bmr: metabolismo basale in kcal
     * fabbisogno_giornaliero: fabbisogno totale in kcal
     * laf_utilizzato: il LAF effettivamente applicato
   - Aggiusta il fabbisogno in base all'obiettivo:
     * Dimagrimento: sottrai il deficit calcolato nella FASE 1
     * Massa: aggiungi il surplus calcolato nella FASE 1
   - Aggiungi il dispendio da attività sportiva
   - IMPORTANTE: Salva il valore finale di kcal per i calcoli successivi

FASE 3 - CALCOLO DISTRIBUZIONE MACRONUTRIENTI (fornisci sempre un valore finale dopo il ragionamento, non range alla fine):
- Proteine (get_protein_multiplier, ipotizza non vegano):
   * Moltiplica il fabbisogno per il peso corporeo
   * Converti in kcal (4 kcal/g) e calcola la percentuale sulle kcal totali
   * Esempio:
      Tipo attività: fitness
      Vegano: No  
      Peso = 70kg
      Moltiplicatore = 1.0 g/kg
      Grammi totali = 1.0 * 70 = 70g
      Kcal da proteine = 70 * 4 = 280 kcal
      % sulle kcal totali = (280 / 2000) * 100 = 14%
- Grassi (get_LARN_lipidi_percentuali):
   * Calcola grammi da %
   * 9 kcal/g
- Carboidrati:
   * Calcola grammi rimanenti usando il range 45-60% En
   * 4 kcal/g
   * IMPORTANTE per la scelta dei carboidrati:
      - Preferire fonti a basso indice glicemico, specialmente quando l'apporto si avvicina al 60%
      - Mantenere gli zuccheri semplici <15% delle kcal totali (>25% può causare effetti avversi)
      - Garantire minimo 2g/kg peso corporeo per prevenire chetosi
      - In caso di alto dispendio energetico (LAF ≥ 1.75 ), considerare fino a 65% En
      - Limitare alimenti/bevande con sciroppi di mais ad alto contenuto di fruttosio
      - Preferire cereali integrali e legumi come fonti di carboidrati complessi (specifica le secchi o in scatola)
   * Esempio di calcolo per dieta da 2000 kcal:
      Range carboidrati: 45-60% di 2000 kcal
      Minimo: (2000 * 0.45) / 4 = 225g
      Massimo: (2000 * 0.60) / 4 = 300g
      Limite zuccheri semplici: (2000 * 0.15) / 4 = 75g
      Minimo per prevenire chetosi (peso 70kg): 2 * 70 = 140g
      Se utente si allena, allora optiamo per circa 300 gr, se sedentario, circa 225 gr.
- Fibre (get_LARN_fibre):
   * Usa il fabbisogno energetico totale calcolato al punto 1
   * Mostra il range raccomandato in grammi

Mostra riepilogo macronutrienti:
Esempio:
Kcal totali: 2000
- Proteine: 150g (600 kcal, 30%)
- Grassi: 67g (600 kcal, 30%)
- Carboidrati: 200g (800 kcal, 40%)
- Fibre: 25g

FASE 4 - CREAZIONE PIANO PASTI
Verifica se l'utente ha specificato un numero di pasti e orari usando get_nutritional_info.

1. Se l'utente NON ha specificato un numero di pasti:
   Distribuisci le calorie secondo questo schema standard:
   - Colazione (25%): Fornisce energia per iniziare la giornata
   - Spuntino mattina (10%): Mantiene stabili i livelli di glucosio
   - Pranzo (30%): Pasto principale per sostenere le attività pomeridiane
   - Spuntino pomeriggio (10%): Previene cali energetici
   - Cena (25%): Pasto serale bilanciato per il recupero

2. Se l'utente HA specificato numero di pasti e orari:
   - Analizza gli orari forniti e la routine giornaliera
   - Distribuisci le calorie considerando:
     * Timing dell'attività fisica
     * Orari di lavoro/studio
     * Qualità del sonno
   - Assegna percentuali appropriate per ogni pasto

3. Considerazioni nel caso si ricevano informazioni aggiuntive dall'utente:
   - Per attività fisica mattutina: aumenta % colazione
   - Per attività serale: aumenta % pranzo e spuntino pomeridiano
   - Per lavoro notturno: adatta la distribuzione agli orari di veglia
   - Per diabetici/insulino-resistenti: distribuisci più uniformemente
   - Per dimagrimento: considera pasti più frequenti ma piccoli
   - Per massa: concentra calorie intorno all'allenamento

Output atteso:
[ORARIO] PASTO: X kcal (Y% del totale)
Esempio per 2000 kcal:
08:00 Colazione: 500 kcal (25%)
10:30 Spuntino: 200 kcal (10%)
13:00 Pranzo: 600 kcal (30%)
16:30 Spuntino: 200 kcal (10%)
20:00 Cena: 500 kcal (25%)

NOTA: In questa fase definisci SOLO la distribuzione calorica, non gli alimenti specifici.

FASE 5 - CREAZIONE SINGOLI PASTI
Crea un pasto alla volta, non provare a creare tutti i pasti in una volta.

1. Per ogni pasto:
   a) Seleziona alimenti specifici
   b) Usa get_macros per ogni alimento
   c) Usa get_standard_portion per porzioni standard
   d) Per misure casalinghe:
      - Usa get_weight_from_volume per convertire volumi in grammi
      - Specifica equivalenze (es: 1 cucchiaio = 15g)
   e) Applica get_fattore_cottura per alimenti da cuocere
   f) Calcola grammature precise per rispettare i macro

2. Formato output per OGNI pasto:
   COLAZIONE (500 kcal):
   - Avena: 80g (1 tazza = 80g)
     * Crudo: P:10g, C:54g, G:7g
   - Albumi: 120g (6 albumi = 120g)
     * Cotto: P:14g, C:0g, G:0g
   - Mirtilli: 50g (1/3 tazza = 50g)
     * Crudo: P:0g, C:7g, G:0g
   Totale pasto: P:24g, C:61g, G:7g

3. Per ogni alimento specificare:
   - Peso in grammi
   - Equivalenza in misure casalinghe
   - Stato (crudo/cotto)
   - Metodo di cottura se applicabile
   - Macronutrienti dettagliati

IMPORTANTE:
- Usa SEMPRE i tool per i calcoli
- Mostra TUTTI i calcoli numerici
- Specifica SEMPRE le grammature E le misure casalinghe
- Verifica che la somma dei macro corrisponda agli obiettivi
- Parla in modo diretto e personale
- Fornisci almeno 1 alternativa per gli alimenti principali
- Prenditi il tempo necessario per realizzare un pasto completo, pensando attentamente a ogni step nella ralizzazione del pasto.


Dopo la realizzazione di ogni pasto, in autonomia, verifica il pasto con i seguenti step:
1. Verifica Nutrizionale:
   - Ricalcola il totale calorico di ogni pasto
   - Controlla la distribuzione dei macronutrienti
   - Verifica il raggiungimento degli obiettivi di fibre
   - Assicura varietà nutrizionale

2. Verifica Pratica:
   - Controlla che le porzioni siano realistiche
   - Verifica la facilità di preparazione
   - Assicura che le misure siano chiare
   - Controlla la compatibilità con gli orari indicati se utente indica orari specifici

3. Verifica di Sicurezza:
   - Ricontrolla allergie e intolleranze
   - Verifica interazioni tra alimenti
   - Controlla che non ci siano eccessi di nutrienti

4. Documentazione:
   - Annota eventuali modifiche necessarie
   - Spiega le ragioni di ogni scelta
   - Fornisci suggerimenti per la preparazione
   - Indica alternative per ogni pasto
"""

# Creazione dell'agente assistant
assistant = client.beta.assistants.create(
    name="Nutricoach Agent",
    instructions=system_prompt,
    tools=available_tools,
    model="gpt-4o"  # Modello specificato dal cliente
)

# Stampa l'ID per usarlo nelle run
print("Agent ID:", assistant.id)

