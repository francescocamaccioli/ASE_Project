FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia i file del progetto nel container
COPY . /app

# Installa le dipendenze necessarie
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta su cui l'app Flask girerà (5000)
EXPOSE 5000

# Comando di esecuzione dell'applicazione
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]
