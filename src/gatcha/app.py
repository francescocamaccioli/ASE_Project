import datetime
import os
import random
from flask import Flask, request, make_response
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import bson.json_util as json_util
import uuid


# for handling image uploads to MinIO
from werkzeug.utils import secure_filename
from minio import Minio
from minio.error import S3Error

# for better error messages
from rich.traceback import install
install(show_locals=True)




# region initializing vars ----------------------------------------

RARITY_PROBABILITIES = {
    'comune': 0.5,       # 50%
    'raro': 0.3,         # 30%
    'epico': 0.15,       # 15%
    'leggendario': 0.05  # 5%
}


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
    MINIO_STORAGE_BUCKET_NAME=MINIO_STORAGE_BUCKET_NAME
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
client_gatcha = MongoClient("db-gatcha", 27017, maxPoolSize=50)
db_gatcha= client_gatcha["db_gatcha"]

app = Flask(__name__, instance_relative_config=True)



# region utility functions ----------------------------------------

def weighted_random_choice(rarities):
    # Selects a rarity based on the predefined probabilities.
    rarity_list = list(rarities.keys())
    probability_list = list(rarities.values())
    return random.choices(rarity_list, probability_list, k=1)[0]

# TODO: non usata?
# Funzione generica per ottenere dati da un database specifico
def get_data_from_db(client, db_name, collection_name, query={}):
    db = client[db_name]
    collection = db[collection_name]
    return list(collection.find(query))

# Funzione generica per inserire dati in un database
def insert_data_to_db(client, db_name, collection_name, data):
    db = client[db_name]
    collection = db[collection_name]
    collection.insert_one(data)

# endregion utility functions ----------------------------------------




# Endpoint per aggiungere dati nel database gacha_db
# TODO: aggiungere input validation per controllare che la richiesta sia come ce lo aspettiamo
# TODO: può farla solo admin
# TODO: c'è un test già scritto, spostarlo in integration tests
@app.route('/addgatchaData', methods=['POST'])
def add_gatcha_data():
    """
    Admins can use this endpoint to add a new gatcha character to the database.

    Request format. The request should be a multipart request that includes two parts:
    - 'file': The image file to upload.
    - 'json': The JSON payload containing other data.
    """
    
    if 'file' not in request.files or 'json' not in request.form:
        return make_response(json_util.dumps({"error": "Both image file and JSON payload are required, as a multipart request."}), 400)

    file = request.files['file']

    if file.filename == '':
        return make_response(json_util.dumps({"error": "No image file uploaded"}), 400)

    filename = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex
    filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{unique_id}_{filename}" # create a unique filename
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

    # insert the data into the database
    try:
        insert_data_to_db(client_gatcha, 'db-gatcha', 'db_gatcha', data)
        response = make_response(json_util.dumps({"message": "Data with image added to gatcha_db", "data": data}), 200)
        response.headers['Content-Type'] = 'application/json' # TODO: dovremmo fare così per tutti i response in JSON? agli altri manca
        return response
    except Exception as e:
        return make_response(json_util.dumps({"error": f"Database insert failed: {str(e)}"}), 500)






# Endpoint per rollare un gatcha
@app.route('/roll', methods=['GET'])
def roll_gatcha():
    try:
        # Estrai la rarità in base alle probabilità definite
        selected_rarity = weighted_random_choice(RARITY_PROBABILITIES)
        
        # Query al database per ottenere un personaggio della rarità selezionata
        gachas = list(client_gatcha['gatcha_db']['gatchas'].find({"rarity": selected_rarity}))

        if not gachas:
            return make_response(f"No character found for rarity {selected_rarity}\n", 404)
        # Estrai un personaggio randomico dalla lista dei personaggi della rarità selezionata
        character = random.choice(gachas) if gachas else None
        
        # Gestisci l'eventualità che non ci sia un personaggio di quella rarità
        if not character:
            return make_response(f"No character found for rarity {selected_rarity}\n", 404)
        
        # Increment NTot for the selected character
        client_gatcha['gatcha_db']['gatchas'].update_one(
            {'_id': character['_id']},  # Trova il personaggio tramite il suo ID
            {'$inc': {'NTot': 1}}       # Incrementa il campo NTot di 1
        )

        ##TODO: dal JWT, prendi il nome utente, e aggiungerai il gatcha all'utente che ha quel nome utente; il JWT ci certifica che il nome utente che c'è scritto dentro appartiene davevro al proprietario (è autenticato
        
        return make_response(json_util.dumps(character), 200)
    except Exception as e:
        return make_response(str(e), 500)
    
# Endpoint per ottenere tutti i possibili gatcha
@app.route('/getAll', methods=['GET'])
def get_all_gatcha():
    try:
        all_gatcha = list(client_gatcha['gatcha_db']['gatchas'].find({}))
        return make_response(json_util.dumps(all_gatcha), 200)
    except Exception as e:
        return make_response(str(e), 500)

def create_app():
    return app
