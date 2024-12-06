from unittest.mock import patch
from flask import request
from functools import wraps
import logging


"""
MOCKING HTTP REQUESTS

FUNZIONAMENTO:
- Vai all'interno delle funzioni handle_get_request e handle_post_request
- Definisci le risposte di default alle richieste GET e POST che vuoi simulare
- Chiamando start_mocking_http_requests(), ogni richiesta HTTP verrà intercettata, e verrà fornita una risposta in base a quanto definito sotto, e non verrà effettuata una vera richiesta HTTP
"""



logger = logging.getLogger(__name__)


# INSERIRE QUI LE RISPOSTE DI DEFAULT PER LE RICHIESTE
# questa funzione verrà chiamata al posto di requests.get(), requests.post(), ecc., ritornando la risposta definita qui
def mock_request(method, url, *args, **kwargs):
    logger.info(f"Intercepted {method} request to URL: {url}")
    
    if url.endswith("/remove_gatcha"): # Esempio: se la richiesta è a /init-user
        return MockResponse({"message": "gatcha removed successfully"}, 200) # alla richiesta verrà risposto con questo JSON e codice di stato 201
    
    if url.endswith("/refund"):
        return MockResponse({"message": "User refunded successfully"}, 200)
    
    if url.endswith("/add_gatcha"):
        return MockResponse({"message": "gatcha added successfully"}, 200)
    
    if url.endswith("/increase_balance"):
        return MockResponse({"message": "balance increased successfully"}, 200)
    
    if url.endswith("/decrease_balance"):
        return MockResponse({"message": "balance decreased successfully"}, 200)
    
    # According to the method, call the appropriate function to handle the request
    if method == 'POST':
        json_body = kwargs.get('json')
        logger.info(f"Handling POST request to URL: {url} with body: {json_body}")
        logger.warning("Returning 404 Not Found for POST request")
        return MockResponse({"error": "Not Found"}, 404)
    
    logger.warning("Returning 404 Not Found for " + method + " request " + url)
    return MockResponse({"error": "Not Found"}, 404)







def start_mocking_http_requests():
    """
    Call this function to start mocking HTTP requests:
    every requests.get, requests.post, etc. will be intercepted and handled by the functions below.
    """
    
    logger.info("Starting to mock HTTP requests using the " + start_mocking_http_requests.__name__ + " function")
    
    methods_to_patch = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
    patchers = [patch(f'requests.{method}', lambda url, **kwargs: mock_request(method.upper(), url, **kwargs)) for method in methods_to_patch]
    
    for patcher in patchers:
        patcher.start()






def fake_get_userID_from_jwt():
    """
    A fake implementation of the get_userID_from_jwt function that returns a predefined user ID.
    """
    header = request.headers.get('Authorization')
    if header.startswith("Bearer "):
        return header.split(" ")[1]



def no_op_decorator(*required_roles):
    """
    A no-op decorator that does nothing, used to override real decorators in unit tests.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator




class MockResponse:
    """
    A mock response class to simulate the response object returned by the requests library.
    """
    def __init__(self, json_data=None, status_code=200):
        self.json_data = json_data or {}
        self.status_code = status_code

    def json(self):
        return self.json_data

    def status_code(self):
        return self.status_code