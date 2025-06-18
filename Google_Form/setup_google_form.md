# 🚀 Setup Google Form per NutrAICoach

## 📋 Passaggi per Creare il Form

### 1. Crea un nuovo Google Form
1. Vai su [forms.google.com](https://forms.google.com)
2. Clicca su "+ Blank"
3. Titolo: "Feedback Tester - NutrAICoach"
4. Descrizione: "Grazie per aver testato NutrAICoach! Il tuo feedback è prezioso per migliorare l'esperienza."

### 2. Importa le Domande
Copia le domande dal file `questionario_feedback_tester.md` seguendo questa struttura:

### 3. Configura le Risposte
1. Vai su "Responses" tab
2. Clicca sul foglio verde per creare/collegare un Google Sheet
3. Nome del foglio: "NutrAICoach_Feedback_Tester"

### 4. Impostazioni Form Consigliate
- ✅ Collect email addresses (opzionale)
- ✅ Limit to 1 response
- ✅ Show progress bar
- ✅ Shuffle question order: OFF

## 📊 Struttura Google Sheet

Il Google Sheet avrà automaticamente queste colonne:
- Timestamp
- Tutte le risposte alle domande

### Colonne Aggiuntive da Aggiungere Manualmente:
- `Costo_Sessione_EUR` (da calcolare con i token)
- `Durata_Sessione_Min`
- `Numero_Messaggi`
- `User_ID`

## 🔗 Link Utili per i Tester

### Template Email per i Tester:
```
Ciao [Nome],

Ti invito a testare NutrAICoach, un assistente nutrizionale AI che crea piani alimentari personalizzati.

**Come partecipare:**
1. Accedi all'app: [link_app]
2. Completa l'intero processo (circa 20-30 minuti)
3. Compila il feedback: [link_google_form]

**Cosa testare:**
- Registrazione e setup iniziale
- Conversazione con l'AI
- Qualità del piano nutrizionale
- Download e contenuto del PDF

Il tuo feedback è fondamentale per migliorare il servizio!

Grazie,
[Tuo Nome]
```

## 📈 Analisi dei Risultati

### Metriche Chiave da Monitorare:
1. **Net Promoter Score** (domanda 28)
2. **Soddisfazione Generale** (domanda 5)
3. **Willingness to Pay** (domanda 20)
4. **Conversion Rate** (domanda 18)

### Dashboard Suggerita:
1. **Overview**
   - Numero totale risposte
   - NPS medio
   - Soddisfazione media
   - Prezzo medio disposti a pagare

2. **Analisi Dettagliata**
   - Distribuzione tempi di completamento
   - Problemi tecnici più comuni
   - Features più richieste
   - Confronto con competitor

3. **Insights Qualitativi**
   - Word cloud dei commenti
   - Temi ricorrenti nei feedback
   - Suggerimenti prioritari

## 🎯 Target per Beta Testing

### Numero Ideale di Tester:
- **Minimo**: 30 tester
- **Ideale**: 50-100 tester
- **Diversificati per**:
  - Età (18-65)
  - Genere
  - Esperienza con diete
  - Competenze tecnologiche

### Criteri di Selezione:
1. Interessati a nutrizione/benessere
2. Disponibili per 30-45 minuti
3. Capaci di dare feedback costruttivo
4. Mix di utenti tech-savvy e non

## 📝 Note per l'Analisi

### Correlazioni da Verificare:
- Durata sessione vs Soddisfazione
- Numero messaggi vs Qualità percepita
- Età vs Facilità d'uso
- Costo sessione vs Willingness to pay

### Red Flags da Monitorare:
- Tempo completamento > 45 min
- NPS < 7
- Problemi tecnici ricorrenti
- Abbandoni durante il processo 