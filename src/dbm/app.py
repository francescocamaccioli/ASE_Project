import time
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import bson.json_util as json_util

# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_gatcha = MongoClient("db-gatcha", 27017, maxPoolSize=50)
db_gatcha= client_gatcha["db_gatcha"]

client_user = MongoClient("db-user", 27017, maxPoolSize=50)
db_user= client_user["db_users"]
#client_market = MongoClient("db-market", 27017, maxPoolSize=50)

app = Flask(__name__, instance_relative_config=True)


# Endpoint per recuperare tutti i log (da un database gatcha)
@app.route('/getAll', methods=['GET'])
def get_all_logs():
    try:
        res = []
        all = list(db_user.collection.find({}))
        for element in all:
            res.append({'username': element["username"], 'password': element["password"]})
        return make_response(jsonify(res), 200)
    except Exception as e:
        print("DEBUG: Error fetching logs:", str(e))
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
    

# Endpoint per notificare un evento al database
@app.route('/notify', methods=['POST'])
def add_log():
    try:
        payload = request.json  
        db_gatcha.collection.insert_one(payload)
        return make_response(jsonify('ok'), 200)
    except Exception as e:
        return make_response(str(e), 500)
    
# Endpoint per la registrazione degli utenti
@app.route('/register', methods=['POST'])
def register_user():
    try:
        payload = request.json  # Ottieni i dati JSON dal corpo della richiesta 
        db_user.collection.insert_one(payload)
        return make_response(jsonify({"message": "User awdawdawd successfully"}), 200)

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)

# Endpoint per ottenere GLI utenti dal nome
@app.route('/get_user_from_name/<username>', methods=['GET'])
def get_user_from_name(username):
    try:
        res = []
        all = list(db_user.collection.find({"username": username}))
        for element in all:
            res.append({'username': element["username"], 'password': element["password"]})
        return make_response(jsonify(res), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

def create_app():
    return app