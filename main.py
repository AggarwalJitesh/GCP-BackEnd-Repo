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
# import bcrypt

# GCP cloud storage
from google.cloud import storage

# static file save
from fastapi.staticfiles import StaticFiles
import uuid

#connection with solidity
from web3 import Web3
import json

app = FastAPI()


# Directory where images will be stored
IMAGE_DIR = "static"
app.mount("/static", StaticFiles(directory="static"), name="static")
imgurl=""

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
    unique_filename = f"image_{uuid.uuid4()}.jpg"
    full_file_path = os.path.join(IMAGE_DIR, unique_filename)
    # print(full_file_path)
    
    # # Get the current IAM policy of the bucket
    # policy = bucket.get_iam_policy()
    
    
    # # Add a new binding to the IAM policy
    # policy.bindings.append({
    #     'role': 'roles/storage.objectViewer',
    #     'members': {'allUsers'}
    #     })
    
    
    # # Save the updated IAM policy
    # bucket.set_iam_policy(policy)
    
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
    
    # class_labels = ['glioma_tumor', 'meningioma_tumor',
    #                 'no_tumor', 'pituitary_tumor']

    class_labels = ['Glioma Tumor', 'Meningioma Tumor',
                    'No Tumor', 'Pituitary Tumor']

    class_name = class_labels[predicted_class]    
    
    
    #save image to local directory
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
    
    
@app.get("/addtoblockchain")
async def addtochain():
    web3 = Web3(Web3.HTTPProvider(
        'https://nd-651-483-575.p2pify.com/cbda8d1c04f6e11e5f15b7a9cb95183f'))
    
    
    # Check connection
    if not web3.is_connected():
        print("Failed to connect to the Ethereum blockchain.")
        exit()


    # Contract Address and ABI (replace with your contract's address and ABI)
    contract_address = '0x8219401F52eECE298E771D2cbFfB3624C139daFb'
    
    with open('NFTMarketplace.json', 'r') as abi_file:
        contract_abi = json.load(abi_file)
    

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    
    # Your account and private key
    account = '0x765941e3AA25533001280b2e0463a5544b165d0F'
    private_key = '0xa45e9945d494d99189a78ffe74bdc21b362276d86a8b920c59a2d89c40ad9ecc'
    
    # Prepare the transaction

    create_token_function = contract.functions.createToken(
        imgurl)
    create_token_txn = create_token_function.build_transaction({
        'from': account,  
        'nonce': web3.eth.get_transaction_count(account),
        'gas': 2000000,  
        # 'gasPrice': web3.to_wei('50', 'gwei')
        'gasPrice': 0
    })
    
    
    

    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(create_token_txn, private_key)
    # print("signed_txn = ", signed_txn)
    
    
    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("tx_hash = ", tx_hash)
    
    
    # Get transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    # print("tx_receipt = ", tx_receipt)
    
    
    # matching the tokenURI and the imgurl
    token_id = 1  # Replace with your actual token ID
    
    token_uri = contract.functions.tokenURI(token_id).call()
    print(f"Token URI: {token_uri}")
    # if token_uri == imgurl:
    #     print("The token URI matches the intended image URL.")
    # else:
    #     print("The token URI does not match the intended image URL.")

    return {"message": "added to chain"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

