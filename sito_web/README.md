# NutriCoach Landing Page

Landing page moderna e responsive per NutriCoach, il nutrizionista digitale intelligente.

## 🚀 Caratteristiche

- **Design Moderno**: Interfaccia pulita e professionale con gradienti accattivanti
- **Responsive**: Ottimizzato per desktop, tablet e mobile
- **Interattivo**: Animazioni fluide e effetti on-scroll
- **SEO Ready**: Struttura HTML semantica e meta tag ottimizzati

## 📁 Struttura File

```
sito_web/
├── index.html      # Pagina principale
├── styles.css      # Stili CSS
├── script.js       # JavaScript per interazioni
├── logo.png        # Logo NutriCoach
└── README.md       # Questo file
```

## ⚙️ Configurazione

### 1. URL Streamlit App

Nel file `script.js`, modifica la variabile `STREAMLIT_URL`:

```javascript
const STREAMLIT_URL = "https://tuo-url-streamlit.streamlit.app/";
```

### 2. Logo

Sostituisci `logo.png` con il tuo logo. Dimensioni consigliate: 200x200px o superiore.

### 3. Colori e Branding

Nel file `styles.css`, puoi personalizzare i colori principali:

```css
/* Colori principali */
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --accent-gradient: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
    --success-color: #28a745;
    --error-color: #dc3545;
}
```

## 🎯 Sezioni della Landing Page

### 1. Hero Section
- Titolo d'impatto con gradiente
- Descrizione del servizio
- Statistiche animate (20 minuti, 100% scientifico, 24/7 disponibile)

### 2. Piani di Servizio
- **Beta Gratuita**: Per tester (attiva)
- **Dieta AI**: $2 per piano (work in progress)
- **AI + Esperto**: $5 per piano revisionato (work in progress)

### 3. Come Funziona
- 3 step process: Chat → Preferenze → Piano Nutrizionale
- Icone e tempistiche per ogni fase

### 4. Vantaggi
- 6 card che evidenziano i punti di forza
- Fonti scientifiche, semplicità, economicità, velocità, affidabilità, accessibilità

### 5. Newsletter
- Form di iscrizione newsletter
- Gestione email con validazione

## 🔧 Personalizzazione

### Modifica Testi

Tutti i testi sono facilmente modificabili nell'`index.html`. Cerca i tag con le classi:
- `.hero-title` - Titolo principale
- `.hero-description` - Descrizione hero
- `.section-title` - Titoli sezioni
- `.benefit-card` - Card vantaggi

### Aggiungere Funzionalità

Per integrare un sistema di newsletter reale, modifica la funzione `handleNewsletterSubmit()` in `script.js`:

```javascript
function handleNewsletterSubmit(event) {
    // Integra qui il tuo servizio di newsletter (Mailchimp, ConvertKit, etc.)
    fetch('/api/newsletter', {
        method: 'POST',
        body: JSON.stringify({ email: email }),
        headers: { 'Content-Type': 'application/json' }
    });
}
```

## 📱 Responsive Design

La landing page è ottimizzata per:
- **Desktop**: Layout a 3 colonne per i piani
- **Tablet**: Layout a 2 colonne, navigazione compatta
- **Mobile**: Layout a 1 colonna, menu hamburger (da implementare se necessario)

## 🎨 Animazioni

- Smooth scroll per navigazione
- Fade in animato per card e sezioni
- Contatori animati nelle statistiche
- Effetti hover su bottoni e card
- Parallax leggero nell'hero section

## 🚀 Deploy

### Hosting Statico
Puoi hostare la landing page su:
- **Netlify**: Drag & drop della cartella `sito_web`
- **Vercel**: Deploy automatico da Git
- **GitHub Pages**: Push su repository e attiva Pages
- **AWS S3**: Upload file e configura come website

### Dominio Personalizzato
Per collegare un dominio personalizzato:
1. Configura i DNS del tuo dominio
2. Aggiungi il dominio nelle impostazioni del tuo hosting
3. Attiva HTTPS (solitamente automatico)

