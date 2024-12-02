import os
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from auth_utils import decode_token, role_required, get_userID_from_jwt
from datetime import datetime

app = Flask(__name__)

# URLS dei microservizi
GATCHA_URL = os.getenv('GATCHA_URL')
MARKET_URL = os.getenv('MARKET_URL')



# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
client_user = MongoClient("db-user", 27017, maxPoolSize=50)
db_user= client_user["db_users"]

def userExists(userID):
    return db_user.collection.find_one({"userID": userID}) is not None

# Endpoint per registrare un utente passando i dati nel body della richiesta
@app.route('/init-user', methods=['POST'])
def init_user():
    try:
        payload = request.json  # Ottieni i dati JSON dal corpo della richiesta 
        if payload is None:
            return make_response(jsonify({"error": "No data provided"}), 400)
        
        if "userID" not in payload:
            return make_response(jsonify({"error": "No userID provided"}), 400)
        
        if userExists(payload.get("userID")):
            return make_response(jsonify({"error": "User already exists"}), 400)

        user = {
            "userID": payload.get("userID"),
            "balance": 0,
            "collection": [],
            "transactions": []
        }
        db_user.collection.insert_one(user)
        return make_response(jsonify({"message": "User initialized successfully"}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)
    
@app.route('/delete_user', methods=['POST'])
def delete_user():
    #receive user ID from POST request and delete the user from the database
    data = request.get_json()
    userID = data['userID']
    try:
        db_user.collection.delete_one({"userID": userID})
        return make_response(jsonify({"message": "User deleted successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    

# Endpoint per ottenere un utente passando il nome utente nel body della richiesta
@app.route('/users/<userID>', methods=['GET'])
def get_user_by_id(userID):
    try:
        user = db_user.collection.find_one({'userID': userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        user_data = {
            'userID': user["userID"],
            'balance': user["balance"],
            'collection': user["collection"],
            'transactions': user["transactions"]
        }
        return make_response(jsonify(user_data), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# endpoint to increase the balance of a user
@app.route('/increase_balance', methods=['POST'])
def increase_balance():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    data = request.json
    amount = data.get("amount")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"userID": userID}, {"$inc": {"balance": amount}})
        return make_response(jsonify({"message": "Balance updated successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    
# endpoint to decrease the balance of a user
# must be usable only by roll and after an auction win
@app.route('/decrease_balance', methods=['POST'])
def decrease_balance():  
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    data = request.json
    amount = data.get("amount")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        if user["balance"] < amount:
            return make_response(jsonify({"error": "Insufficient funds"}), 400)
        db_user.collection.update_one({"userID": userID}, {"$inc": {"balance": -amount}})
        return make_response(jsonify({"message": "Balance updated successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# endpoint per fare i refund di una bid
@app.route('/refund', methods=['POST'])
def refund():
    data = request.json
    username = data.get("username")
    amount = data.get("amount")
    try:
        user = db_user.collection.find_one({"username": username})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"username": username}, {"$inc": {"balance": amount}})
        transaction = {
            "amount": amount,
            "type": "refund",
            "timestamp": datetime.now()
        }
        db_user.collection.update_one({"username": username}, {"$push": {"transactions": transaction}})
        return make_response(jsonify({"message": "Refund successful"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint per aggiungere un gatcha alla collezione di un utente
# TODO: deve essere usabile solo dall'endpoint gatcha/roll e alla fine di un asta
@app.route('/add_gatcha', methods=['POST'])
def add_gatcha():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    data = request.json
    gatcha = data.get("gatcha_ID")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one({"userID": userID}, {"$push": {"collection": gatcha}})
        return make_response(jsonify({"message": "Gatcha added successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    
# Endpoint per eliminare un gatcha dalla collezione di un utente
@app.route('/remove_gatcha', methods=['POST'])
def remove_gatcha():
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": "Error decoding token"}), 401)
    data = request.json
    gatcha = data.get("gatcha_ID")
    try:
        user = db_user.collection.find_one({"userID": userID})
        if user is None:
            return make_response(jsonify({"error": "User not found"}), 404)
        db_user.collection.update_one(
            {"userID": userID},
            {"$pull": {"collection": gatcha}},
            {"multi": False}  # This ensures only one instance is removed
        )
        return make_response(jsonify({"message": "Gatcha removed successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint per verificare la connessione al database
@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        # Esegui un ping al database per verificare la connessione
        client_user.admin.command('ping')
        return make_response(jsonify({"message": "Connection to db-gatcha is successful!"}), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Failed to connect to db-gatcha"}), 500)


# TODO: usare nome RESTful tipo /users/
# Endpoint per recuperare tutti i log (da un database gatcha)
@app.route('/getAll', methods=['GET'])
def get_all_logs():
    try:
        res = []
        all = list(db_user.collection.find({}))
        for element in all:
            res.append({
                'userID': element["userID"],
                'balance': element["balance"],
                'collection': element["collection"],
                'transactions': element["transactions"]})
        return make_response(jsonify(res), 200)
    except Exception as e:
        print("DEBUG: Error fetching logs:", str(e))
        return make_response(str(e), 500)
