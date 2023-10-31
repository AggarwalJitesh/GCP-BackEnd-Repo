from flask import Flask, request, jsonify, session
from flask_cors import CORS
import numpy as np
import cv2
import os
from os.path import join, dirname, realpath
from keras.models import load_model
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploads/')
app = Flask(__name__)
CORS(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'This is your secret key to utilize session in Flask'

model = load_model("/Users/jiteshaggarwal/Downloads/trained_model/model.h5")


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


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    uploaded_img = request.files['image']

    img_filename = secure_filename(uploaded_img.filename)
    uploaded_img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
    img = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
    session['uploaded_img_file_path'] = os.path.join(
        app.config['UPLOAD_FOLDER'], img_filename)
    img_file_path = session.get('uploaded_img_file_path', None)

    print(img)

    pred = predict_result(img_file_path)
    return jsonify({'message': str(pred)})

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=int(os.envion.get("PORT",5000)))
