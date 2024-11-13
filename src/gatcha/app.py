import random
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

RARITY_PROBABILITIES = {
    'comune': 0.5,       # 50%
    'raro': 0.3,         # 30%
    'epico': 0.15,       # 15%
    'leggendario': 0.05  # 5%
}

# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_gatcha = MongoClient("db-gatcha", 27017, maxPoolSize=50)

app = Flask(__name__, instance_relative_config=True)

def weighted_random_choice(rarities):
    # Selects a rarity based on the predefined probabilities.
    rarity_list = list(rarities.keys())
    probability_list = list(rarities.values())
    return random.choices(rarity_list, probability_list, k=1)[0]

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
        insert_data_to_db(client_gatcha, 'gatcha_db', 'results', data)
        return make_response(jsonify({"message": "Data added to gatcha_db"}), 200)
    except Exception as e:
        return make_response(str(e), 500)


# Endpoint per rollare un gatcha
@app.route('/roll', methods=['GET'])
def roll_gatcha():
    try:
        # Estrai la rarità in base alle probabilità definite
        selected_rarity = weighted_random_choice(RARITY_PROBABILITIES)
        
        # Query al database per ottenere un personaggio della rarità selezionata
        gatcha_data = client_gatcha['gatcha_db']['results']
        character = gatcha_data.find_one({'rarity': selected_rarity})
        
        # Gestisci l'eventualità che non ci sia un personaggio di quella rarità
        if not character:
            return make_response(f"No character found for rarity {selected_rarity}\n", 404)
        
        return make_response(jsonify(character), 200)
    except Exception as e:
        return make_response(str(e), 500)

def create_app():
    return app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
