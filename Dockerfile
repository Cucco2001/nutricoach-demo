# Usa l'immagine Python ufficiale come base
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file di requirements per installare le dipendenze
COPY requirements.txt .

# Installa le dipendenze del sistema necessarie per alcune librerie Python
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice dell'applicazione
COPY . .

# Espone la porta 7860 (porta standard per Hugging Face Spaces)
EXPOSE 7860

# Comando per avviare l'applicazione Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"] 