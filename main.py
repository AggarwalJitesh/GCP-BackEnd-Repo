import io
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
from keras.models import load_model

# GCP cloud sql commands
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = load_model('model.h5')

@app.post("/classify")
async def classify_image(image: UploadFile = File(...)):
    # Read the image file
    contents = await image.read()
    image = Image.open(io.BytesIO(contents))

    image = image.resize((150, 150))  # Adjust the size based on your model requirements
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array)

    predicted_class = np.argmax(predictions[0])

    class_labels = ['glioma_tumor', 'meningioma_tumor',
              'no_tumor', 'pituitary_tumor']

    class_name = class_labels[predicted_class]

    return JSONResponse({'message': str(class_name)})




# GCP cloud sql commands
DATABASE_URL = "mysql://sign-up-database:blockconvey2024@34.29.182.200/Signup"


class FormData(BaseModel):
    username: str
    email: str
    password: str


database = Database(DATABASE_URL)

@app.post("/submit-form")
async def submit_form(data: FormData):
    await database.connect()
    
    query = "INSERT INTO users(username, email, password) VALUES (:username, :email, :password)"
    values = {"username": data.username,
              "email": data.email, "password": data.password}
    try:
        await database.execute(query=query, values=values)
        return {"message": "Data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    await database.disconnect()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

