import requests, time

from flask import Flask, request, make_response 
from requests.exceptions import ConnectionError, HTTPError
from pymongo.errors import ServerSelectionTimeoutError

from werkzeug.exceptions import NotFound

ALLOWED_USER_OPS = ['register', 'login', 'admin/register', 'admin/login', 'add-balance', 'profile']
ALLOWED_GATCHA_OPS = ['roll', 'get-gatcha-id', 'get-all-gatcha', 'add-gatcha', 'delete-gatcha']
ALLOWED_MARKET_OPS = ['create-auction', 'bid', 'get-auction', 'add-auction', 'delete-auction']

#CHANGE URLS TO MATCH THE NAMES AND PORTS OF THE SERVICES IN THE DOCKER-COMPOSE FILE
GATCHA_URL = 'http://gatcha:5000'
USER_URL = 'http://user:5000'
MARKET_URL = 'http://market:5000'
DB_MANAGER_URL = 'http://db-manager:5000'


ids = {} #CAREFUL, THIS IS NOT FOR MULTIUSER AND MULTITHREADING, JUST FOR DEMO PURPOSES

app = Flask(__name__, instance_relative_config=True)

def create_app():
    return app

def service_request(url, data=None):
    try:
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except ConnectionError:
        return make_response('Gatcha service is down\n', 500)
    except HTTPError:
        return make_response(response.content, response.status_code)
    

@app.route('/gatcha/<op>')
def gatcha(op):
    if op == 'roll':
        json_response = service_request(GATCHA_URL + '/roll')
        if json_response is None:
            return "Error with the Gatcha service", 500  # Return an error message if the request fails
    
        return json_response

@app.route('/dbm/<op>', methods=['GET', 'POST'])  # Ensure the route listens for both GET and POST requests
def dbm_op(op):
    if op == 'checkconnection' and request.method == 'GET':
        # Send a GET request to DB Manager for checking connection
        json_response = service_request(DB_MANAGER_URL + '/checkconnection')
        if json_response is None:
            return "Error with the DB Manager service", 500  # Return an error message if the request fails
        return json_response

    elif op == 'notify' and request.method == 'POST':
        # Send a POST request to DB Manager for adding a log
        data = request.json  # Assuming data is sent as JSON in the request body
        json_response = service_request(DB_MANAGER_URL + '/notify', data=data)
        if json_response is None:
            return "Error with the DB Manager service", 500  # Return an error message if the request fails
        return json_response

    # Default response if no operation matched
    return "Operation not supported", 400


@app.route('/getAll')# funzione per ottenere tutti i log di tutte le operazioni dal db-manager
def getAll():
    try:
        x = requests.get(DB_MANAGER_URL + '/getAll', verify=False)
        x.raise_for_status()
        return x.json()
    except ConnectionError:
        return make_response('DB Manager service is down\n', 500)
    except HTTPError:
        return make_response(x.content, x.status_code)