import os
import re
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import ServerSelectionTimeoutError
import uuid
import bson.json_util as mongo_json
import jwt
from auth_utils import role_required, get_userID_from_jwt
import bcrypt
import os
import requests

# for better error messages
from rich.traceback import install
install(show_locals=True)


# Constants
TOKEN_EXPIRATION_MINUTES = 30

AUTH_DB_URL = os.getenv("AUTH_DB_URL")
AUTH_DB_NAME = os.getenv("AUTH_DB_NAME")
JWT_SECRET = os.getenv("JWT_SECRET")
GATEWAY_URL = os.getenv("GATEWAY_URL")
ADMIN_GATEWAY_URL = os.getenv("ADMIN_GATEWAY_URL")



# Initializations
app = Flask(__name__)

mongo_client = MongoClient(AUTH_DB_URL)
auth_db= mongo_client[AUTH_DB_NAME]


# adding to the database a test admin user
test_admin_user = {
    "username": "adminuser",
    "password": "password123",
    "email": "adminuser@example.com",
    "role": "adminUser"
}

# Insert the test user into the database
try:
    auth_db.users.insert_one(test_admin_user)
except ServerSelectionTimeoutError:
    print("Could not connect to MongoDB server.")


# region ROUTES DEFINITIONS -------------------------------

@app.route('/register', methods=['POST'])
def register_user():
    try:
        payload = request.json  # Get JSON data from the request body
        if payload is None:
            return make_response(jsonify({"error": "No data provided"}), 400)
        
        if 'username' not in payload or 'password' not in payload or 'email' not in payload:
            return make_response(jsonify({"error": "Missing fields"}), 400)
        
        if auth_db.users.find_one({"username": payload['username']}):
            return make_response(jsonify({"error": "User already exists"}), 400)
        
        if not re.match(r"^[a-zA-Z0-9._-]{3,20}$", payload['username']):
            return make_response(jsonify({"error": "Username must be alfanumeric and between 3 and 20 digits"}), 400)
        
        user = {
            "userID": str(uuid.uuid4()),
            "username": payload['username'],
            # non so se va fatto hash(hash(psw)+salt) qui o se l'user deve mandare già la password hashata
            "password": bcrypt.hashpw(payload['password'].encode(), bcrypt.gensalt()),
            "email": payload['email'],
            "role": 'normalUser'
        }
        
        auth_db.users.insert_one(user)

        # commented to allow easier testing
        # Requires at least one uppercase letter.
        # Requires at least one lowercase letter.
        # Requires at least one digit.
        # Requires at least one special character (@, $, !, %, *, ?, &).
        # Requires at least 8 characters long and includes valid characters only.
        
        # if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", payload['password']):
        #     return make_response(jsonify({"error": "Invalid password"}), 400)

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", payload['email']):
            return make_response(jsonify({"error": "Invalid email"}), 400)
        
        user = {
            "username": payload['username'],
            # non so se va fatto hash(hash(psw)+salt) qui o se l'user deve mandare già la password hashata
            "password": bcrypt.hashpw(payload['password'].encode(), bcrypt.gensalt()),
            "email": payload['email'],
            "role": "normalUser"
        }
        
        auth_db.users.insert_one(user)
        # need to insert user also in db-user, with initializated fields
        # non so se ha piu senso fare un endpoint in user che crea un utente con i campi inizializzati o se fare l'accesso al db-user direttamente qui e crearlo
        response = requests.post(ADMIN_GATEWAY_URL+"/user/init-user", json={"userID": user["userID"]})
        if response.status_code != 201:
            return make_response(jsonify({"error": "Could not initialize user, problem with the user microservice"}), 502)
                    

        
        return make_response(jsonify({"message": "User registered successfully"}), 200)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)



# Ritorna tutti gli utenti contenenti nel database
# questa route serve solo per il debug, ovviamente in preoduzione non dovrebbe esistere
@app.route('/debug/users', methods=['GET'])
def get_all_users():
    try:
        users = list(auth_db.users.find({}))  # Include all fields
        return make_response(mongo_json.dumps(users), 200)
    except ServerSelectionTimeoutError:
        return jsonify({"error": "Could not connect to MongoDB server."}), 500



