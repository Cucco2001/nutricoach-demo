import sys
import os
# Aggiungi la cartella parent al path per permettere gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from .prompts import available_tools, system_prompt
import time

# Inizializza OpenAI client (assicurati di impostare OPENAI_API_KEY nell'ambiente)
client = OpenAI()

# NOTA: available_tools e system_prompt sono ora importati da prompts.py per centralizzazione

# Creazione dell'agente assistant
assistant = client.beta.assistants.create(
    name="Nutricoach Agent",
    instructions=system_prompt,
    tools=available_tools,
    model="gpt-4o"  # Modello specificato dal cliente
)

# Stampa l'ID per usarlo nelle run
print("Agent ID:", assistant.id) 