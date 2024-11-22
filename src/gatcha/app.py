import os
import random
from flask import Flask, request, make_response
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import bson.json_util as json_util

RARITY_PROBABILITIES = {
    'comune': 0.5,       # 50%
    'raro': 0.3,         # 30%
    'epico': 0.15,       # 15%
    'leggendario': 0.05  # 5%
}

# URLS dei microservizi
USER_URL = os.getenv('USER_URL')
MARKET_URL = os.getenv('MARKET_URL')

# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_gatcha = MongoClient("db-gatcha", 27017, maxPoolSize=50)
db_gatcha= client_gatcha["db_gatcha"]

app = Flask(__name__, instance_relative_config=True)

def weighted_random_choice(rarities):
    # Selects a rarity based on the predefined probabilities.
    rarity_list = list(rarities.keys())
    probability_list = list(rarities.values())
    return random.choices(rarity_list, probability_list, k=1)[0]

# TODO: non usata?
# Funzione generica per ottenere dati da un database specifico
def get_data_from_db(client, db_name, collection_name, query={}):
    db = client[db_name]
    collection = db[collection_name]
    return list(collection.find(query))

# Funzione generica per inserire dati in un database
def insert_data_to_db(client, db_name, collection_name, data):
    db = client[db_name]
    collection = db[collection_name]
    collection.insert_one(data)

# Endpoint per aggiungere dati nel database gacha_db
@app.route('/addgatchaData', methods=['POST'])
def add_gatcha_data():
    data = request.json
    try:
        insert_data_to_db(client_gatcha, 'db-gatcha', 'db_gatcha', data) 
        return make_response(json_util.dumps({"message": "Data added to gatcha_db"}), 200)
    except Exception as e:
        return make_response(str(e), 500)


# Endpoint per rollare un gatcha
@app.route('/roll', methods=['GET'])
def roll_gatcha():
    try:
        # Estrai la rarità in base alle probabilità definite
        selected_rarity = weighted_random_choice(RARITY_PROBABILITIES)
        
        # Query al database per ottenere un personaggio della rarità selezionata
        gachas = list(client_gatcha['gatcha_db']['gatchas'].find({"rarity": selected_rarity}))
       
        if not gachas:
            return make_response(f"No character found for rarity {selected_rarity}\n", 404)
        # Estrai un personaggio randomico dalla lista dei personaggi della rarità selezionata
        character = random.choice(gachas) if gachas else None
        
        # Gestisci l'eventualità che non ci sia un personaggio di quella rarità
        if not character:
            return make_response(f"No character found for rarity {selected_rarity}\n", 404)
        
        # Increment NTot for the selected character
        client_gatcha['gatcha_db']['gatchas'].update_one(
            {'_id': character['_id']},  # Trova il personaggio tramite il suo ID
            {'$inc': {'NTot': 1}}       # Incrementa il campo NTot di 1
        )

        ##TODO Communicate with user to update his collection
        
        return make_response(json_util.dumps(character), 200)
    except Exception as e:
        return make_response(str(e), 500)
    
# Endpoint per ottenere tutti i possibili gatcha
@app.route('/getAll', methods=['GET'])
def get_all_gatcha():
    try:
        all_gatcha = list(client_gatcha['gatcha_db']['gatchas'].find({}))
        return make_response(json_util.dumps(all_gatcha), 200)
    except Exception as e:
        return make_response(str(e), 500)

def create_app():
    return app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)