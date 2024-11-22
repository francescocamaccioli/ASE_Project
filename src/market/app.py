from datetime import datetime, timedelta
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
import bson.json_util as json_util
from pymongo.errors import ServerSelectionTimeoutError

client_market = MongoClient("db-market", 27017, maxPoolSize=50)
db_market = client_market["db_market"]
Bids = db_market["Bids"]
Auctions = db_market["Auctions"]

app = Flask(__name__)

@app.route('/add-auction', methods=['POST'])
def add_auction():
    data = request.json
    auction = {
        "Auction_ID": Auctions.count_documents({}) + 1, # TODO: maybe add hash here (?)
        "Gatcha_ID": data.get("GatchaID"),
        # TODO: add User_ID here from JWT
        "starting_price": data.get("starting_price"),
        "current_price": data.get("starting_price"),
        "creation_time": datetime.now(),
        "end_time": datetime.now() + timedelta(minutes=10)
    }
    try:
        Auctions.insert_one(auction)
        return make_response(jsonify({"message": "Auction added successfully"}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/delete-auction', methods=['DELETE'])
def delete_auction():
    # TODO: check on token => only admin can delete auctions
    data = request.json
    auction_id = data.get("Auction_ID")
    if not auction_id:
        return make_response(jsonify({"error": "Auction_ID is required"}), 400)
    try:
        result = Auctions.delete_one({"_id": auction_id})
        if result.deleted_count == 1:
            return make_response(jsonify({"message": "Auction deleted successfully"}), 200)
        else:
            return make_response(jsonify({"error": "Auction not found"}), 404)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/bid', methods=['POST'])
def bid():
    data = request.json
    bid = {
        "Bid_ID": Bids.count_documents({}) + 1,
        "Auction_ID": data.get("Auction_ID"),
        "User_ID": data.get("User_ID"),
        "amount": data.get("amount"),
        "timestamp": data.get("timestamp")
    }
    try:
        auction = Auctions.find_one({"_id": bid["Auction_ID"]})
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        
        if bid["amount"] <= auction["current_price"]:
            return make_response(jsonify({"error": "Bid amount must be higher than current price"}), 400)
        
        Auctions.update_one(
            {"_id": bid["Auction_ID"]},
            {"$set": {"current_price": bid["amount"]}, "$push": {"bids": bid}}
        )
        return make_response(jsonify({"message": "Bid placed successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/get-auction', methods=['GET'])
def get_auction():
    data = request.json
    auction_id = data.get("AuctionID")
    if not auction_id:
        return make_response(jsonify({"error": "AuctionID is required"}), 400)
    try:
        auction = Auctions.find_one({"_id": auction_id})
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        return make_response(json_util.dumps(auction), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

 # Endpoint per verificare la connessione al database
@app.route('/checkconnection', methods=['GET'])
def check_connection():
    try:
        # Esegui un ping al database per verificare la connessione
        client_market.admin.command('ping')
        return make_response(jsonify({"message": "Connection to db-gatcha is successful!"}), 200)
    except ServerSelectionTimeoutError:
        return make_response(jsonify({"error": "Failed to connect to db-gatcha"}), 500)

