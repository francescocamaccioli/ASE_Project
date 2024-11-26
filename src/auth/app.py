import os
from flask import Flask, request, make_response, jsonify
import requests
from pymongo import MongoClient
import datetime
from pymongo.errors import ServerSelectionTimeoutError
import uuid
import bson.json_util as mongo_json

import secrets
import jwt

# for better error messages
from rich.traceback import install
install(show_locals=True)


# Constants
TOKEN_EXPIRATION_MINUTES = 30

AUTH_DB_URL = os.getenv("AUTH_DB_URL")
AUTH_DB_NAME = os.getenv("AUTH_DB_NAME")
JWT_SECRET = os.getenv("JWT_SECRET")



# Initializations
app = Flask(__name__)

mongo_client = MongoClient(AUTH_DB_URL)
auth_db= mongo_client[AUTH_DB_NAME]


# adding to the database a test user
# a test user, useful for debugging
test_user = {
    "username": "testuser",
    "password": "password123", # TODO: hash the password, use salt etc
    "email": "testuser@example.com",
    "role": "normalUser" # TODO: derfinire ruoli, magari tipo normalUser e adminUser
}

# Insert the test user into the database
try:
    auth_db.users.insert_one(test_user)
except ServerSelectionTimeoutError:
    print("Could not connect to MongoDB server.")




# region ROUTES DEFINITIONS -------------------------------

#TODO: register route

@app.route('/debug/users', methods=['GET'])
def get_all_users():
    try:
        users = list(auth_db.users.find({}))  # Include all fields
        return make_response(mongo_json.dumps(users), 200)
    except ServerSelectionTimeoutError:
        return jsonify({"error": "Could not connect to MongoDB server."}), 500



@app.route('/oauth/token', methods=['POST'])
def token_endpoint():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Validate credentials (lookup from the database)
    user = auth_db.users.find_one({"username": username})
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 400

    # Generate tokens
    access_token = jwt.encode(
        {
            "sub": username, # JWT Subject: the user's ID
            "role": user["role"],
            
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
            "email": user["email"],
            "role": user["role"],
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

# endregion ROUTES DEFINITIONS
