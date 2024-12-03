from flask import request, jsonify
from functools import wraps
from os import getenv
import requests

# SHARED FILE
# This file contains utility functions for decentralized authentication and authorization
# to be used inside each microservice.

# ATTENZIONE: OGNI VOLTA CHE SI MODIFICA, LA NUOVA VERSIONE VA COPIATA IN TUTTI I MICROSERVIZI
# per farlo, usare il file /shared/sync.py

JWT_SECRET = getenv("JWT_SECRET")
ADMIN_GATEWAY_URL = getenv("ADMIN_GATEWAY_URL")

if not JWT_SECRET or JWT_SECRET.strip() == "":
    raise ValueError("JWT_SECRET environment variable is not set or is empty")

def introspect_token(token):
    """Introspect the token using the /auth/introspect endpoint."""
    response = requests.post(f"{ADMIN_GATEWAY_URL}/auth/introspect", data={"token": token})
    if response.status_code == 200:
        return response.json(), None
    return None, response.json().get("error", "Unknown error")

def role_required(*required_roles):
    """Decorator to check if the user has the required roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(" ")[1]
            claims, error = introspect_token(token)
            if error:
                return jsonify({"error": error}), 401
            
            user_role = claims.get("role", [])
            if not any(role in required_roles for role in user_role):
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
    claims, error = introspect_token(token)
    if error:
        return None, error
    
    return claims.get("user_id"), None