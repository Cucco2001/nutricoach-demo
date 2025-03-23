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
    attivita = st.text_area("Descrivi la tua attività fisica settimanale (opzionale)")
    preferenze = st.text_area("Hai allergie, intolleranze o alimenti da evitare?")
    messaggio = st.text_area("Scrivi qui se hai richieste particolari (es. 'vorrei più proteine', 'sono vegetariano')")

    submitted = st.form_submit_button("Genera la tua dieta")

# ---------------------- GENERATE PLAN ----------------------
def build_prompt():
    prompt = f"""
Sei un nutrizionista professionista. Genera una dieta settimanale personalizzata e bilanciata per un utente con i seguenti dati:
Età: {eta} anni
Sesso: {sesso}
Peso: {peso} kg
Altezza: {altezza} cm
"""
    if massa_grassa:
        prompt += f"Massa grassa: {massa_grassa}%\n"
    if massa_magra:
        prompt += f"Massa magra: {massa_magra} kg\n"
    if attivita:
        prompt += f"Attività fisica: {attivita}\n"
    if obiettivo:
        prompt += f"Obiettivo: {obiettivo}\n"
    if preferenze:
        prompt += f"Allergie o alimenti da evitare: {preferenze}\n"
    if messaggio:
        prompt += f"Preferenze aggiuntive: {messaggio}\n"

    prompt += """
Genera un piano alimentare settimanale, dal lunedì alla domenica, con colazione, pranzo, cena e spuntini. Includi grammature, kcal giornaliere e proporzione di macronutrienti. Segui le linee guida LARN e utilizza valori nutrizionali dal database USDA. Rispondi in italiano.
"""
    return prompt

# ---------------------- GPT CALL ----------------------
def get_dieta(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1800,
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
