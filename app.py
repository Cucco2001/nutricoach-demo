# NutriCoach - Powered by Giancarlo Cuccorese
# Streamlit app for generating personalized weekly diet plans using GPT

import streamlit as st
import pandas as pd
import datetime
import openai
import csv
import os

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="NutriCoach", page_icon="🥦")
st.title("NutriCoach 🥦")
st.markdown("**Powered by Giancarlo Cuccorese**")

# ---------------------- API SETUP ----------------------
# NOTE: Replace with your actual OpenAI API key or use environment variable
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else ""

# ---------------------- FORM ----------------------
st.subheader("Inserisci i tuoi dati per ricevere una dieta personalizzata")

with st.form("nutricoach_form"):
    col1, col2 = st.columns(2)
    with col1:
        eta = st.number_input("Età (anni)", min_value=10, max_value=100)
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0)
        massa_grassa = st.text_input("Massa grassa (%) - opzionale")
    with col2:
        sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])
        altezza = st.number_input("Altezza (cm)", min_value=120, max_value=220)
        massa_magra = st.text_input("Massa magra (kg) - opzionale")

    obiettivo = st.text_input("Qual è il tuo obiettivo (es. perdere peso, aumentare massa, mantenere)?")
    attivita = st.text_area("Descrivi la tua attività fisica settimanale (e.g. quante volte vai in palestra, quanto ti alleni, quanto ti muovi in generale. Piu info dai, meglio è)")
    preferenze = st.text_area("Hai allergie, intolleranze o alimenti da evitare?")
    messaggio = st.text_area("Scrivi qui se hai richieste particolari (es. 'vorrei più proteine', 'sono vegetariano')")

    submitted = st.form_submit_button("Genera la tua dieta")

# ---------------------- GENERATE PLAN ----------------------
def build_prompt():
    prompt = (
        "Sei un nutrizionista virtuale esperto in nutrizione sportiva e clinica. "
        "Simula la creazione di un esempio di piano alimentare settimanale per un profilo utente ipotetico, "
        "basato sui dati seguenti. Il piano deve essere bilanciato, semplice da seguire e ispirato alle linee guida LARN. "
        "Utilizza i valori nutrizionali delle tabelle ufficiali USDA e CREA per stimare le calorie.\n\n"
        "Nota: questo piano è solo a scopo educativo e non sostituisce una consulenza professionale.\n\n"
        "### DATI DELL’UTENTE:\n"
        f"- Sesso: {sesso}\n"
        f"- Età: {eta} anni\n"
        f"- Altezza: {altezza} cm\n"
        f"- Peso: {peso} kg\n"
    )

    if massa_grassa:
        prompt += f"- Massa grassa: {massa_grassa}%\n"
    if massa_magra:
        prompt += f"- Massa magra: {massa_magra} kg\n"
    if attivita:
        prompt += f"- Attività fisica: {attivita}\n"
    if obiettivo:
        prompt += f"- Obiettivo: {obiettivo}\n"
    if preferenze:
        prompt += f"- Preferenze alimentari: {preferenze}\n"
    if messaggio:
        prompt += f"- Altre indicazioni: {messaggio}\n"

    prompt += (
        "\n### STRUTTURA DEL PIANO RICHIESTA:\n"
        "- Un piano settimanale da lunedì a domenica\n"
        "- Ogni giorno con: colazione, spuntino, pranzo, merenda e cena\n"
        "- Bilancia ciascun pasto secondo direttive LARN, ogni pasto deve avere un apporto bilanciato di grassi, carboidrati e proteine"
        "- Includi due sostituzioni per TUTTI gli alimenti proposto che contenga circa gli stessi macronutrienti al fianco di ciascun cibo\n"
        "- Includi quantità in grammi (e anche numero cucchiai o cucchiaini ove possibile), kcal giornaliere al termine di ogni giorno, % di macronutrienti per ciascuna giornata\n"
        "- Almeno 3 pranzi e 3 cene diversi nella settimana\n"
        "- Ingredienti comuni e facili da reperire\n"
        "- Una spiegazione finale approfondita sul ragionamento utilizzato nel definire quel quantitativo di calorie e quella distribuzione di macronutrienti (basato su LARN, il calcolo per il totale di kcal, come modifica kcal giornaliere in base ad attività fisica del paziente con coefficiente moltiplicativo utilizzato)\n"
        "Scrivi in italiano, in modo chiaro, pratico e motivante.\n"
        "Il contenuto è puramente dimostrativo e non costituisce una prescrizione medica."
    )

    return prompt
# ---------------------- GPT CALL (updated for openai>=1.0.0) ----------------------
def get_dieta(prompt):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# ---------------------- SAVE TO CSV ----------------------
def salva_dati():
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "eta": eta,
        "sesso": sesso,
        "peso": peso,
        "altezza": altezza,
        "massa_grassa": massa_grassa,
        "massa_magra": massa_magra,
        "obiettivo": obiettivo,
        "attivita": attivita,
        "preferenze": preferenze,
        "messaggio": messaggio
    }
    file_path = "dati_nutricoach.csv"
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

# ---------------------- OUTPUT ----------------------
if submitted:
    with st.spinner("Sto generando la tua dieta personalizzata..."):
        prompt = build_prompt()
        output = get_dieta(prompt)
        salva_dati()
        st.success("Ecco la tua dieta settimanale!")
        st.markdown(output)
        st.info("NutriCoach è un prodotto in via di definizione. Il piano proposto ha scopo dimostrativo. Il tuo feedback ci aiuta a migliorarlo.")

        st.markdown("---")
        st.subheader("Hai una richiesta o modifica da fare alla dieta?")
        followup = st.text_area("Scrivi la tua domanda o modifica (es. 'vorrei più proteine a pranzo', 'sono intollerante al glutine')")
        if st.button("Chiedi a NutriCoach"):
            with st.spinner("Sto aggiornando la dieta su tua richiesta..."):
                followup_prompt = output + "\n\nModifica la dieta secondo questa richiesta dell'utente: " + followup + "\nRispondi con un nuovo piano aggiornato."
                followup_response = get_dieta(followup_prompt)
                st.markdown("### Dieta aggiornata su richiesta:")
                st.markdown(followup_response)
