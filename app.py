from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import database
from objects import User, Plant
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
import os
import uuid
from flask_cors import CORS, cross_origin
import datetime

app = Flask(__name__)

db = database.model()

IMG_PATH = 'docs/images/user_plants'
if not os.path.exists(IMG_PATH):
    os.makedirs(IMG_PATH)

def authenticate(username, password):
    user = db.get_user_by_username(username=username)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user

def identity(payload):
    user_id = payload['identity']
    user = db.get_user_by_id(user_id=user_id)
    return user

app.config['SECRET_KEY'] = 'This is a secret key!'

app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(hours=48)
jwt = JWT(app, authenticate, identity)

#set the CORS headrer to allow all access
CORS(app, supports_credentials=True)

@app.route('/new_user', methods=["POST"])
def new_user():
    credentials = request.get_json()
    if db.create_user(credentials["username"],credentials["password"]):
        return jsonify("Success"), 201
    return jsonify("Couldn't create user"), 500

@app.route('/plants/img', methods=["POST"])
@jwt_required()
def add_img():
    img = request.files['plant_img']
    filename = str(uuid.uuid4()) + '.jpg'
    with open(os.path.join(IMG_PATH, filename), "wb") as fp:
        fp.write(img.read())
    return {"img_name":filename}, 200

@app.route('/plant', methods=["POST"])
@jwt_required()
def add_plant():
    values = request.values
    name = values['name']
    description = values['desciption']
    water_interval = values["water_interval"]
    img = request.files['plant_img'].read()

    filename = str(uuid.uuid4()) + '.jpg'
    filepath = os.path.join(IMG_PATH, filename)
    with open(filepath, "wb") as fp:
        fp.write(img)
    
    new_plant = Plant(id=None,user_id=current_identity.id, name=name, img_path=str(filepath), water_interval=water_interval, days_until_water=water_interval, notes=description)
    try:
        db.add_plant(current_identity, new_plant)
    except:
        return jsonify("couldn't add plant"), 500
    return jsonify("added the plant"), 200

@app.route('/plants', methods=["GET"])
@jwt_required()
def get_plants():
    plants = db.get_plants(current_identity)
    all_plants = []
    for plant in plants:
        all_plants.append(plant.__dict__)
    return jsonify(all_plants), 200

@app.route('/dashboard', methods=["GET"])
@jwt_required()
def dashboard():
    user = current_identity
    return jsonify(user.username)


if __name__ == "__main__":
    app.run(debug=True)
