import os
import logging
from typing import Optional, Dict, Any, List
import requests
import re
import bleach
from flask import Flask, request, jsonify, Response
from requests.exceptions import ConnectionError, HTTPError, RequestException
from werkzeug.exceptions import BadRequest, MethodNotAllowed

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Regex per validare service_name e subpath
VALID_SERVICE_REGEX = r'^[a-zA-Z0-9._-]+$'
VALID_SUBPATH_REGEX = r'^[a-zA-Z0-9._/-]+$'

# Service URLs from environment variables with default values
SERVICE_URLS = {
    'user': os.getenv('USER_URL'),
    'gatcha': os.getenv('GATCHA_URL'),
    'market': os.getenv('MARKET_URL'),
    'storage': os.getenv('MINIO_STORAGE_URL'),
    'auth': os.getenv('AUTH_URL')
}

# WHITELIST of allowed endpoints
# if an endpoint is commented out or not present in the whitelist, it will be blocked
# remember to add comments to explain why an endpoint is allowed or not allowed
WHITELIST = [
    # minio storage microservice
    {
        'service': 'storage',
        'method': 'GET',
        'path': 'gachabucket/images/<file_name>' # accessibile anche a normalUser
    },
    
    # auth microservice
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'register' # accessibile anche a normalUser
    },
    # {
    #     'service': 'auth',
    #     'method': 'GET',
    #     'path': 'debug/users' # accessibile solo a admin
    # },
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'login'
    },
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'editinfo'
    },
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'delete_user' # posso eliminare solo il mio account
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'userinfo'
    },
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'introspect'
    },
    {
        'service': 'auth',
        'method': 'POST',
        'path': 'tokens/revoke'
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'test'
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'test/normaluseronly'
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'test/adminuseronly'
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'test/bothroles'
    },
    {
        'service': 'auth',
        'method': 'GET',
        'path': 'userid'
    },

    # gatcha microservice
    # {
    #     'service': 'gatcha',
    #     'method': 'POST',
    #     'path': 'gatchas' # solo gli admin possono creare gatchas
    # },
    # {
    #     'service': 'gatcha',
    #     'method': 'DELETE',
    #     'path': 'gatchas/<gatcha_id>' # solo gli admin possono eliminare gatchas
    # },
    {
        'service': 'gatcha',
        'method': 'GET',
        'path': 'roll'
    },
    {
        'service': 'gatcha',
        'method': 'GET',
        'path': 'gatchas'
    },
    {
        'service': 'gatcha',
        'method': 'GET',
        'path': 'gatchas/<gatcha_id>' 
    },
    # {
    #     'service': 'gatcha',
    #     'method': 'PUT',
    #     'path': 'gatchas/<gatcha_id>' # solo gli admin possono modificare gatchas
    # },

    # market microservice
    {
        'service': 'market',
        'method': 'POST',
        'path': 'add-auction'
    },
    # {
    #     'service': 'market',
    #     'method': 'DELETE',
    #     'path': 'delete-auction' # solo gli admin possono eliminare aste
    # },
    {
        'service': 'market',
        'method': 'POST',
        'path': 'bid' # i normalUser possono fare offerte
    },
    {
        'service': 'market',
        'method': 'GET',
        'path': 'auction' # chiunque può vedere le aste
    },
    {
        'service': 'market',
        'method': 'GET',
        'path': 'auctions' # chiunque può vedere le aste
    },
    {
        'service': 'market',
        'method': 'GET',
        'path': 'checkconnection'
    },

    # user microservice
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'init-user' # chiamabile solo dal microservizio auth, gli utenti non possono chiamarlo
    # },
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'delete_user' # chiamabile solo dal microservizio auth, gli utenti non possono chiamarlo
    # },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'users/<userID>' # TODO: questo deve rimanere nella whitelist o va tolto? ogni utente può sapere la balance degli altri?
    },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'balance' # gli utenti possono sapere la loro balance
    },
    {
        'service': 'user',
        'method': 'POST',
        'path': 'increase_balance' # gli utenti possono aumentare la loro balance (simula l'acquisto di ricarica)
    },
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'decrease_balance'
    # },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'transactions' # utente1 può vedere le transazioni di utente1
    },
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'refund'
    # },
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'add_gatcha' # solo gli admin o gli endpoint possono aggiungere gatchas senza fare roll
    # },
    # {
    #     'service': 'user',
    #     'method': 'POST',
    #     'path': 'remove_gatcha' # solo gli admin o gli endpoint possono rimuovere gatchas
    # },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'collection' # user1 può vedere la sua collezione
    },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'collection/<gatcha_ID>' # user1 può vedere un gatcha della sua collezione
    },
    {
        'service': 'user',
        'method': 'GET',
        'path': 'checkconnection'
    },
    # {
    #     'service': 'user',
    #     'method': 'GET',
    #     'path': 'getAll'
    # }
]

