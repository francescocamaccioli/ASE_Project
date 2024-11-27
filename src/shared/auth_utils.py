import jwt
from flask import request, jsonify
from functools import wraps

# SHARED FILE
# This file contains utility functions for decentralized authentication and authorization
# to be used inside each microservice.

# ATTENZIONE: OGNI VOLTA CHE SI MODIFICA, LA NUOVA VERSIONE VA COPIATA IN TUTTI I MICROSERVIZI
# TODO: trovare un modo migliore


JWT_SECRET = "supersecret" # TODO: decidere qual è la source of truth per il secret



# utility function, used only inside this file
# usage: token_payload, error = decode_token()
def decode_token():
    """Extract and decode the token from the Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, "Missing or invalid authorization header"
    
    token = auth_header.split(" ")[1]  # Get the token part
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"




def role_required(required_role):
    """Decorator to enforce role-based authorization:
    If the JWT you sent doesn't contain the required_role, you won't be authorized to continue.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token_payload, error = decode_token()
            if error:
                return jsonify({'error': error}), 401

            # Check the role in the JWT payload
            user_role = token_payload.get("role", "")
            if user_role != required_role:
                return jsonify({'error': f'Unauthorized: requires role {required_role}'}), 403

            # Call the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator



def get_username_from_jwt():
    """
    Returns the username from the JWT payload (reading the "sub" field).
    This username should be guaranteed to be authenticated by the JWT.
    """
    token_payload, error = decode_token()
    if error:
        raise ValueError(f"Error decoding token: {error}")
    
    # get the username from the JWT, and return it
    username = token_payload.get("sub", "")
    if not username:
        raise ValueError('Username not found in token')
    return username