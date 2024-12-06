from unittest.mock import patch
import requests
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


def start_mocking_http_requests():
    """
    call this function to start mocking http requests:
    every requests.get, requests.post, etc. will be intercepted and handled by the functions below
    """
    
    logger.info("Starting to mock HTTP requests using the" + start_mocking_http_requests.__name__ + " function")

    # This function will be called every time a request is made with the requests library
    def mock_request(method, url, *args, **kwargs):
        logger.info(f"Intercepted {method} request to URL: {url}")
        return MockResponse({"message": "User initialized successfully"}, 201)
        
        # according to the method, call the appropriate function to handle the request
        if method == 'POST':
            return handle_post_request(url, kwargs.get('json'))
        return MockResponse({"error": "Not Found"}, 404)


    # LE RISPOSTE ALLE RICHIESTE POST VANNO QUI
    def handle_post_request(url, json_body):
        logger.info(f"Handling POST request to URL: {url} with body: {json_body}")
        
        if url.endswith("/init-user"):
            return MockResponse({"message": "User initialized successfully"}, 201)
        
        if url.endswith("/user/delete_user"):
            return MockResponse({"message": "User deleted successfully"}, 200)
        
        logger.warning("Returning 404 Not Found for POST request")
    
    patcher = patch('requests.request', mock_request)
    patcher.start()






def fake_get_userID_from_jwt():
    """
    A fake implementation of the get_userID_from_jwt function that returns a predefined user ID.
    """
    return "1234567890"




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