"""
Funzioni per la gestione del frontend degli sport nel sistema NutrAICoach.

Questo modulo contiene tutte le funzioni necessarie per gestire la selezione
e configurazione degli sport durante l'onboarding e la gestione profilo utente.
"""

import streamlit as st
import json
import os


def load_sports_data():
    """Carica i dati degli sport dal file JSON e li organizza per categoria."""
    try:
        with open(os.path.join("Dati_processed", "sport_calories.json"), 'r', encoding='utf-8') as file:
            sports_data = json.load(file)
        
        # Organizza gli sport per categoria
        sports_by_category = {}
        for sport_name, sport_info in sports_data["sports"].items():
            category = sport_info["category"]
            if category not in sports_by_category:
                sports_by_category[category] = []
            
            # Formatta il nome dello sport (sostituisci '_' con spazi e prima lettera di ogni parola maiuscola)
            words = sport_name.split('_')
            formatted_name = ' '.join(word.capitalize() for word in words)
            
            sports_by_category[category].append({
                "name": formatted_name,
                "key": sport_name,
                "kcal_per_hour": sport_info["kcal_per_hour"],
                "description": sport_info["description"]
            })
        
        # Ordina alfabeticamente gli sport in ogni categoria
        for category in sports_by_category:
            sports_by_category[category] = sorted(sports_by_category[category], key=lambda x: x["name"])
        
        return sports_data["sports"], sports_by_category
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati degli sport: {str(e)}")
        return {}, {}


def get_sports_by_category(category_name):
    """Restituisce la lista degli sport per una categoria specifica."""
    # Mappa i nomi delle categorie del menu a quelli del file JSON
    category_map = {
        "Fitness - Allenamento medio (principianti e livello intermedio)": "Fitness - Allenamento medio",
        "Fitness - Bodybuilding Massa": "Fitness - Bodybuilding Massa",
        "Fitness - Bodybuilding Definizione": "Fitness - Bodybuilding Definizione",
        "Sport di forza (es: powerlifting, sollevamento pesi, strongman)": "Sport di forza",
        "Sport di resistenza (es: corsa, ciclismo, nuoto, triathlon)": "Sport di resistenza",
        "Sport aciclici (es: tennis, pallavolo, arti marziali, calcio)": "Sport aciclici",
        "Altro": None
    }
    
    # Carica i dati degli sport se non sono già in session_state
    if "sports_data" not in st.session_state or "sports_by_category" not in st.session_state:
        st.session_state.sports_data, st.session_state.sports_by_category = load_sports_data()
    
    mapped_category = category_map.get(category_name)
    
    # Debug: stampa le categorie disponibili
    print(f"Categoria selezionata: {category_name}")
    print(f"Categoria mappata: {mapped_category}")
    print(f"Categorie disponibili: {list(st.session_state.sports_by_category.keys())}")
    
    if mapped_category and mapped_category in st.session_state.sports_by_category:
        return st.session_state.sports_by_category[mapped_category]
    else:
        # Se la categoria non esiste o è "Altro", mostra tutti gli sport
        all_sports = []
        for category, sports in st.session_state.sports_by_category.items():
            all_sports.extend(sports)
        # Rimuovi duplicati e ordina
        return sorted(all_sports, key=lambda x: x["name"])


def on_sport_category_change(i):
    """
    Callback per reagire al cambio di categoria sport.
    Rimuove la selezione precedente dello sport specifico per forzare una nuova selezione.
    
    Args:
        i: indice dello sport nella lista
    """
    print(f"Categoria sport cambiata per sport index {i}")
    
    # Rimuovi la selezione precedente dello sport specifico per forzare una nuova selezione
    if f"specific_sport_{i}" in st.session_state:
        del st.session_state[f"specific_sport_{i}"]
    
    # Assicurati che i dati degli sport siano caricati
    if "sports_data" not in st.session_state or "sports_by_category" not in st.session_state:
        st.session_state.sports_data, st.session_state.sports_by_category = load_sports_data()
    
    # Aggiorna la lista degli sport in session_state
    if "sports_list" in st.session_state and i < len(st.session_state.sports_list):
        selected_category = st.session_state[f"sport_type_{i}"]
        print(f"Nuova categoria selezionata: {selected_category}")
        
        # Aggiorna la categoria nello sports_list
        st.session_state.sports_list[i]["sport_type"] = selected_category
        
        # Rimuovi lo sport specifico selezionato precedentemente
        if "specific_sport" in st.session_state.sports_list[i]:
            del st.session_state.sports_list[i]["specific_sport"] 