import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
import bson.json_util as json_util
from pymongo.errors import ServerSelectionTimeoutError
import requests
from auth_utils import role_required, get_userID_from_jwt
import time
from datetime import datetime, timedelta
import logging

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG)

USER_URL = os.getenv('USER_URL')

client_market = MongoClient("db-market", 27017, maxPoolSize=50)
db_market = client_market["db_market"]
Bids = db_market["Bids"]
Auctions = db_market["Auctions"]

scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__, instance_relative_config=True)


UNIT_TEST_MODE = os.getenv('UNIT_TEST_MODE', 'False') == 'True'

if UNIT_TEST_MODE:
    app.logger.info("Running in unit test mode!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    from mocks import start_mocking_http_requests, no_op_decorator, fake_get_userID_from_jwt # mocks.py in the same folder
    start_mocking_http_requests() # after calling this function, the requests are now mocked: they answer with the mocks defined inside app.py
    role_required = no_op_decorator # override the role_required decorator to do nothing
    get_userID_from_jwt = fake_get_userID_from_jwt # override the get_userID_from_jwt function to return a predefined user ID
else :
    app.logger.info("Running in normal mode!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

@app.route('/add-auction', methods=['POST'])
@role_required('normalUser')
def add_auction():
    data = request.json
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 401)
    
    if data.get("starting_price") is None or data.get("Gatcha_ID") is None:
        return make_response(jsonify({"error": "Gatcha_ID and starting_price are required"}), 400)
    
    auction = {
        "Auction_ID": Auctions.count_documents({}) + 1, # TODO: maybe add hash here (?)
        "Gatcha_ID": data.get("Gatcha_ID"),
        "Auctioner_ID": userID,
        "Winner_ID": "",
        "starting_price": data.get("starting_price"),
        "current_price": data.get("starting_price"), # current highest bid value, to be refounded if another higher bid is placed
        "creation_time": datetime.now(),
        "end_time": datetime.now() + timedelta(minutes=1)
    }
    try:
        response = requests.post(
            USER_URL + "/remove_gatcha",
            json={"userID": auction["Auctioner_ID"], "gatcha_ID": auction["Gatcha_ID"]},
            verify=False,
            timeout=10
        )
        if response.status_code != 200:
            return str(response)
        
        Auctions.insert_one(auction)

        logging.debug(f"End time: {auction['end_time']}")
        # adding a job to finalize the auction
        scheduler.add_job(
            finalize_auction,
            trigger=DateTrigger(run_date=auction["end_time"]),
            args=[auction["Auction_ID"], auction["Gatcha_ID"]],
            id=f"finalize_auction_{auction['Auction_ID']}",
            replace_existing=True
        )

        return make_response(jsonify({"message": "Auction added successfully"}), 201)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

@app.route('/delete-auction', methods=['DELETE']) # TODO: manca test
@role_required('adminUser')
def delete_auction():
    data = request.json
    auction_id = data.get("Auction_ID")
    if not auction_id:
        return make_response(jsonify({"error": "Auction_ID is required"}), 400)
    try:
        auction = Auctions.find_one({"Auction_ID": auction_id})
        if not auction:
            return make_response(jsonify({"error": "Auction not found"}), 404)
        
        # if the auction has a winner, his bid needs to be refounded
        if auction["Winner_ID"]:
            previous_winner = auction["Winner_ID"]
            previous_bid_amount = auction["current_price"]
            response = requests.post(
                USER_URL + "/refund",
                json={"userID": previous_winner, "amount": previous_bid_amount},
                verify=False,
                timeout=10
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
    

# Thread function to delete an auction after a delay.
def finalize_auction(auction_id, gatcha_id):
    try:
        logging.debug(f"------------------------------------------ Finalizing auction {auction_id}------------------------------------------")
        auction = Auctions.find_one({"Auction_ID": auction_id})
        if not auction:
            logging.debug(f"Auction {auction_id} not found")
            return

        # Handle the winner or refund
        if auction["Winner_ID"] != "":
            response = requests.post(USER_URL + "/add_gatcha", json={
                "userID": auction["Winner_ID"],
                "gatcha_ID": gatcha_id},
                 verify=False,
                 timeout=10
            )
            
            if response.status_code != 200:
                print(f"Failed to add gatcha to winner for auction {auction_id}")
                return

            response = requests.post(USER_URL + "/increase_balance", json={
                "userID": auction["Auctioner_ID"],
                "amount": auction["current_price"]},
                verify=False,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Failed to increase balance for auctioner {auction_id}")
                return
        else:
            # Refund the gatcha to the auctioner if no bids were placed
            response = requests.post(USER_URL + "/add_gatcha", json={
                "userID": auction["Auctioner_ID"],
                "gatcha_ID": gatcha_id},
                verify=False,
                timeout=10
            )
            if response.status_code != 200:
                print(f"Failed to return gatcha to auctioner for auction {auction_id}")
                return

        # Delete the auction
        result = Auctions.delete_one({"Auction_ID": auction_id})
        if result.deleted_count == 1:
            print(f"Auction {auction_id} finalized.")
        else:
            print(f"Failed to delete auction {auction_id}")
    except Exception as e:
        print(f"Error finalizing auction {auction_id}: {e}")



@app.route('/bid', methods=['POST'])
def bid():
    data = request.json
    try: 
        userID = get_userID_from_jwt()
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 401)
    if data.get("Auction_ID") is None or data.get("amount") is None:
        return make_response(jsonify({"error": "Auction_ID and amount are required"}), 400)
    
    if data.get("amount") <= 0:
        return make_response(jsonify({"error": "Bid amount must be positive"}), 400)
    
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
        
        if auction["Auctioner_ID"] == userID:
            return make_response(jsonify({"error": "You cannot bid on your own auction"}), 400)
        
        if int(bid["amount"]) <= int(auction["current_price"]):
            return make_response(jsonify({"error": "Bid amount must be higher than current price"}), 400)
        
        # if the auction has a winner, his bid needs to be refounded
        if auction["Winner_ID"] != "":
            if auction["Winner_ID"] == userID:
                return make_response(jsonify({"error": "You are already the winner of this auction"}), 400)
            previous_winner = auction["Winner_ID"]
            previous_bid_amount = auction["current_price"]
            response = requests.post(
                USER_URL + "/refund",
                json={"userID": previous_winner, "amount": previous_bid_amount},
                verify=False,
                timeout=10
            )
            if response.status_code != 200:
                return make_response(jsonify({"error": "Failed to refund previous winner"}), 500)
        
        # decrease the bidder's balance
        response = requests.post(
            USER_URL + "/decrease_balance",
            json={"userID": userID, "amount": bid["amount"]},
            verify=False,
            timeout=10
        )
        if response.status_code != 200:
            return make_response(jsonify({"error": "Failed to decrease balance to bidder"}), 500)
        
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
        response = make_response(json_util.dumps(auctions), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
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

