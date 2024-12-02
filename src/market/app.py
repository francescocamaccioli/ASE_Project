from datetime import datetime, time, timedelta
import os
import threading
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
import bson.json_util as json_util
from pymongo.errors import ServerSelectionTimeoutError
import requests
from auth_utils import role_required, get_userID_from_jwt


USER_URL = os.getenv('USER_URL')

client_market = MongoClient("db-market", 27017, maxPoolSize=50)
db_market = client_market["db_market"]
Bids = db_market["Bids"]
Auctions = db_market["Auctions"]

app = Flask(__name__)

@app.route('/add-auction', methods=['POST'])
@role_required('normalUser')
def add_auction():
    data = request.json
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 401)
    
    #TODO: check if gatcha exists in user collection
    #TODO: erase gatcha from user collection
    
    auction = {
        "Auction_ID": Auctions.count_documents({}) + 1, # TODO: maybe add hash here (?)
        "Gatcha_ID": data.get("GatchaID"),
        "Auctioner_ID": userID,
        "Winner_ID": "",
        "starting_price": data.get("starting_price"),
        "current_price": data.get("starting_price"), # current highest bid value, to be refounded if another higher bid is placed
        "creation_time": datetime.now(),
        "end_time": datetime.now() + timedelta(minutes=10)
    }
    try:

        jwt_token = request.headers.get('Authorization')
        headers = {'Authorization': jwt_token}
        # Erase from user collection the gatcha that is being auctioned
        response = requests.post(
            USER_URL + "/remove_gatcha",
            json={"gatcha_ID": auction["Gatcha_ID"]},headers=headers
        )
        if response.status_code != 200:
            return make_response(jsonify({"error": "Failed to remove gatcha from user"}), 500)

        Auctions.insert_one(auction)


        # Start a thread to delete the auction after the specified end_time
        delay_seconds = (auction["end_time"] - auction["creation_time"].total_seconds())
        thread = threading.Thread(target=delete_auction_after_delay, args=(auction["Auction_ID"], delay_seconds,auction["Gatcha_ID"]))
        thread.daemon = True  # Ensures the thread ends if the main app stops
        thread.start()


        return make_response(jsonify({"message": "Auction added successfully"}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/delete-auction', methods=['DELETE'])
@role_required('adminUser')
def delete_auction():
    data = request.json
    auction_id = data.get("Auction_ID")
    if not auction_id:
        return make_response(jsonify({"error": "Auction_ID is required"}), 400)
    try:
        auction = Auctions.find_one({"Auction_ID": auction_id}) ## correzione di auction_id id
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        
        # if the auction has a winner, his bid needs to be refounded
        if auction["Winner_ID"]:
            previous_winner = auction["Winner_ID"]
            previous_bid_amount = auction["current_price"]
            response = requests.post(
                USER_URL + "/refund",
                json={"username": previous_winner, "amount": previous_bid_amount}
            )
            if response.status_code != 200:
                return make_response(jsonify({"error": "Failed to refund previous winner"}), 500)
        
        result = Auctions.delete_one({"Auction_ID": auction_id})
        if result.deleted_count == 1:
            return make_response(jsonify({"message": "Auction deleted successfully"}), 200)
        else:
            return make_response(jsonify({"error": "Auction not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)
    

#   Thread function to delete an auction after a delay.
def delete_auction_after_delay(auction_id, delay_seconds,gatcha_id):
    
    time.sleep(delay_seconds)
    try:
        auction = Auctions.find_one({"Auction_ID": auction_id}) ## correzione di auction_id id
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        
        if auction["Winner_ID"]:
            winner = auction["Winner_ID"]
            response = requests.post(
                USER_URL + "/add_gatcha",
                json={"username": winner, "gatcha_ID": gatcha_id}
            )
        if response.status_code != 200:
                return make_response(jsonify({"error": "Failed to add gatcha to user"}), 500)
        
        result = Auctions.delete_one({"Auction_ID": auction_id})
        if result.deleted_count == 1:
            return make_response(jsonify({"message": "Auction ended successfully"}), 200)
        else:
            return make_response(jsonify({"error": "Auction not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route('/bid', methods=['POST'])
def bid():
    data = request.json
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 401)
    bid = {
        "Bid_ID": Bids.count_documents({}) + 1,
        "Auction_ID": data.get("Auction_ID"),
        "User_ID": userID,
        "amount": data.get("amount"),
        "timestamp": datetime.now()
    }
    try:
        auction = Auctions.find_one({"Auction_ID": bid["Auction_ID"]})
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        
        if bid["amount"] <= auction["current_price"]:
            return make_response(jsonify({"error": "Bid amount must be higher than current price"}), 400)
        
        # if the auction has a winner, his bid needs to be refounded
        if auction["Winner_ID"]:
            previous_winner = auction["Winner_ID"]
            previous_bid_amount = auction["current_price"]
            response = requests.post(
                USER_URL + "/refund",
                json={"username": previous_winner, "amount": previous_bid_amount}
            )
            if response.status_code != 200:
                return make_response(jsonify({"error": "Failed to refund previous winner"}), 500)
        
        Auctions.update_one(
            {"Auction_ID": bid["Auction_ID"]},
            {"$set": {"current_price": bid["amount"], "Winner_ID": userID}, "$push": {"bids": bid}}
        )
        return make_response(jsonify({"message": "Bid placed successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/auction', methods=['GET'])
def get_auction():
    data = request.json
    auction_id = data.get("Auction_ID")
    if not auction_id:
        return make_response(jsonify({"error": "AuctionID is required"}), 400)
    try:
        auction = Auctions.find_one({"Auction_ID": auction_id})
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        return make_response(json_util.dumps(auction), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

# Endpoint per ottenere tutte le aste attive
@app.route('/auctions', methods=['GET'])
def get_all_auctions():
    try:
        auctions = list(Auctions.find({}))
        return make_response(json_util.dumps(auctions), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Could not connect to MongoDB server."}), 500)

 # Endpoint per verificare la connessione al database
@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        # Esegui un ping al database per verificare la connessione
        client_market.admin.command('ping')
        return make_response(jsonify({"message": "Connection to db-gatcha is successful!"}), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Failed to connect to db-gatcha"}), 500)

