"""
Definizione delle domande nutrizionali iniziali per l'onboarding utente.

Questo modulo contiene la configurazione completa delle domande che vengono
poste agli utenti durante la fase di registrazione iniziale nel sistema NutriCoach.
"""

# Definizione delle domande nutrizionali iniziali
NUTRITION_QUESTIONS = [
    {
        "id": "allergies",
        "question": "Hai qualche intolleranza o allergia alimentare?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": "Specifica quali:",
        "show_follow_up_on": "Sì"
    },
    {
        "id": "weight_goal",
        "question": lambda user_info: f"Quanti kg vuoi {'perdere' if user_info['obiettivo'] == 'Perdita di peso' else 'aumentare'} e in quanto tempo (in mesi)?",
        "type": "number_input",
        "show_if": lambda user_info: user_info["obiettivo"] in ["Perdita di peso", "Aumento di peso"],
        "fields": [
            {
                "id": "kg",
                "label": lambda user_info: f"Kg da {'perdere' if user_info['obiettivo'] == 'Perdita di peso' else 'aumentare'}",
                "min": 1,
                "max": 30,
                "default": 5
            },
            {
                "id": "months",
                "label": "In quanti mesi",
                "min": 1,
                "max": 24,
                "default": 3
            }
        ]
    },
    {
        "id": "sports",
        "question": "Pratichi sport?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": {
            "type": "multiple_sports",
            "fields": [
                {
                    "id": "sport_type",
                    "label": "Che tipo di attività sportiva pratichi?",
                    "type": "select",
                    "options": [
                        "Fitness - Allenamento medio (principianti e livello intermedio)",
                        "Fitness - Bodybuilding Massa",
                        "Fitness - Bodybuilding Definizione",
                        "Sport di forza (es: powerlifting, sollevamento pesi, strongman)",
                        "Sport di resistenza (es: corsa, ciclismo, nuoto, triathlon)",
                        "Sport aciclici (es: tennis, pallavolo, arti marziali, calcio)",
                        "Altro"
                    ]
                },
                {
                    "id": "specific_sport",
                    "label": "Specifica lo sport",
                    "type": "select",
                    "dynamic_options": True,
                    "options": []
                },
                {
                    "id": "intensity",
                    "label": "Intensità dell'attività",
                    "type": "select",
                    "options": ["easy", "medium", "hard"],
                    "descriptions": {
                        "easy": "Attività leggera (-20% calorie)",
                        "medium": "Attività moderata (calorie standard)",
                        "hard": "Attività intensa (+20% calorie)"
                    }
                },
                {
                    "id": "hours_per_week",
                    "label": "Quante ore alla settimana?",
                    "type": "number",
                    "min": 1,
                    "max": 30,
                    "default": 3
                }
            ]
        },
        "show_follow_up_on": "Sì"
    },
    {
        "id": "meal_preferences",
        "question": "Vuoi decidere tu il numero di pasti giornalieri?",
        "type": "radio",
        "options": ["No", "Sì"],
        "follow_up": {
            "type": "meal_schedule",
            "fields": [
                {
                    "id": "num_meals",
                    "label": "Quanti pasti vuoi fare al giorno?",
                    "type": "number",
                    "min": 1,
                    "max": 6,
                    "default": 5
                },
                {
                    "id": "meal_times",
                    "label": "A che ora vorresti fare i pasti? (opzionale)",
                    "type": "dynamic_time",
                    "optional": True,
                    "dynamic_count": "num_meals",
                    "meal_labels": [
                        "Colazione",
                        "Spuntino mattutino",
                        "Pranzo",
                        "Spuntino pomeridiano",
                        "Cena",
                        "Spuntino serale",
                        "Altro pasto"
                    ]
                }
            ]
        },
        "show_follow_up_on": "Sì"
    }
] 