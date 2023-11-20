import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from flask import Flask, send_from_directory
from PIL import Image
import numpy as np
import tensorflow as tf

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this based on your deployment needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = tf.keras.models.load_model('model.h5')


@app.post("/classify")
async def classify_image(image: UploadFile = File(...)):
    contents = await image.read()
    image = Image.open(io.BytesIO(contents))

    image = image.resize((150, 150))  
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array)

    predicted_class = np.argmax(predictions[0])

    class_labels = ['glioma_tumor', 'meningioma_tumor',
              'no_tumor', 'pituitary_tumor']

    class_name = class_labels[predicted_class]

    return JSONResponse({'message': str(class_name)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
