# NutrAICoach Backend API

Backend FastAPI per l'applicazione NutrAICoach - Migrazione da Streamlit.

## Installazione

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

2. Configura le variabili d'ambiente:
   - Copia il file `.env.example` in `.env`
   - Aggiungi le tue chiavi API (OpenAI, Supabase, ecc.)

3. Avvia il server:
```bash
python run.py
```

Il server sarà disponibile su: `http://localhost:8000`

## Documentazione API

La documentazione interattiva è disponibile su:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints principali

### Autenticazione
- `POST /auth/login` - Login utente
- `POST /auth/logout` - Logout utente
- `GET /auth/me` - Informazioni utente corrente

### Chat
- `POST /chat/send` - Invia messaggio all'assistente
- `GET /chat/history` - Recupera cronologia chat
- `DELETE /chat/clear` - Cancella cronologia chat

### Thread Management
- `POST /chat/thread/create` - Crea nuovo thread
- `GET /chat/thread/current` - Ottieni thread corrente

## Utenti Demo

Per il testing, sono disponibili questi utenti:
- Username: `admin`, Password: `admin123`
- Username: `demo`, Password: `demo123`

## Struttura del progetto

```
backend/
├── main.py           # Applicazione FastAPI principale
├── config.py         # Configurazione dell'applicazione
├── run.py           # Script per avviare il server
├── requirements.txt  # Dipendenze Python
└── README.md        # Questo file
```

## Prossimi passi

1. **Integrazione OpenAI**: Sostituire la risposta mock con l'integrazione reale OpenAI Assistant API
2. **Database**: Sostituire il mock storage con un database reale (PostgreSQL/SQLite)
3. **Autenticazione sicura**: Implementare JWT con hash delle password
4. **Validazione**: Aggiungere validazione più robusta per i dati in input
5. **Logging**: Implementare logging per debugging e monitoraggio
6. **Rate limiting**: Aggiungere rate limiting per le API
7. **Tests**: Scrivere test automatici per gli endpoints 