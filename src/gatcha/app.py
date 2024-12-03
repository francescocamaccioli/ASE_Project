import datetime
import os
import random
from flask import Flask, request, make_response, jsonify
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import bson.json_util as json_util
import bson
import uuid

import requests
from auth_utils import role_required, get_userID_from_jwt


# for handling image uploads to MinIO
from werkzeug.utils import secure_filename
from minio import Minio
from minio.error import S3Error

# for better error messages
from rich.traceback import install
install(show_locals=True)

GATEWAY_URL = os.getenv("GATEWAY_URL")

# region initializing vars ----------------------------------------

ROLL_PRICE = 10

RARITY_PROBABILITIES = {
    'comune': 0.5,       # 50%
    'raro': 0.3,         # 30%
    'epico': 0.15,       # 15%
    'leggendario': 0.05  # 5%
}

GATCHA_DATABASE_URL = os.getenv('GATCHA_DATABASE_URL')

# URLS dei microservizi
USER_URL = os.getenv('USER_URL')
MARKET_URL = os.getenv('MARKET_URL')
MINIO_STORAGE_URL = os.getenv('MINIO_STORAGE_URL')

# MinIO/S3 settings
MINIO_STORAGE_ACCESS_KEY = os.getenv("MINIO_STORAGE_ACCESS_KEY")
MINIO_STORAGE_SECRET_KEY = os.getenv("MINIO_STORAGE_SECRET_KEY")
MINIO_STORAGE_BUCKET_NAME = os.getenv("MINIO_STORAGE_BUCKET_NAME")

def validate_env_vars(**vars):
    for name, value in vars.items():
        if not value or not isinstance(value, str):
            raise ValueError(f"Environment variable {name} with value {value} is not set or is not a valid string.")

# Validate required environment variables
validate_env_vars(
    USER_URL=USER_URL,
    MARKET_URL=MARKET_URL,
    MINIO_STORAGE_URL=MINIO_STORAGE_URL,
    MINIO_STORAGE_ACCESS_KEY=MINIO_STORAGE_ACCESS_KEY,
    MINIO_STORAGE_SECRET_KEY=MINIO_STORAGE_SECRET_KEY,
    MINIO_STORAGE_BUCKET_NAME=MINIO_STORAGE_BUCKET_NAME,
    GATCHA_DATABASE_URL=GATCHA_DATABASE_URL
)
# endregion initializing vars ----------------------------------------





# region configuring MinIO ----------------------------------------

# Configure S3 client
minio_client = Minio(MINIO_STORAGE_URL,
    access_key=MINIO_STORAGE_ACCESS_KEY,
    secret_key=MINIO_STORAGE_SECRET_KEY,
    secure=False # se mettiamo True, aggiunge "https://" all'inizio dell'URL. Se metti False, aggiunge "http://"
)

def create_bucket(bucket_name):
    
    read_only_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                "Resource": f"arn:aws:s3:::{bucket_name}",
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
            },
        ],
    }
    
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
        policy_str = json_util.dumps(read_only_policy)  # Convert dictionary to JSON string
        minio_client.set_bucket_policy(bucket_name, policy_str)
        print("Bucket policy set to public")
    else:
        print("Bucket", bucket_name, "already exists")

try:
    create_bucket(MINIO_STORAGE_BUCKET_NAME)
except S3Error as e:
    print("Error while creating the bucker", e)
# endregion configuring MinIO  ----------------------------------------




# Connessione ai database dei microservizi (modificato per usare i container MongoDB tramite nome servizio)
DATABASE_NAME = 'gatcha_db'
GATCHA_COLLECTION_NAME = 'gatchas'

mongo_client = MongoClient(GATCHA_DATABASE_URL, 27017, maxPoolSize=50)
db = mongo_client[DATABASE_NAME]




app = Flask(__name__, instance_relative_config=True)




# region utility functions ----------------------------------------

def weighted_random_choice(rarities):
    # Selects a rarity based on the predefined probabilities.
    rarity_list = list(rarities.keys())
    probability_list = list(rarities.values())
    return random.choices(rarity_list, probability_list, k=1)[0]


# endregion utility functions ----------------------------------------




