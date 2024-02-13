import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from keras.models import load_model

# GCP cloud sql commands
from pydantic import BaseModel
from databases import Database

# GCP cloud storage
from google.cloud import storage
from datetime import datetime

# static file save
from fastapi.staticfiles import StaticFiles
import uuid

# connection with solidity
from web3 import Web3
import json
from eth_abi.exceptions import EncodingError
from hexbytes import HexBytes

# connectiion with creds file
from creds import HTTPlink, contract_address, account_address, private_key


app = FastAPI()


# Directory where images will be stored
IMAGE_DIR = "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

userid = ""
imgurl = ""
classificationResult = ""
unique_filename = ""
original_dict = {}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = load_model('model.h5')

# Initialize Google Cloud Storage client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service_access.json'
storage_client = storage.Client()
bucket = storage_client.bucket('demo_blockconvey')


@app.post("/classify")
async def classify_image(image: UploadFile = File(...)):
    contents = await image.read()
    global unique_filename
    unique_filename = f"image_{uuid.uuid4()}.jpg"
    full_file_path = os.path.join(IMAGE_DIR, unique_filename)
    # print(full_file_path)

    # Google Cloud Storage
    blob = bucket.blob(full_file_path)
    blob.upload_from_string(contents, content_type=image.content_type)

    # Construct the GCP URL
    global imgurl
    imgurl = f"https://storage.cloud.google.com/{bucket.name}/{blob.name}"

    image = Image.open(io.BytesIO(contents))
    image = image.resize((150, 150))
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array)

    predicted_class = np.argmax(predictions[0])

    class_labels = ['Glioma Tumor', 'Meningioma Tumor',
                    'No Tumor', 'Pituitary Tumor']

    class_name = class_labels[predicted_class]

    global classificationResult
    classificationResult = class_name

    # save image to local directory
    # image.save(full_file_path)

    # Construct the local URL
    # imgurl = f"http://127.0.0.1:8000/static/{unique_filename}"

    return JSONResponse({'message': str(class_name)})


class FormData(BaseModel):
    username: str
    email: str
    password: str


class loginFormData(BaseModel):
    email: str
    password: str


# GCP cloud sql commands
DATABASE_URL = "mysql://root:blockconvey2024@34.29.182.200:3306/Signup"

database = Database(DATABASE_URL)


async def email_exists(email: str) -> bool:
    query = "SELECT * FROM users WHERE email = :email"
    return await database.fetch_one(query, {"email": email})


async def verify_password(email: str, user_password: str) -> bool:
    query = "SELECT password FROM users WHERE email = :email"
    result = await database.fetch_one(query, {"email": email})

    if result:
        stored_password_hash = result['password']
        return user_password == stored_password_hash
    else:
        return False


async def finduser(email: str) -> str:
    query = "SELECT username FROM users WHERE email = :email"
    result = await database.fetch_one(query, {"email": email})
    return result['username']


@app.post("/submit-form")
async def signup(data: FormData):
    await database.connect()

    if await email_exists(data.email):
        return {"message": "Email already in use, please use a different email"}

    # If email does not exist, insert new user data
    query = "INSERT INTO users(username, email, password) VALUES (:username, :email, :password)"
    values = {"username": data.username,
              "email": data.email, "password": data.password}

    try:
        await database.execute(query, values)
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/checklogin")
async def login(data: loginFormData):
    await database.connect()

    if await email_exists(data.email) and await verify_password(data.email, data.password):
        global userid
        userid = await finduser(data.email)
        return {"message": "User Authenticated", "userid": userid}
    else:
        return {"message": "Authentication Failed"}


@app.get("/logout")
async def logout():
    userid = None
    print("logout = ", userid)
    return {"message": "Logged out successfully"}


# BLOCKCHAIN CONNECTION

w3 = Web3(Web3.HTTPProvider(HTTPlink))

with open('NFT.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)


def hexbytes_to_hex(json_data):
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, HexBytes):
                json_data[key] = value.hex()
            elif isinstance(value, (dict, list)):
                json_data[key] = hexbytes_to_hex(value)
    elif isinstance(json_data, list):
        json_data = [hexbytes_to_hex(item) if isinstance(
            item, (dict, list)) else item for item in json_data]
    return json_data


# GCP cloud sql commands
DATABASE_URL_uploadhistory = "mysql://root:blockconvey2024@34.29.182.200:3306/uploadHistory"

database_uploadhistory = Database(DATABASE_URL_uploadhistory)