## 📊 Analytics

Per aggiungere Google Analytics, inserisci questo codice nel `<head>` di `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_TRACKING_ID');
</script>
```

## 🔍 SEO

Per migliorare la SEO, aggiungi nell'`<head>`:

```html
<meta name="description" content="NutriCoach - Il tuo nutrizionista digitale intelligente. Piano nutrizionale personalizzato in 20 minuti con AI.">
<meta name="keywords" content="nutrizionista digitale, dieta AI, piano nutrizionale, nutrizione personalizzata">
<meta property="og:title" content="NutriCoach - Nutrizionista Digitale Intelligente">
<meta property="og:description" content="Ottieni un piano nutrizionale personalizzato in 20 minuti">
<meta property="og:image" content="logo.png">
```

## 📞 Supporto

Per domande o personalizzazioni, contatta il team di sviluppo.

## Setup Google Sheets per Email Collection

### 1. Crea il Google Apps Script

. Crea un nuovo Google Sheet
Vai su sheets.google.com
Crea un nuovo foglio di calcolo
Chiamalo "NutriCoach Email Database" o simile
2. Imposta le colonne nel foglio
Nella prima riga, aggiungi queste intestazioni:
Colonna A: Email
Colonna B: Tipo (beta/newsletter)
Colonna C: Data
Colonna D: Ora
3. Crea il Google Apps Script
Nel tuo Google Sheet, vai su Estensioni > Apps Script
Cancella il codice esistente e incolla questo:
function doPost(e) {
  try {
    // Ottieni il foglio di calcolo
    const sheet = SpreadsheetApp.getActiveSheet();
    
    // Parsing dei dati JSON
    const data = JSON.parse(e.postData.contents);
    const email = data.email;
    const type = data.type || 'beta'; // 'beta' o 'newsletter'
    
    // Validazione email
    if (!email || !isValidEmail(email)) {
      return ContentService
        .createTextOutput(JSON.stringify({
          success: false,
          message: 'Email non valida'
        }))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Controlla se l'email esiste già per questo tipo
    const existingData = sheet.getDataRange().getValues();
    for (let i = 1; i < existingData.length; i++) {
      if (existingData[i][0] === email && existingData[i][1] === type) {
        return ContentService
          .createTextOutput(JSON.stringify({
            success: true,
            message: 'Email già presente',
            duplicate: true
          }))
          .setMimeType(ContentService.MimeType.JSON);
      }
    }
    
    // Aggiungi i dati al foglio
    const now = new Date();
    const dateString = Utilities.formatDate(now, Session.getScriptTimeZone(), 'dd/MM/yyyy');
    const timeString = Utilities.formatDate(now, Session.getScriptTimeZone(), 'HH:mm:ss');
    
    sheet.appendRow([email, type, dateString, timeString]);
    
    // Risposta di successo
    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: 'Email salvata con successo'
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    // Gestione errori
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: 'Errore interno: ' + error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Funzione per validare l'email
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Funzione per testare lo script (opzionale)
function testScript() {
  const testEvent = {
    postData: {
      contents: JSON.stringify({
        email: 'test@example.com',
        type: 'beta'
      })
    }
  };
  
  const result = doPost(testEvent);
  Logger.log(result.getContent());
} 
4. Pubblica il Google Apps Script
Salva il progetto (Ctrl+S)
Clicca su Implementa in alto a destra
Scegli Nuova implementazione
In "Tipo", seleziona App web
Imposta:
Esegui come: Me (il tuo account)
Chi ha accesso: Chiunque
Clicca Implementa
COPIA L'URL che ti viene fornito - questo è quello che dovrai mettere nel GOOGLE_SCRIPT_URL
5. Aggiorna l'URL nel tuo script.js
L'URL che hai messo sembra molto lungo e con caratteri duplicati. Sostituiscilo con l'URL corretto che ottieni dal passaggio 4.