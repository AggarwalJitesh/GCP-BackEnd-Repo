import io
import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from flask import Flask, send_from_directory
from PIL import Image
import numpy as np
import tensorflow as tf

# Create a FastAPI app
app = FastAPI()

# Enable CORS (Cross-Origin Resource Sharing) for all routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this based on your deployment needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your pre-trained model
model = tf.keras.models.load_model('model.h5')

# Create a Flask app for serving the React app
# react_app = Flask(__name__, static_folder="react_app/build", static_url_path="/")

# # Route to serve the React app
# @react_app.route("/")
# def index():
#     return send_from_directory(react_app.static_folder, "index.html")

# # Route to serve static files from the React app
# @react_app.route("/static/<path:filename>")
# def static_files(filename):
#     return send_from_directory(react_app.static_folder + "/static", filename)


# Route to handle image classification
@app.post("/classify")
async def classify_image(image: UploadFile = File(...)):
    # Read the image file
    contents = await image.read()
    image = Image.open(io.BytesIO(contents))

    # Preprocess the image
    image = image.resize((150, 150))  # Adjust the size based on your model requirements
    image_array = np.array(image) / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    # Make predictions using the model
    predictions = model.predict(image_array)

    # Get the predicted class
    predicted_class = np.argmax(predictions[0])

    # Replace this with your own class labels
    class_labels = ['glioma_tumor', 'meningioma_tumor',
              'no_tumor', 'pituitary_tumor']

    # Get the class name
    class_name = class_labels[predicted_class]

    # Return the result as JSON
    return JSONResponse({'message': str(class_name)})

# Run the FastAPI app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    # uvicorn.run(app, host="0.0.0.0", port=5000)
