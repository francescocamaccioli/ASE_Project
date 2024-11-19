import os
import logging
from typing import Optional, Dict, Any

import requests
from flask import Flask, request, jsonify
from requests.exceptions import ConnectionError, HTTPError, RequestException
from werkzeug.exceptions import BadRequest, MethodNotAllowed

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs from environment variables with default values
GATCHA_URL = os.getenv('GATCHA_URL', 'http://gatcha:5000')
USER_URL = os.getenv('USER_URL', 'http://user:5000')
MARKET_URL = os.getenv('MARKET_URL', 'http://market:5000')
DB_MANAGER_URL = os.getenv('DBM_URL', 'http://db-manager:5000')

# Allowed operations mapping
ALLOWED_OPERATIONS = {
    'user': {
        'register': 'POST',
        'login': 'POST',
        'profile': 'GET',
        'add-balance': 'POST',
        'get_user_from_name': 'GET',
    },
    'gatcha': {
        'roll': 'GET',
    },
    'dbm': {
        'checkconnection': 'GET',
        'notify': 'POST',
        'getAll': 'GET',
    }
}

SERVICE_URLS = {
    'user': USER_URL,
    'gatcha': GATCHA_URL,
    'dbm': DB_MANAGER_URL,
}






def service_request(service_name: str, operation: str, method: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
    """Helper function to make requests to service endpoints.

    Args:
        service_name (str): The service name ('user', 'gatcha', etc.).
        operation (str): The service operation.
        method (str): HTTP method ('GET', 'POST').
        params (Optional[Dict[str, Any]]): Query parameters.
        data (Optional[Dict[str, Any]]): Data to be sent in the request.

    Returns:
        Any: The JSON response from the service.

    Raises:
        HTTPError: If the HTTP request returned an unsuccessful status code.
        ConnectionError: If there was a connection error.
        RequestException: Other requests exceptions.
    """
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        raise ValueError(f"Unknown service: {service_name}")

    url = f"{base_url}/{operation}"

    try:
        if method.upper() == 'POST':
            response = requests.post(url, json=data)
        else:
            response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except (HTTPError, ConnectionError) as http_err:
        logger.error(f"HTTP error occurred while accessing {url}: {http_err}")
        raise
    except RequestException as req_err:
        logger.error(f"Request error occurred while accessing {url}: {req_err}")
        raise
    except ValueError as val_err:
        logger.error(f"Error decoding JSON from {url}: {val_err}")
        raise





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

@app.route('/<service>/<operation>', methods=['GET', 'POST'])
@app.route('/<service>/<operation>/<path:param>', methods=['GET'])
def gateway_handler(service, operation, param=None):
    """General gateway handler to route requests to appropriate services and operations."""
    # Validate service
    if service not in ALLOWED_OPERATIONS:
        logger.warning(f"Unknown service: {service}")
        return jsonify({'error': 'Service not found'}), 404

    # Validate operation
    allowed_ops = ALLOWED_OPERATIONS[service]
    if operation not in allowed_ops:
        logger.warning(f"Operation '{operation}' not allowed for service '{service}'")
        return jsonify({'error': 'Operation not allowed'}), 400

    # Validate method
    method_allowed = allowed_ops[operation]
    if method_allowed != request.method:
        logger.warning(f"Method '{request.method}' not allowed for operation '{operation}'")
        raise MethodNotAllowed()

    # Prepare parameters and data
    params = {}
    data = None

    if request.method == 'GET':
        if param:
            # If there is a parameter in the URL, include it in the params
            params['param'] = param
        # Include query parameters
        params.update(request.args.to_dict())
    elif request.method == 'POST':
        data = request.get_json()
        if data is None:
            raise BadRequest('Request must be in JSON format')

    try:
        # Call the appropriate service
        json_response = service_request(
            service_name=service,
            operation=operation,
            method=request.method,
            params=params,
            data=data
        )
        return jsonify(json_response), 200
    except HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response else 500
        logger.error(f"HTTPError: {http_err}")
        return jsonify({'error': 'Error with service'}), status_code
    except Exception as e:
        logger.exception(f"Exception during handling {service}/{operation}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500





@app.route('/', methods=['GET'])
def index():
    """Health check route."""
    return jsonify({"message": "API Gateway is running"}), 200



# END OF ROUTES ----------------------------------------------------------------




if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))