def is_request_allowed(service_name: str, method: str, subpath: str) -> bool:
    """
    Checks if the incoming request is allowed based on the whitelist.

    Args:
        service_name (str): The name of the target service.
        method (str): HTTP method of the request.
        subpath (str): The subpath of the request.

    Returns:
        bool: True if the request is allowed, False otherwise.
    """
    # Normalize the subpath by removing leading and trailing slashes
    normalized_subpath = subpath.strip('/')
    
    logger.debug(f"Checking if request to {service_name}/{subpath} with method {method} is allowed")

    for rule in WHITELIST:
        # Check if the service and method match
        if rule['service'] == service_name and method == rule['method']:
            # Normalize the rule path by removing leading and trailing slashes
            normalized_rule_path = rule['path'].strip('/')

            # Split the paths into parts
            rule_path_parts = normalized_rule_path.split('/')
            subpath_parts = normalized_subpath.split('/')

            # Check if the number of parts in the rule path and subpath match
            if len(rule_path_parts) == len(subpath_parts):
                match = True
                for rule_part, subpath_part in zip(rule_path_parts, subpath_parts):
                    # Check if each part matches or is a parameter (e.g., <gatcha_id>)
                    if rule_part != subpath_part and not (rule_part.startswith('<') and rule_part.endswith('>')):
                        match = False
                        break

                if match:
                    return True

    return False

def forward_request(service_name: str, subpath: str) -> Response:
    """
    Forwards the incoming request to the specified service with the given subpath.

    Args:
        service_name (str): The name of the target service.
        subpath (str): The subpath to append to the service URL.

    Returns:
        Response: The response object from the target service.
    """
    
    logger.debug(f"Trying to forward the request to {service_name}/{subpath}")
    
    # Validate the service name
    if not validate_input(service_name, VALID_SERVICE_REGEX):
        logger.warning(f"Invalid service name: {service_name}")
        return jsonify({'error': 'Invalid service name'}), 400

    # Retrieve the base URL of the service
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        logger.warning(f"Unknown service: {service_name}")
        return jsonify({'error': 'Service not found'}), 404

    # Validate the subpath
    if not validate_input(subpath, VALID_SUBPATH_REGEX):
        logger.warning(f"Invalid subpath: {subpath}")
        return jsonify({'error': 'Invalid subpath'}), 400

    # Check if the request is allowed
    if not is_request_allowed(service_name, request.method, subpath):
        logger.warning(f"Request to {service_name}/{subpath} with method {request.method} is not allowed because is not in the whitelist.")
        return jsonify({'error': 'This endpoint was not found in this user gateway. (debug: it is not in the whitelist)'}), 404 # TODO: remove debug message

    # Construct the target URL
    target_url = f"{base_url}/{subpath}"
    logger.info(f"Forwarding {request.method} request to {target_url} without query parameters")

    try:
        # Prepare headers (excluding 'host' to avoid conflicts)
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        # Forward the request without query parameters
        response = requests.request(
            method=request.method,
            url=target_url,
            data=request.get_data(),
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10,
            verify=False
        )

        # Remove unnecessary headers in the response
        excluded_headers = ['content-encoding', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in response.raw.headers.items()
                   if name.lower() not in excluded_headers]

        return Response(response.content, response.status_code, headers)

    except ConnectionError as ce:
        logger.error(f"Connection error while accessing {target_url}: {ce}")
        return jsonify({'error': 'Service unavailable'}), 503
    except HTTPError as he:
        logger.error(f"HTTP error while accessing {target_url}: {he}")
        return jsonify({'error': 'HTTP error with service'}), he.response.status_code if he.response else 500
    except RequestException as re:
        logger.error(f"Request exception while accessing {target_url}: {re}")
        return jsonify({'error': 'Error forwarding request'}), 500
    except Exception as e:
        logger.exception(f"Unexpected error while forwarding to {target_url}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ERROR HANDLERS ---------------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error.description)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ROUTES -----------------------------------------------------------------------
@app.route('/<service>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def gateway_handler(service, subpath):
    """
    General gateway handler to route requests to appropriate services and subpaths.
    Forwards the request without modifying the path, query parameters, or body.
    """
    return forward_request(service, subpath)

@app.route('/', methods=['GET'])
def index():
    """Health check route."""
    return jsonify({"message": "API Gateway is running"}), 200

# INPUT SANITIZATION -----------------------------------------------------------
def sanitize_input(data: str) -> str:
    """
    Sanitizes input string by removing potentially dangerous characters.
    This helps prevent injection attacks.

    Args:
        data (str): Input string to sanitize.

    Returns:
        str: Sanitized string.
    """
    # Sanitize using bleach, only allowing safe HTML tags if needed
    return bleach.clean(data, tags=[], attributes=[], strip=False, protocols=['http', 'https'])

def validate_input(input_value: str, regex: str) -> bool:
    """
    Validates input using a regex pattern.

    Args:
        input_value (str): The input string to validate.
        regex (str): The regex pattern to validate against.

    Returns:
        bool: True if the input matches the regex, False otherwise.
    """
    return re.match(regex, input_value) is not None

def sanitize_query_params(params):
    """
    Sanitize query string parameters to ensure no unsafe characters are present.

    Args:
        params (MultiDict): The query parameters to sanitize.

    Returns:
        dict: The sanitized query parameters.
    """
    sanitized_params = {}
    for key, value in params.items():
        if validate_input(key, VALID_QUERY_PARAM_REGEX) and validate_input(value, VALID_QUERY_PARAM_REGEX):
            sanitized_params[key] = value
        else:
            logger.warning(f"Unsafe query parameter detected: {key}={value}")
            sanitized_params[key] = None  # Or you can exclude it entirely, depending on the use case
    return sanitized_params