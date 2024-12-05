from flask import request, jsonify
from functools import wraps
from os import getenv
import requests
import json
import logging

logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SHARED FILE
# This file contains utility functions for decentralized authentication and authorization
# to be used inside each microservice.

# ATTENZIONE: OGNI VOLTA CHE SI MODIFICA, LA NUOVA VERSIONE VA COPIATA IN TUTTI I MICROSERVIZI
# per farlo, usare il file /shared/sync.py

AUTH_URL = getenv("AUTH_URL")

def introspect_token(token):
    """Introspect the token using the /auth/introspect endpoint."""

    try:
        response = requests.post(f"{AUTH_URL}/introspect", data={"token": token}, timeout=10, verify=False)
        if response.status_code == 200:
            claims = json.loads(response.text)
            logger.debug("Introspected token: " + str(claims))
            return claims
        elif response.status_code == 401:
            logger.warning("The server returned 401 while introspecting the token" + response.text)
            raise ValueError("Invalid token: " + json.loads(response.text).get("error", "Unknown error"))
        else:
            logger.error("The server responded with an unexpected status code " + str(response.status_code) + " while introspecting the token: " + json.loads(response.text).get("error", "Unknown error"))
            raise ValueError("Error while introspecting token: " + response.text)
    except requests.exceptions.Timeout:
        logger.error("Request to introspect token timed out")
        raise ValueError("Request to introspect token timed out")

def role_required(*required_roles):
    """Decorator to check if the user has the required roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(" ")[1]
            try:
                claims = introspect_token(token)
            except Exception as e:
                logger.error("Error while getting the claims from the token: " + str(e))
                return jsonify({"error": str(e)}), 401
            
            try:
                user_role = claims.get("role")
            except Exception as e:
                logger.error("Error while getting the role from the JWT: " + str(e))
                return jsonify({"error": "Invalid token: " + str(e)}), 401
            
            if user_role not in required_roles:
                logger.warning(f"User with role {user_role} tried to access a resource that requires one of the following roles: {required_roles}")
                return jsonify({"error": "Forbidden"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_userID_from_jwt():
    """Extract user ID from JWT token."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, "Missing or invalid authorization header"
    
    token = auth_header.split(" ")[1]
    
    try:
        claims = introspect_token(token)
        userID = claims["sub"] # the user ID is stored in the "sub" field
        if not userID:
            raise ValueError("User ID not found in the token")
        logger.debug(f"Found user ID inside get_userID_from_jwt(): {userID}")
    except Exception as e:
        logger.error("Error while getting the userID. " + str(e))
        return jsonify({"error": "Error while getting the userID. " + e}), 401
    return userID
    