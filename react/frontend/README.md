# NutrAICoach Frontend

Frontend React per l'applicazione NutrAICoach - migrazione da Streamlit.

## 🚀 Avvio Rapido

```bash
# Installa le dipendenze
npm install

# Avvia il server di sviluppo
npm run dev

# Build per produzione
npm run build

# Preview della build
npm run preview
```

## 📁 Struttura del Progetto

```
src/
├── components/          # Componenti React
│   ├── Layout.tsx      # Layout principale con navigazione
│   ├── Login.tsx       # Componente di login
│   ├── Home.tsx        # Dashboard home
│   ├── Chat.tsx        # Interfaccia chat
│   ├── Diet.tsx        # Sezione dieta (placeholder)
│   ├── Settings.tsx    # Sezione impostazioni (placeholder)
│   └── *.css          # Stili componenti
├── contexts/           # React Context per state management
│   └── AuthContext.tsx # Gestione autenticazione
├── services/           # Servizi per comunicazione API
│   ├── authService.ts  # Servizio autenticazione
│   └── chatService.ts  # Servizio chat
├── App.tsx            # Componente principale
├── main.tsx           # Entry point
└── index.css          # Stili globali
```

## 🎨 Componenti Principali

### Layout
- **Header**: Logo, info utente, logout
- **Navigation**: Tab per le sezioni (Home, Diet, Chat, Settings)
- **Main Content**: Area contenuto dinamico
- **Responsive**: Adattivo mobile/desktop

### Chat
- **Interface Chat**: Messaggi utente/assistente
- **Input Form**: Invio messaggi con validazione
- **History**: Cronologia persistente
- **Loading States**: Indicatori di caricamento
- **Error Handling**: Gestione errori di rete
- **Suggested Questions**: Domande suggerite per iniziare

### Auth
- **Login Form**: Autenticazione utente
- **Session Management**: Gestione token
- **Route Protection**: Protezione route autenticate

## 🔧 Tecnologie e Librerie

### Core
- **React 18**: Framework UI principale
- **TypeScript**: Type safety e developer experience
- **Vite**: Build tool veloce con HMR

### Routing & State
- **React Router**: Client-side routing
- **React Context**: State management per auth

### HTTP & API
- **Axios**: HTTP client con interceptors
- **Custom Services**: Astrazione API calls

### UI & Styling
- **CSS Modules**: Styling isolato per componente
- **Responsive Design**: Mobile-first approach
- **Lucide React**: Libreria di icone moderne

## 🎯 Features Implementate

### ✅ Autenticazione
- Login con username/password
- Gestione automatica token
- Logout e session cleanup
- Protezione route autenticate
- Persistenza sessione (localStorage)

### ✅ Chat Interface
- Design moderno simile a chat apps popolari
- Messaggi con timestamp
- Scroll automatico ai nuovi messaggi
- Typing indicator durante caricamento
- Gestione errori con retry
- Cronologia persistente
- Bottoni azioni (clear history, new thread)

### ✅ Layout Responsivo
- Navigation tab adattiva
- Header con info utente
- Design mobile-first
- Breakpoints ottimizzati

### ✅ State Management
- AuthContext per stato globale autenticazione
- Gestione loading states
- Error boundaries

## 🌐 Comunicazione Backend

### Auth Service (`authService.ts`)
```typescript
// Login utente
authService.login(username, password)

// Logout
authService.logout()

// Info utente corrente
authService.getCurrentUser()

// Health check server
authService.healthCheck()
```

### Chat Service (`chatService.ts`)
```typescript
// Invia messaggio
chatService.sendMessage(message)

// Recupera cronologia
chatService.getChatHistory()

// Cancella cronologia
chatService.clearChatHistory()

// Gestione thread
chatService.createNewThread()
chatService.getCurrentThread()
```

## 🎨 Design System

### Colori
- **Primary**: Gradiente blu-viola (`#667eea` → `#764ba2`)
- **Background**: Grigio chiaro (`#f8f9fa`)
- **Text**: Grigio scuro (`#333`)
- **Cards**: Bianco con shadow

### Typography
- **Font**: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- **Line Height**: 1.5-1.6 per leggibilità
- **Font Sizes**: Sistema scalabile

### Spacing
- **Grid**: Sistema 8px base
- **Padding**: 1rem, 1.5rem, 2rem
- **Margins**: Auto per centratura

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

### Adaptations
- Navigation collapse su mobile
- Input form ottimizzato touch
- Chat messages responsive width
- Header semplificato mobile

## 🔄 Stati dell'Applicazione

### Auth States
- `isLoading`: Caricamento iniziale
- `isAuthenticated`: Stato autenticazione
- `user`: Dati utente corrente

### Chat States
- `messages`: Array messaggi
- `isLoading`: Invio messaggio in corso
- `error`: Gestione errori

## ⚡ Performance

### Ottimizzazioni
- **Code Splitting**: Componenti lazy-loaded
- **Tree Shaking**: Bundle ottimizzato
- **HMR**: Hot Module Replacement in dev
- **TypeScript**: Type checking compile-time

### Best Practices
- Componenti funzionali con hooks
- Memo per evitare re-render inutili
- Gestione cleanup effect
- Error boundaries

## 🧪 Testing

```bash
# Run tests (da implementare)
npm run test

# Test coverage
npm run test:coverage

# E2E tests
npm run test:e2e
```

## 🚀 Deploy

```bash
# Build ottimizzata per produzione
npm run build

# Preview build locale
npm run preview
```

Il build genera una cartella `dist/` con i file statici ottimizzati.

## 🔧 Configurazione

### Environment Variables
- `VITE_API_BASE_URL`: URL del backend API
- `VITE_NODE_ENV`: Ambiente (development/production)

### Vite Config
- Hot reload configurato
- Proxy per API development
- Build ottimizzazioni

## 📋 TODO

### Step 2: Features Chat
- [ ] Formattazione messaggi (markdown)
- [ ] Upload file/immagini
- [ ] Emoji picker
- [ ] Ricerca nella cronologia

### Step 3: Sezioni Principali
- [ ] Implementare Diet section
- [ ] Implementare Settings section
- [ ] Dashboard analytics Home

### Step 4: UX Improvements
- [ ] Tema scuro/chiaro
- [ ] Notifiche toast
- [ ] Shortcut da tastiera
- [ ] PWA capabilities

## 🤝 Contributing

1. Segui gli standard TypeScript
2. Usa componenti funzionali + hooks
3. Implementa responsive design
4. Gestisci loading/error states
5. Documenta props complesse

---

**Frontend URL**: `http://localhost:5173`
**Backend API**: `http://localhost:8000`
