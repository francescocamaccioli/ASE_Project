import requests
import os
from flask import Flask, request, jsonify, make_response
from requests.exceptions import ConnectionError, HTTPError
ALLOWED_USER_OPS = {
    'register': 'POST',
    'login': 'POST',
    'profile': 'GET',
    'add-balance': 'POST',
    'get_user_from_name': 'GET'
}

# URLs for services based on environment variables
GATCHA_URL = os.getenv('GATCHA_URL', 'http://gatcha:5000')
USER_URL = os.getenv('USER_URL', 'http://user:5000')
MARKET_URL = os.getenv('MARKET_URL', 'http://market:5000')
DB_MANAGER_URL = os.getenv('DBM_URL', 'http://db-manager:5000')

app = Flask(__name__)

def service_request(url, data):
    try:
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making request to {url}: {str(e)} with data{str(data)}")  # Log error
        return None

# Endpoint per la registrazione degli utenti
@app.route('/user/register/<username>/<password>')
def register(username, password):
    
    data = {'username': username, 'password': password}

    try:
        # Effettua la richiesta POST al servizio user
        response = requests.post(USER_URL + '/register', json=data)
        
        # Verifica se la risposta è vuota
        if response is None or response.text.strip() == "":
            return jsonify({'error': 'Empty response from User service'}), 500

        # Prova a estrarre il JSON dalla risposta
        try:
            json_response = response.json()  
        except ValueError:
            return jsonify({'error': f'Invalid JSON from User service: {response.text}'}), response.status_code

        # Restituisci il JSON estratto
        if response.status_code == 200:
            return jsonify(json_response), 200
        else:
            return jsonify({'error': json_response.get('error', 'Unknown error')}), response.status_code

    except Exception as e:
        return jsonify({'error': f'Error with the User service: {str(e)}'}), 500



# Endpoint per il login degli utenti
@app.route('/user/get_user_from_name/<username>')
def get_user_from_name(username):
    op = 'get_user_from_name'

    if op not in ALLOWED_USER_OPS:
        return jsonify({'error': 'Operation not allowed'}), 400

    # Prepara i dati da inviare al servizio user
    target_url = f"{USER_URL}/{op}"
    data = {'username': username}

    try:
        json_response = service_request(target_url, data)
        
        # Se non ricevi nulla o un errore
        if json_response is None:
            return jsonify({'error': 'Error with User service'}), 500

        # Verifica la risposta e gestisci eventuali errori
        if 'error' in json_response:
            return jsonify({'error': json_response['error']}), 400

        return jsonify(json_response), 200

    except Exception as e:
        return jsonify({'error': f'Error with the User service: {str(e)}'}), 500



@app.route('/gatcha/<op>')
def gatcha(op):
    if op == 'roll':
        return service_request(f"{GATCHA_URL}/{op}", data=None)
    return jsonify({'error': 'Operation not supported'}), 400


@app.route('/dbm/<op>', methods=['GET', 'POST'])
def dbm_op(op):
    if op == 'checkconnection' and request.method == 'GET':
        return service_request(f"{DB_MANAGER_URL}/checkconnection", data=None)

    if op == 'notify' and request.method == 'POST':
        data = request.json
        return service_request(f"{DB_MANAGER_URL}/notify", data=data)

    return jsonify({'error': 'Operation not supported or invalid method'}), 400

# Endpoint per recuperare tutti gli utenti (da un database user)
@app.route('/getAll')
def get_all_logs():
    try:
        response = requests.get(DB_MANAGER_URL + '/getAll', verify=False)
        response.raise_for_status()
        return response.json()
    except ConnectionError:
        return jsonify({'error': 'DB Manager service is unreachable'}), 500
    except HTTPError as e:
        return jsonify({'error': str(e), 'details': response.content.decode()}), response.status_code
