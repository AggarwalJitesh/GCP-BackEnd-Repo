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

# static file save
from fastapi.staticfiles import StaticFiles
import uuid

# connection with solidity
from web3 import Web3
import json
from eth_abi.exceptions import EncodingError
from hexbytes import HexBytes

app = FastAPI()


# Directory where images will be stored
IMAGE_DIR = "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# test variable
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


# GCP cloud sql commands
DATABASE_URL = "mysql://root:blockconvey2024@34.29.182.200:3306/Signup"


class FormData(BaseModel):
    username: str
    email: str
    password: str


class loginFormData(BaseModel):
    email: str
    password: str


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
        return {"message": "User Authenticated"}


# BLOCKCHAIN CONNECTION

w3 = Web3(Web3.HTTPProvider(
    'https://nd-651-483-575.p2pify.com/cbda8d1c04f6e11e5f15b7a9cb95183f'))

contract_address = '0x96DE750De9C3AB4b5916FbbF977AE6FE2Fc0f739'


with open('NFT.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)

account_address = '0x765941e3AA25533001280b2e0463a5544b165d0F'
private_key = '0xa45e9945d494d99189a78ffe74bdc21b362276d86a8b920c59a2d89c40ad9ecc'



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


@app.get("/transaction")
async def transaction_dict():

    json_serializable_dict = hexbytes_to_hex(original_dict)

    data_to_send = {
        "blockHash": json_serializable_dict["blockHash"],
        "blockNumber": json_serializable_dict["blockNumber"],
        "hash": json_serializable_dict["hash"],
        "imageName": unique_filename,
        "result": classificationResult,
        "url": imgurl
    }

    return data_to_send


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

        # Sign the transaction
        signed_tx = w3.eth.account.sign_transaction(
            create_token_txn, private_key=private_key)
        # print("signed_txn = ", signed_txn)

        # Send the transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        print("tx_hash = ", tx_hash_hex)

        # Get transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("tx_receipt = ", tx_receipt)

        global original_dict
        original_dict = dict(w3.eth.get_transaction(tx_hash))
        
        return {"message": "added successfully"}

    except EncodingError:
        raise HTTPException(status_code=400, detail="Invalid image URL format")

    # Parse the transaction receipt to find the events

    # if tx_receipt.status == 1 and tx_receipt.logs:
    #     try:
    #         decoded_logs = contract.events.Transfer().processReceipt(tx_receipt)
    #         for event in decoded_logs:
    #             token_id = event.args.tokenId
    #             print("Token ID:", token_id)
    #     except Exception as e:
    #         print("Error processing receipt:", e)
    # else:
    #     print("No successful transfer events found or transaction failed.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
