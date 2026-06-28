from flask import Flask, request, jsonify 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token

load_dotenv(override=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  'sqlite:///data.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
cors = CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

@app.route("/")
def index():
    return "Hello doing a project for Vincent!"

if __name__ == "__main__":
    app.run(debug = True)