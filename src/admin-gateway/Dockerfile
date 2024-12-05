# Usa l'immagine di base Python
FROM python:3.10-slim

# Setta la directory di lavoro
WORKDIR /app

# Copia i file dei requisiti per installare le dipendenze
COPY requirements.txt /app/

# Aggiorna pip e setuptools per risolvere eventuali vulnerabilità
RUN pip install --upgrade pip setuptools

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il contenuto del progetto nella directory di lavoro
COPY . /app

# Esponi la porta su cui il servizio Flask sarà in ascolto
EXPOSE 5000

# Comando di esecuzione dell'applicazione
CMD flask run --host=0.0.0.0 --port=5000 --debug --cert=/run/secrets/admin_gateway_cert --key=/run/secrets/admin_gateway_key
