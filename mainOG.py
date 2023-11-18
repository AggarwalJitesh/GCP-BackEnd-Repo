from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from fastapi import FastAPI
from uvicorn import run
import uvicorn
import numpy as np
import cv2
import os
import io
from PIL import Image
from os.path import join, dirname, realpath
from keras.models import load_model
from werkzeug.utils import secure_filename
from typing_extensions import Annotated, Final, Literal, TypeGuard, get_args, get_origin
from typing import Type


UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploads/')
# app = Flask(__name__)
# CORS(app,origins="*")
app = FastAPI()

# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.secret_key = 'This is your secret key to utilize session in Flask'

model = load_model("model.h5")

# MyType = Type[int]



def predict_result(predict):
    img = cv2.imread(predict)
    img = cv2.resize(img, (150, 150))
    img_array = np.array(img)
    img_array = img_array.reshape(1, 150, 150, 3)
    a = model.predict(img_array)
    indices = a.argmax()
    labels = ['glioma_tumor', 'meningioma_tumor',
              'no_tumor', 'pituitary_tumor']
    return labels[indices]


# @app.route('/')
# def home():
#    return render_template('index.html')


@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_image():
    
    if request.method == "POST":
        file = request.files.get('file')
        if file is None or file.filename == "":
            return jsonify({"error": "no file"})

        try:
            image_bytes = file.read()
            pillow_img = Image.open(io.BytesIO(image_bytes)).convert('L')
            prediction = predict_result(pillow_img)
            return jsonify({'message': str(prediction)})
        except Exception as e:
            return jsonify({"error": str(e)})

    return "OK"


    # if 'image' not in request.files:
    #     return jsonify({'error': 'No file part in the request'}), 400

    # uploaded_img = request.files['image']

    # img_filename = secure_filename(uploaded_img.filename)
    # uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
    # img = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
    # session['uploaded_img_file_path'] = os.path.join(
    #     app.config['UPLOAD_FOLDER'], img_filename)
    # img_file_path = session.get('uploaded_img_file_path', None)

    # print(img)

    # pred = predict_result(img_file_path)
    # return jsonify({'message': str(pred)})

# if __name__ == '__main__':
#     # app.run(debug=True)

#     app.run(port=int(os.environ.get("PORT",5000)),host='0.0.0.0',debug=True)
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, workers=2)
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=2)
    # run(app, reload=True)
    # uvicorn.run(app, host="0.0.0.0", port=5000)