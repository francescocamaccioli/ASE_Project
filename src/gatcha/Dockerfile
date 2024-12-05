FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia solo il file delle dipendenze prima
COPY requirements.txt /app/

# Installa le dipendenze necessarie
RUN pip install --no-cache-dir -r requirements.txt

# Copia i file del progetto nel container
COPY . /app

# Esponi la porta su cui l'app Flask girerà (5000)
EXPOSE 5000

# Comando di esecuzione dell'applicazione
CMD flask run --host=0.0.0.0 --port=5000 --debug --cert=/run/secrets/gatcha_cert --key=/run/secrets/gatcha_key