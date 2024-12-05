from unittest.mock import patch
import requests

def mock_requests():
    """
    Mock the requests library to return predefined responses for specific URLs and methods.
    """
    def mock_request(method, url, *args, **kwargs):
        """
        Handle different HTTP methods and URLs to return appropriate mock responses.
        """
        if method == 'GET':
            return handle_get_request(url)
        elif method == 'POST':
            return handle_post_request(url, kwargs.get('json'))
        return MockResponse({"error": "Not Found"}, 404)

    def handle_get_request(url):
        """
        Handle GET requests and return mock responses based on the URL.
        """
        if url == "http://service1/api/resource":
            return MockResponse({"data": "response from service 1"}, 200)
        elif url == "http://service2/api/resource":
            return MockResponse({"data": "response from service 2"}, 200)
        return MockResponse({"error": "Not Found"}, 404)

    def handle_post_request(url, json_body):
        """
        Handle POST requests and return mock responses based on the URL and request body.
        """
        if url == "http://service1/api/resource":
            if json_body == {"key": "value"}:
                return MockResponse({"data": "response from service 1 with correct body"}, 200)
            else:
                return MockResponse({"error": "Incorrect body"}, 400)
        elif url == "http://service2/api/resource":
            if json_body == {"key": "value"}:
                return MockResponse({"data": "response from service 2 with correct body"}, 200)
            else:
                return MockResponse({"error": "Incorrect body"}, 400)
        return MockResponse({"error": "Not Found"}, 404)

    # Patch the 'requests.request' method with our mock_request function
    patcher = patch('requests.request', mock_request)
    patcher.start()

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

def no_op_decorator(f):
    """
    A no-op decorator that does nothing, used to override real decorators in unit tests.
    """
    def wrapped(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapped