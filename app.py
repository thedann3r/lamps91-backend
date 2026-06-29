from flask import Flask, request, jsonify 
from flask import Flask
from flask_restful import Api
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from models import db
from resources.crud import Customer, CustomerResource, Product, ProductResource, Quotation, QuotationResource

load_dotenv(override=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  'sqlite:///data.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)
cors = CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
api = Api(app)

@app.route("/")
def index():
    return "Hello! I am doing a project for Vincent!"

api.add_resource(Customer, "/customers")
api.add_resource(CustomerResource, "/customers/<int:customer_id>")
api.add_resource(Product, "/products")
api.add_resource(ProductResource, "/products/<int:product_id>")
api.add_resource(Quotation, "/quotations")
api.add_resource(QuotationResource, "/quotations/<int:quotation_id>")

if __name__ == "__main__":
    app.run(debug = True)