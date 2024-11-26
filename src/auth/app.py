import os
from flask import Flask, request, make_response, jsonify
import requests
from pymongo import MongoClient
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import uuid

import secrets
import jwt

# for better error messages
from rich.traceback import install
install(show_locals=True)


TOKEN_EXPIRATION_MINUTES = 30

AUTH_DB_URL = os.getenv("AUTH_DB_URL")
AUTH_DB_NAME = os.getenv("AUTH_DB_NAME")
JWT_SECRET = os.getenv("JWT_SECRET")


app = Flask(__name__)

mongo_client = MongoClient(AUTH_DB_URL)
auth_db= mongo_client[AUTH_DB_NAME]




#TODO: register


@app.route('/oauth/token', methods=['POST'])
def token_endpoint():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Validate credentials ( TODO: replace with actual user database lookup)
    if username != "testuser" or password != "password123":
        return jsonify({"error": "Invalid credentials"}), 400

    # Generate tokens
    access_token = jwt.encode(
        {
            "sub": username, # JWT Subject: the user's ID
            "role": "normalUser", # TODO: derfinire ruoli, magari tipo normalUser e adminUser
            
            "iat": datetime.datetime.utcnow(), # JWT Issued At
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRATION_MINUTES),
            
            "iss": "https://auth.example.com", # JWT Issuer
            "jti": str(uuid.uuid4()) # JWT ID: univocal identifier for the token
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    
    id_token = jwt.encode(
        {
            "sub": username,
            "email": "testuser@example.com",
            "role": "normalUser", # TODO: derfinire ruoli, magari tipo normalUser e adminUser
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({
        "access_token": access_token,
        "id_token": id_token,
        "token_type": "Bearer"
    })






"""
Provides user profile data about the authenticated user, based on the claims contained in the access token.
Process:
- Accepts a valid access token (Bearer Token) in the Authorization header.
- Extracts user claims (like username, email) from the token. 
"""
@app.route('/userinfo', methods=['GET'])
def userinfo_endpoint():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized. your request doesn't contain an authorization header."}), 401

    token = auth_header.split(" ")[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify({
            "sub": claims["sub"],  # User ID
            "email": claims.get("email", None)
        })
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401





"""
TODO: ue use this ONLY if we use CENTRALIZED token validation

Validates the access token. This endpoint is called directly by microservices or the API Gateway, IF we use centralized token validation.
Process :
- Accepts a token in the request body.
- Validates the token and returns metadata (e.g., user ID, expiration) or an error.
"""
@app.route('/introspect', methods=['POST'])
def introspect_endpoint():
    token = request.form.get("token")

    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return jsonify({
            "active": True,
            "sub": claims["sub"],
            "exp": claims["exp"]
        })
    except jwt.ExpiredSignatureError:
        return jsonify({"active": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"active": False, "error": "Invalid token"}), 401 
    



@app.route('/', methods=['GET'])
def hello():
    return "Hello, this is the auth service!"