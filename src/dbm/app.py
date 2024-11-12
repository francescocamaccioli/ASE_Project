from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_gatcha = MongoClient("db-gatcha", 27017, maxPoolSize=50)
#client_user = MongoClient("db-user", 27017, maxPoolSize=50)
#client_market = MongoClient("db-market", 27017, maxPoolSize=50)

app = Flask(__name__, instance_relative_config=True)

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

# Endpoint per recuperare tutti i log (da un database centrale)
@app.route('/getAll', methods=['GET'])
def get_all_logs():
    try:
        logs = get_data_from_db(client_gatcha, 'db_manager_db', 'logs')
        return make_response(jsonify(logs), 200)
    except Exception as e:
        return make_response(str(e), 500)
    
# Endpoint per verificare la connessione al database
@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        # Esegui un ping al database per verificare la connessione
        client_gatcha.admin.command('ping')
        return make_response(jsonify({"message": "Connection to db-gatcha is successful!"}), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Failed to connect to db-gatcha"}), 500)
    

@app.route('/notify', methods=['POST'])
def add_log():
    try:
        payload = request.json  # Ottieni i dati JSON dal corpo della richiesta
        # Usa la funzione insert_data_to_db per inserire i dati nel database
        insert_data_to_db(client_gatcha, 'db_manager_db', 'logs', payload)
        return make_response(jsonify('ok'), 200)
    except Exception as e:
        return make_response(str(e), 500)


def create_app():
    return app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