@app.route('/login', methods=['POST'])
def token_endpoint():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Validate credentials (lookup from the database)
        user = auth_db.users.find_one({"username": username})
        if not user or not bcrypt.checkpw(password.encode(), user["password"]):
            return jsonify({"error": "Invalid credentials"}), 400

        # Generate tokens
        access_token = jwt.encode(
            {
                "sub": user["userID"], # JWT Subject: the user's ID
                "role": user["role"],
                
                "iat": datetime.now(), # JWT Issued At
                "exp": datetime.now() + timedelta(minutes=TOKEN_EXPIRATION_MINUTES),
                
                "iss": "https://auth.example.com", # JWT Issuer
                "jti": str(uuid.uuid4()) # JWT ID: univocal identifier for the token
            },
            JWT_SECRET,
            algorithm="HS256"
        )
        
        # TODO: lo ho commentato perché basta access_token. Va bene? Oppure serve per via dello standard?
        # id_token = jwt.encode(
        #     {
        #         "sub": username,
        #         "email": user["email"],
        #         "role": user["role"],
        #         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
        #     },
        #     JWT_SECRET,
        #     algorithm="HS256"
        # )

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer"
        })
        
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)

@app.route('/editinfo', methods=['POST'])
def edit_user_info():
    try:    
        try:
            userID = get_userID_from_jwt()
        except Exception as e:
            return jsonify({"error": str(e)}), 401
        
        data = request.get_json()
        new_username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role')
        
        user = auth_db.users.find_one({"userID": userID})
        if not user:
            return jsonify({"error": "User not found " + userID}), 404
        if new_username:
            user['username'] = new_username
        if password:
            user['password'] = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        if email:
            user['email'] = email
        if role:
            user['role'] = role
        
        auth_db.users.update_one({"userID": userID}, {"$set": user})

        return jsonify({"message": "User info updated successfully"})
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    try:
        try:
            userID = get_userID_from_jwt()
        except Exception as e:
            return jsonify({"error": str(e)}), 401
        
        auth_db.users.delete_one({"userID": userID})
        # invoke the user microservice to delete the user
        response = requests.post(ADMIN_GATEWAY_URL+"/user/delete_user", json={"userID": userID})
        if response.status_code != 200:
            return make_response(jsonify({"error": "Could not delete user, problem with the user microservice "+ response.text}), 502)
        
        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 502)




"""
Provides user profile data about the authenticated user, based on the claims contained in the access token.
Process:
- Accepts a valid access token (Bearer Token) in the Authorization header.
- Extracts user claims (like username - called "sub") from the token. 
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
    


# endregion ROUTES DEFINITIONS



# region TEST ROUTES -------------------------------

# Questi test possono essere esempi utili su come usare auth_utils.py per fare auntenticazione e autorizzazione negli altri microservizi

@app.route('/test', methods=['GET'])
def hello():
    return "Hello, this is the auth service!"


# Requests to this route should succeed
# ONLY if you present a token of a normalUser
@app.route('/test/normaluseronly', methods=['GET'])
@role_required("normalUser")
def normal_user_only():
    return jsonify({"message": "You successfully accessed a normal user-only endpoint."})

# Requests to this route should succeed
# ONLY if you present a token of an adminUser
@app.route('/test/adminuseronly', methods=['GET'])
@role_required("adminUser")
def admin_user_only():
    return jsonify({"message": "You successfully accessed an admin user-only endpoint."})

# endpoint for both normal and admin users
@app.route('/test/bothroles', methods=['GET'])
@role_required('normalUser', 'adminUser')
def both_roles():
    return jsonify({"message": "You successfully accessed an endpoint that requires admin OR user role."})


# When you send a request to this route, you also send you JWT token.
# It extracs the username from the JWT, and echoes it to you.
@app.route('/test/echousername', methods=['GET'])
def echo_username():
    try:
        username = get_username_from_jwt()
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    return jsonify({
        "message": "Your username was successfully extracted from the JWT token you sent with this request",
        "username": username
    })

# endregion TEST ROUTES
