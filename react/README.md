# NutrAICoach - Migrazione React

Migrazione graduale dell'applicazione NutrAICoach da Streamlit a React + FastAPI.

## 🎯 Stato Attuale della Migrazione

✅ **COMPLETATO - Step 1: Setup Base**
- Backend FastAPI con API per la chat
- Frontend React con Vite e 4 tabs (Home, Diet, Chat, Settings)
- Sistema di autenticazione funzionante
- Chat completamente implementata e funzionale

🚧 **PROSSIMI STEP**
- Integrazione OpenAI Assistant API nel backend
- Implementazione sezioni Diet e Settings
- Migrazione di più funzionalità da Streamlit

## 📁 Struttura del Progetto

```
react/
├── backend/          # API FastAPI
│   ├── main.py      # Server principale
│   ├── config.py    # Configurazione
│   ├── run.py       # Script di avvio
│   └── README.md    # Documentazione backend
└── frontend/         # App React
    ├── src/
    │   ├── components/   # Componenti React
    │   ├── contexts/     # Context per state management
    │   ├── services/     # Servizi per API calls
    │   └── App.tsx      # App principale
    └── README.md        # Documentazione frontend
```

## 🚀 Avvio Rapido

### 1. Backend (FastAPI)

```bash
cd react/backend
pip install -r requirements.txt
python run.py
```

Server disponibile su: `http://localhost:8000`
Documentazione API: `http://localhost:8000/docs`

### 2. Frontend (React)

```bash
cd react/frontend  
npm install
npm run dev
```

App disponibile su: `http://localhost:5173`

## 🔐 Autenticazione Demo

Credenziali di test:
- **Username:** `demo` / **Password:** `demo123`
- **Username:** `admin` / **Password:** `admin123`

## 🌟 Funzionalità Implementate

### ✅ Autenticazione
- Login/logout funzionale
- Gestione token di sessione
- Protezione delle route

### ✅ Chat Assistant
- Interfaccia chat moderna e responsive
- Cronologia messaggi persistente
- Invio/ricezione messaggi in tempo reale
- Gestione errori e loading states
- Domande suggerite per iniziare

### ✅ Layout e Navigazione
- Header con info utente e logout
- Navigazione tab responsive
- Layout adattivo mobile/desktop

### 🚧 Sezioni Placeholder
- **Home:** Dashboard di benvenuto
- **Diet:** Sezione in sviluppo
- **Settings:** Sezione in sviluppo

## 🔄 Migrazione da Streamlit

### API Migrate

Le seguenti API sono state migrate dal sistema Streamlit:

1. **Autenticazione** (`/auth/*`)
   - Login utente
   - Gestione sessioni
   - Informazioni utente

2. **Chat** (`/chat/*`)
   - Invio messaggi all'assistente
   - Cronologia conversazioni
   - Gestione thread

### Prossime API da Migrare

- Gestione dati nutrizionali
- Sistema preferenze alimentari
- Generazione piani dietetici
- Integrazione DeepSeek per estrazione dati

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI** - Framework web moderno e veloce
- **Pydantic** - Validazione dati
- **Uvicorn** - Server ASGI
- **OpenAI** - Integrazione AI (in preparazione)

### Frontend
- **React 18** - Framework UI
- **TypeScript** - Type safety
- **Vite** - Build tool veloce
- **React Router** - Routing client-side
- **Axios** - HTTP client
- **Lucide React** - Icone moderne

## 📋 Prossimi Sviluppi

### Step 2: Integrazione AI
- [ ] Collegare OpenAI Assistant API al backend
- [ ] Implementare sistema di tool calling
- [ ] Migrare agent tools da Streamlit

### Step 3: Funzionalità Nutrizionali
- [ ] API per gestione dati utente
- [ ] Sistema preferenze alimentari
- [ ] Generazione piani dietetici
- [ ] Analisi nutrizionale

### Step 4: Features Avanzate
- [ ] Sistema notifiche
- [ ] Export PDF
- [ ] Dashboard analytics
- [ ] Tema scuro/chiaro

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/nome-feature`)
3. Commit delle modifiche (`git commit -am 'Aggiunge nuova feature'`)
4. Push del branch (`git push origin feature/nome-feature`)
5. Crea una Pull Request

## 📞 Supporto

Per domande o problemi, consulta:
- [Backend README](./backend/README.md) per questioni API
- [Frontend README](./frontend/README.md) per questioni React
- Documentazione API: `http://localhost:8000/docs`

---

**Nota:** Questo è il primo step di una migrazione graduale. L'app Streamlit originale rimane funzionale durante tutto il processo di migrazione. 