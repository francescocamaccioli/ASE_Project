import os
import logging
from typing import Optional, Dict, Any
import requests
import re
import bleach
from flask import Flask, request, jsonify, Response
from requests.exceptions import ConnectionError, HTTPError, RequestException
from werkzeug.exceptions import BadRequest, MethodNotAllowed

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
    'dbm': os.getenv('DBM_URL'),
    'storage': os.getenv('MINIO_STORAGE_URL'),
    'auth': os.getenv('AUTH_URL')
}

# TODO: aggiungere una WHITELIST con gli endpoint che possono essere chiamati da questo gateway (default deny). questo perché questo endpoint è pubblico. dobbiamo evitare che possa chiamare endpoint sensibili riservati agli admin.

def forward_request(service_name: str, subpath: str) -> Response:
    """
    Forwards the incoming request to the specified service with the given subpath.
    
    Args:
        service_name (str): The name of the target service.
        subpath (str): The subpath to append to the service URL.
    
    Returns:
        Response: The response object from the target service.
    """
    
   # Validazione del nome del servizio
    if not validate_input(service_name, VALID_SERVICE_REGEX):
        logger.warning(f"Invalid service name: {service_name}")
        return jsonify({'error': 'Invalid service name'}), 400

    # Recupera l'URL di base del servizio
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        logger.warning(f"Unknown service: {service_name}")
        return jsonify({'error': 'Service not found'}), 404

    # Validazione del subpath
    if not validate_input(subpath, VALID_SUBPATH_REGEX):
        logger.warning(f"Invalid subpath: {subpath}")
        return jsonify({'error': 'Invalid subpath'}), 400

    # Costruisci l'URL target senza i parametri della query string
    target_url = f"{base_url}/{subpath}"
    logger.info(f"Forwarding {request.method} request to {target_url} without query parameters")

    try:
        # Prepara gli header (escludendo 'host' per evitare conflitti)
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        # Inoltra la richiesta senza parametri della query string
        response = requests.request(
            method=request.method,
            url=target_url,  # Usa solo il target URL senza parametri
            data=request.get_data(),
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10  # Timeout personalizzabile
        )

        # Rimuovi header non necessari nella risposta
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

# INPUT SANIFICATION ----------------------------------------------------------------

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