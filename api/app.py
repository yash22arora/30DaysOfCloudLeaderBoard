from flask import Flask, jsonify, request, redirect
from database import SessionLocal, engine
from getData import *
from database import *
from getDB import *
import models
from security import *
from werkzeug.utils import secure_filename
import csv

app = Flask(__name__)

db = SessionLocal()
models.Base.metadata.create_all(bind=engine)

@app.route('/')
def index():
    return jsonify(getJsonFromDB())


@app.route('/add', methods=['POST'])
def add():
    # get header
    header = request.headers.get('Authorization')
    if header is None:
        return jsonify({"error": "No authorization header"}), 401

    # pass token to verify
    if get_current_user(header) == None:
        return jsonify({"error": "Invalid token"}), 401
    
    # get data from the name email and qwiklabs from the request
    #print(request.json)
    
    name = request.json['name']
    email = request.json['email']
    qwiklabs = request.json['qwiklabs']
    score = getScore(qwiklabs)
    user = models.Leaderboard(name=name, email=email, qwiklab_url=qwiklabs, total_score=score["total_score"], track1_score=score["track1_score"], track2_score=score["track2_score"])
    try:
        db.add(user)
        db.commit()
        # refresh the db
        refreshDb()
        return jsonify({"success": "success"})
    except:
        return jsonify({"error": "Already exists"})

# upload csv file and put data in the database
@app.route('/upload', methods=['POST'])
def upload():
    # get header
    header = request.headers.get('Authorization')
    if header is None:
        return jsonify({"error": "No authorization header"}), 401

    # pass token to verify
    if get_current_user(header) == None:
        return jsonify({"error": "Invalid token"}), 401
    
    # get name email and qwiklabs from the file uploaded
    file = request.files['file']
    # saving the file
    filename = secure_filename(file.filename)
    file.save(filename)
    # open the file => csv file
    with open(filename, 'r') as csvfile:
        # read the file
        reader = csv.DictReader(csvfile)
        # loop through the file
        for row in reader:
            # get data from the name email and qwiklabs from the file
            try:
                name = row['name']
                email = row['email']
                qwiklabs = row['qwiklabs']
                score = getScore(qwiklabs)
                user = models.Leaderboard(name=name, email=email, qwiklab_url=qwiklabs, total_score=score["total_score"], track1_score=score["track1_score"], track2_score=score["track2_score"])
                try:
                    db.add(user)
                    db.commit()
                except:
                    pass
            except:
                return jsonify({"error": "Invalid csv file"})
        # refresh the db
        return jsonify({"success": "success"})

@app.route('/register', methods=['POST'])
def register():
    # get data from the name email and qwiklabs from the request
    #print(request.json)
    
    username = request.json['username']
    password = request.json['password']
    user = models.UserModel(username=username, password=hashMe(password))
    try:
        db.add(user)
        db.commit()
        return jsonify({"success": "success"})
    except:
        return jsonify({"error": "Already exists"})

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    user = db.query(models.UserModel).filter_by(username=username).first()
    if not user:
        return jsonify({"message": "user does not exist"})        

    if not verify_passwd(password, user.password):
        # return status code 401 and send message
        return jsonify({"message": "Invalid credentials"})

    access_token = create_access_token(user.username)
    return {"access_token": access_token, "type": "bearer"}


if __name__== "__main__":
    app.run(
        host='0.0.0.0', port="5000",
    )


