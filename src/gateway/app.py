import os
import logging
from typing import Optional, Dict, Any
import requests
from flask import Flask, request, jsonify, Response
from requests.exceptions import ConnectionError, HTTPError, RequestException
from werkzeug.exceptions import BadRequest, MethodNotAllowed

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs from environment variables with default values
SERVICE_URLS = {
    'user': os.getenv('USER_URL'),
    'gatcha': os.getenv('GATCHA_URL'),
    'market': os.getenv('MARKET_URL'),
    'dbm': os.getenv('DBM_URL'),
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
    base_url = SERVICE_URLS.get(service_name)
    if not base_url:
        logger.warning(f"Unknown service: {service_name}")
        return jsonify({'error': 'Service not found'}), 404

    # Construct the target URL
    target_url = f"{base_url}/{subpath}"
    logger.info(f"Forwarding {request.method} request to {target_url}")

    try:
        # Prepare the headers, excluding host to avoid conflicts
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        # Forward the request based on its method
        response = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10  # you can adjust the timeout as needed
        )

        # Prepare the response to return to the client
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

# END OF ROUTES ----------------------------------------------------------------

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))