@app.get("/addtoblockchain")
async def addtochain():

    try:

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)

        create_token_txn = contract.functions.createToken(imgurl).build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gas': 2000000,
            # 'gasPrice': web3.to_wei('50', 'gwei')
            'gasPrice': 0

        })

        signed_tx = w3.eth.account.sign_transaction(
            create_token_txn, private_key=private_key)
        # print("signed_txn = ", signed_txn)

        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        print("tx_hash = ", tx_hash_hex)

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("tx_receipt = ", tx_receipt)

        global original_dict
        original_dict = dict(w3.eth.get_transaction(tx_hash))

        json_serializable_dict = hexbytes_to_hex(original_dict)

        current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # saving image perticular in gcp

        await database_uploadhistory.connect()

        query = "INSERT INTO uploadLogs(imagename, result, blockHash , blockNumber , txnHash , imgUrl, dateTime, userid ) VALUES (:imagename, :result, :blockHash , :blockNumber , :txnHash , :imgUrl, :dateTime, :userid )"
        values = {"imagename": unique_filename, "result": classificationResult,
                  "blockHash": json_serializable_dict["hash"], "blockNumber": json_serializable_dict["blockNumber"], "txnHash": tx_hash_hex, "imgUrl": imgurl, "dateTime": current_datetime, "userid": userid}

        try:
            await database_uploadhistory.execute(query, values)
            return {"message": "added successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    except EncodingError:
        raise HTTPException(status_code=400, detail="Invalid image URL format")


@app.get("/transaction")
async def transaction_dict():
    
    # array = [{'imagename': 'image_b973a0f6-381d-4110-a334-c199ffb6a249.jpg', 'result': 'No Tumor', 'blockHash': '0xde1ec045879ab33eefc5be20d828def04effdfda7b7925931ef91814af51abaa', 'blockNumber': '9868486', 'txnHash': '0xde1ec045879ab33eefc5be20d828def04effdfda7b7925931ef91814af51abaa', 'imgUrl': 'https://storage.cloud.google.com/demo_blockconvey/static/image_b973a0f6-381d-4110-a334-c199ffb6a249.jpg', 'dateTime': '2024-02-08T20:26:04'}, {'imagename': 'image_6b4e1ed8-cb1b-4bc3-bde4-c172ae22cfec.jpg', 'result': 'No Tumor', 'blockHash': '0x32786e8ee64214620168b00c1338e079292e1953c512c220ced160e96ed95e97', 'blockNumber': '9868746', 'txnHash': '0x32786e8ee64214620168b00c1338e079292e1953c512c220ced160e96ed95e97', 'imgUrl': 'https://storage.cloud.google.com/demo_blockconvey/static/image_6b4e1ed8-cb1b-4bc3-bde4-c172ae22cfec.jpg', 'dateTime': '2024-02-08T20:30:24'}, {'imagename': 'image_7a5c5356-6ff9-4290-8f1d-63ad1941ce86.jpg', 'result': 'No Tumor', 'blockHash': '0xac4174f76a0a6fa36b63687321bfe11572ead789c6e227824d15f131b94469c0', 'blockNumber': '9870273', 'txnHash': '0xac4174f76a0a6fa36b63687321bfe11572ead789c6e227824d15f131b94469c0', 'imgUrl': 'https://storage.cloud.google.com/demo_blockconvey/static/image_7a5c5356-6ff9-4290-8f1d-63ad1941ce86.jpg', 'dateTime': '2024-02-08T20:55:51'}, {'imagename': 'image_08be4813-2416-4add-9832-aea79a71f260.jpg', 'result': 'No Tumor', 'blockHash': '0xadbcdaacb0cf7c2f42700f73f3ebd4179258c7f586ba5922a4c21012f1019b1a', 'blockNumber': '9870313', 'txnHash': '0xadbcdaacb0cf7c2f42700f73f3ebd4179258c7f586ba5922a4c21012f1019b1a', 'imgUrl': 'https://storage.cloud.google.com/demo_blockconvey/static/image_08be4813-2416-4add-9832-aea79a71f260.jpg', 'dateTime': '2024-02-08T20:56:31'}]
    
    # return array
    
    
    await database_uploadhistory.connect()

    query = "SELECT imagename, result, blockHash , blockNumber , txnHash , imgUrl, dateTime FROM uploadLogs WHERE userid = :userid"
    result = await database_uploadhistory.fetch_all(query, {"userid": userid})
    
    if result:
        return [dict(row) for row in result]



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