# Endpoint per aggiungere dati nel database gacha_db
@app.route('/gatchas', methods=['POST'])
@role_required('adminUser')
def add_gatcha_data():
    """
    Admins can use this endpoint to add a new gatcha to the database.

    Request format. The request should be a multipart request that includes two parts:
    - 'file': The image file to upload.
    - 'json': The JSON payload containing other data.
    
    This endpoint satisfies this user story:
    AS AN administrator I WANT TO modify the gacha collection SO THAT I I can add/remove gachas
    """
    
    if 'file' not in request.files or 'json' not in request.form:
        return make_response(json_util.dumps({"error": "Both image file and JSON payload are required, as a multipart request."}), 400)

    file = request.files['file']

    if file.filename == '':
        return make_response(json_util.dumps({"error": "No image file uploaded"}), 400)
    
    gatcha_uuid = uuid.uuid4().hex

    filename = secure_filename(file.filename)
    filename = f"{gatcha_uuid}_{filename}" # create a unique filename
    destination_file_path = f"images/{filename}"

    # Upload the file to MinIO bucket and get the image_url
    try:
        # Save the file to a temporary location
        temp_file_path = os.path.join('/tmp', filename)
        file.save(temp_file_path)

        # Upload the file to MinIO
        minio_client.fput_object(
            bucket_name=MINIO_STORAGE_BUCKET_NAME, 
            object_name=destination_file_path, 
            file_path=temp_file_path,
            content_type=file.content_type
        )
        print(
            f"File '{file.filename}' successfully uploaded as '{destination_file_path}' to bucket '{MINIO_STORAGE_BUCKET_NAME}'"
        )
        image_url = f"/storage/{MINIO_STORAGE_BUCKET_NAME}/images/{filename}"
    except Exception as e:
        app.logger.error(f"Failed to upload image: {str(e)}")
        return make_response(json_util.dumps({"error": "Failed to upload image"}), 500)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # take the JSON from the request, and add the image URL we just defined to it
    try:
        data = json_util.loads(request.form.get('json'))
    except Exception as e:
        return make_response(json_util.dumps({"error": "Invalid JSON format provided"}), 400)

    data['image'] = image_url
    data["_id"] = gatcha_uuid
    data["NTot"] = 0

    # insert the data into the database
    try:
        db[GATCHA_COLLECTION_NAME].insert_one(data)
        
        response = make_response(json_util.dumps({"message": "Data with image added to gatcha_db", "data": data}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(json_util.dumps({"error": f"Database insert failed: {str(e)}"}), 500)


@role_required('adminUser')
@app.route('/gatchas/<gatcha_id>', methods=['DELETE'])
def delete_gatcha(gatcha_id):
    """
    Admins can use this endpoint to delete a gatcha from the database.

    Request format. The gatcha ID should be provided in the URL path.
    
    This endpoint satisfies this user story:
    AS AN administrator I WANT TO modify the gacha collection SO THAT I can add/remove gachas
    """
    try:
        if not gatcha_id:
            return make_response(json_util.dumps({"error": "Gatcha ID is required"}), 400)

        # Find the gatcha in the database
        gatcha = db[GATCHA_COLLECTION_NAME].find_one({'_id': gatcha_id})

        if not gatcha:
            return make_response(json_util.dumps({"error": "Gatcha not found"}), 404)

        # Delete the image from the MinIO bucket
        if 'image' in gatcha:
            image_path = gatcha['image'].replace(f"/storage/{MINIO_STORAGE_BUCKET_NAME}/", "")
            try:
                minio_client.remove_object(MINIO_STORAGE_BUCKET_NAME, image_path)
            except S3Error as e:
                return make_response(json_util.dumps({"error": f"Failed to delete image from MinIO: {str(e)}"}), 500)

        # Delete the gatcha from the database
        result = db[GATCHA_COLLECTION_NAME].delete_one({'_id': gatcha_id})

        if result.deleted_count == 0:
            return make_response(json_util.dumps({"error": "Gatcha not found"}), 404)

        return make_response(json_util.dumps({"message": "Gatcha deleted successfully"}), 200)
    except Exception as e:
        return make_response(json_util.dumps({"error": f"Failed to delete gatcha: {str(e)}"}), 500)




# Endpoint per rollare un gatcha
@app.route('/roll', methods=['GET'])
@role_required('normalUser')
def roll_gatcha():
    try:
        try:
            userID = get_userID_from_jwt()
        except Exception as e:
            return make_response(json_util.dumps({"error": str(e)}), 401)
        
        # Estrai la rarità in base alle probabilità definite
        selected_rarity = weighted_random_choice(RARITY_PROBABILITIES)
        
        # Query al database per ottenere un gatcha della rarità selezionata
        gachas = list(db[GATCHA_COLLECTION_NAME].find({"rarity": selected_rarity}))

        if not gachas:
            return make_response(f"No gatcha found for rarity {selected_rarity}\n", 404)
        # Estrai un gatcha randomico dalla lista dei personaggi della rarità selezionata
        gatcha = random.choice(gachas) if gachas else None
        
        # Gestisci l'eventualità che non ci sia un gatcha di quella rarità
        if not gatcha:
            return make_response(f"No gatcha found for rarity {selected_rarity}\n", 404)
        
        # Increment NTot for the selected gatcha
        db[GATCHA_COLLECTION_NAME].update_one(
            {'_id': gatcha['_id']},  # Trova il gatcha tramite il suo ID
            {'$inc': {'NTot': 1}}       # Incrementa il campo NTot di 1
        )
        
        jwt_token = request.headers.get('Authorization')
        headers = {'Authorization': jwt_token}
        
        response = requests.post(GATEWAY_URL + "/user/decrease_balance", json={"userID": userID, "amount": ROLL_PRICE}, headers=headers)
        
        if response.status_code != 200:
            return make_response(jsonify({"error": "Failed to decrease balance"}, response.text), response.status_code)
        
        response = requests.post(GATEWAY_URL + "/user/add_gatcha", json={"userID": userID, "gatcha_ID": gatcha['_id']}, headers=headers)
        
        if response.status_code != 200:
            return make_response(jsonify({"error": "Failed to add gatcha", "details": response.text}), response.status_code)
        
        response = make_response(json_util.dumps({"message": "Gatcha rolled successfully", "gatcha": gatcha}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(str(e), 500)
    


@app.route('/gatchas', methods=['GET'])
@role_required('adminUser', 'normalUser')
def get_all_gatcha():
    """
    Endpoint to get all the existing gatcha characters.
    
    This endpoint satisfies the following user stories:
    - AS A player I WANT TO  see the system gacha collection SO THAT I know what I miss of my collection
    - AS AN administrator I WANT TO check all the gacha collection SO THAT I can check all the collection
    """
    try:
        all_gatcha = list(db[GATCHA_COLLECTION_NAME].find({}))
        response = make_response(json_util.dumps(all_gatcha), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(str(e), 500)


@app.route('/gatchas/<gatcha_id>', methods=['GET'])
@role_required('adminUser', 'normalUser')
def get_gatcha(gatcha_id):
    """
    Endpoint to get a specific gatcha character by ID.
    
    This endpoint satisfies the following user stories:
    - AS A player I WANT TO see the info of a system gacha SO THAT I can see the info of a gacha I miss
    - AS AN administrator I WANT TO check a specific gacha SO THAT I can check the status of a gacha
    """
    try:
        gatcha = db[GATCHA_COLLECTION_NAME].find_one({'_id': gatcha_id})
        if not gatcha:
            return make_response(json_util.dumps({"error": "Gatcha not found"}), 404)
        
        response = make_response(json_util.dumps(gatcha), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(str(e), 500)



@app.route('/gatchas/<gatcha_id>', methods=['PUT'])
@role_required("adminUser")
def update_gatcha(gatcha_id):
    """
    Endpoint to update the information of a specific gatcha character by ID.

    Request format. The request should be a JSON payload containing the fields to update.
    There is no constraint on the fields that can be updated: an admin can add and or overwrite any field, except for the _id field.
    
    This endpoint satisfies the following user stories:
    AS AN administrator I WANT TO modify the gacha collection SO THAT I can update gacha information
    """
    try:
        if not gatcha_id:
            return make_response(json_util.dumps({"error": "Gatcha ID is required"}), 400)

        # Parse the JSON payload from the request
        data = request.get_json()
        if not data:
            return make_response(json_util.dumps({"error": "Invalid JSON format provided"}), 400)
        
        if '_id' in data:
            return make_response(json_util.dumps({"error": "You cannot update the _id field"}), 400)

        # Find the gatcha character in the database
        gatcha = db[GATCHA_COLLECTION_NAME].find_one({'_id': gatcha_id})
        if not gatcha:
            return make_response(json_util.dumps({"error": "Gatcha not found"}), 404)

        # Update the gatcha character in the database
        result = db[GATCHA_COLLECTION_NAME].update_one({'_id': gatcha_id}, {'$set': data})

        if result.matched_count == 0:
            return make_response(json_util.dumps({"error": "Gatcha not found"}), 404)

        updated_gatcha = db[GATCHA_COLLECTION_NAME].find_one({'_id': gatcha_id})
        response = make_response(json_util.dumps({"message": "Gatcha updated successfully", "data": updated_gatcha}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        return make_response(json_util.dumps({"error": f"Failed to update gatcha: {str(e)}"}), 500)