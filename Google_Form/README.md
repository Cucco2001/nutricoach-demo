# 📋 Google Form - Feedback Tester NutrAICoach

Questa cartella contiene tutti i materiali necessari per raccogliere feedback dai tester dell'applicazione NutrAICoach.

## 📂 Contenuto della Cartella

- **`questionario_feedback_tester.md`** - Lista completa di 32 domande per il feedback
- **`setup_google_form.md`** - Guida passo-passo per configurare Google Form e Sheets
- **`README.md`** - Questo file

## 🚀 Quick Start

1. **Crea il Form**
   - Vai su [forms.google.com](https://forms.google.com)
   - Importa le domande da `questionario_feedback_tester.md`

2. **Collega Google Sheets**
   - Nel form, vai su "Risposte" → Clicca sull'icona Sheets
   - Salva come "NutrAICoach_Feedback_Tester"

3. **Condividi con i Tester**
   - Ottieni il link del form
   - Invia insieme al link dell'app

## 📊 Dati da Integrare

Dopo che i tester compilano il form, aggiungi manualmente queste colonne nel Google Sheet:

- `User_ID` - Dal sistema NutrAICoach
- `Costo_Sessione_EUR` - Dal tracking dei token
- `Durata_Sessione_Min` - Dal tracking della sessione
- `Numero_Messaggi` - Dal contatore messaggi

## 📈 Metriche Chiave

Focus principale su:
- **NPS** (Net Promoter Score) - Domanda 28
- **Soddisfazione** - Domanda 5  
- **Willingness to Pay** - Domanda 20
- **Seguirebbe la dieta** - Domanda 18

## 🎯 Obiettivi Testing

- **Minimo**: 30 tester
- **Ideale**: 50-100 tester
- **Diversificati** per età, genere, esperienza

## 💡 Tips

- Raccogli feedback entro 24h dall'uso
- Offri incentivi per completare il form
- Analizza sia dati quantitativi che commenti
- Fai follow-up con utenti insoddisfatti 