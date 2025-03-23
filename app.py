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
        "Sei un nutrizionista professionista esperto in nutrizione sportiva e clinica. "
        "Ti chiedo di creare un piano alimentare settimanale altamente personalizzato per un paziente, "
        "basato su dati antropometrici, composizione corporea e obiettivi. "
        "Il piano deve essere bilanciato, realistico, semplice da seguire e clinicamente corretto secondo le linee guida LARN.\n\n"
        "Tutte le calorie e i valori nutrizionali devono essere calcolati utilizzando le tabelle ufficiali USDA e CREA, "
        "in modo da garantire la massima accuratezza nella stima energetica degli alimenti.\n\n"
        "### DATI DEL PAZIENTE:\n"
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
        prompt += f"- Preferenze: {preferenze}\n"
    if messaggio:
        prompt += f"- Altre indicazioni: {messaggio}\n"

    prompt += (
        "\n### STRUTTURA DEL PIANO RICHIESTA:\n"
        "- Piani giornalieri da Lunedì a Domenica\n"
        "- Ogni giorno deve includere: Colazione, Spuntino mattina, Pranzo, Merenda, Cena\n"
        "- Specificare dieta di ogni giorno e dare almeno un'alternativa per ciascun pasto\n"
        "- Specificare quantità in grammi, Kcal totali per giorno, e percentuale di macronutrienti (Carboidrati, Proteine, Grassi)\n"
        "- Ogni pasto deve essere facilmente replicabile, con ingredienti comuni\n"
        "- Varietà: tutti i pranzi e cene diversi nella settimana\n"
        "- Includere una lista della spesa finale con grammature totali suddivise per alimento\n\n"
        "### OUTPUT:\n"
        "Fornisci:\n"
        "1. Il piano alimentare settimanale (in formato leggibile per utente)\n"
        "2. Le kcal giornaliere e distribuzione dei macronutrienti\n"
        "3. Le fonti di riferimento per calorie e macro\n"
        "4. La lista della spesa con quantità totali per la settimana\n\n"
        "Scrivi in italiano, in modo chiaro, pratico e motivante. Inizia con una breve introduzione personalizzata per il paziente."
        "Nota bene: questo piano ha solo scopo educativo, simulativo e informativo, e non sostituisce una consulenza nutrizionale personalizzata.\n"
    )

    return prompt
# ---------------------- GPT CALL (updated for openai>=1.0.0) ----------------------
def get_dieta(prompt):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
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
        st.markdown("[Lascia un feedback qui](https://docs.google.com/forms/d/e/1FAIpQLSfzF3OpgEjLpgbPSFJpn6raAEOSdZEqprvcglSNLEJ5niA81w/viewform)")
