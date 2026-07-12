# from flask import Flask, request, jsonify 
from flask import Flask
from flask_restful import Api
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from models import db
import os
from resources.crud import (    
    Customer, CustomerResource,
    Product, ProductResource,
    Quotation, QuotationResource,
    SalesOrder, SalesOrderResource,
    Invoice, InvoiceResource,
    Receipt, ReceiptResource,
    Supplier, SupplierResource,
    PurchaseOrder, PurchaseOrderResource,
    StockTransaction, StockTransactionResource,
    Project, ProjectResource
)

load_dotenv(override=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  'sqlite:///data.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default_secret_key")

db.init_app(app)
migrate = Migrate(app, db)
cors = CORS(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
api = Api(app)

@app.route("/")
def index():
    return "Hello! I am doing a project for Vincent!"

# customer endpoints
api.add_resource(Customer, "/customers")
api.add_resource(CustomerResource, "/customers/<int:customer_id>")

# Product endpoints
api.add_resource(Product, "/products")
api.add_resource(ProductResource, "/products/<int:product_id>")

# Quotation endpoints
api.add_resource(Quotation, "/quotations")
api.add_resource(QuotationResource, "/quotations/<int:quotation_id>")

# Sales Order endpoints
api.add_resource(SalesOrder, "/salesorders")
api.add_resource(SalesOrderResource, "/salesorders/<int:order_id>")

# Invoice endpoints
api.add_resource(Invoice, "/invoices")
api.add_resource(InvoiceResource, "/invoices/<int:invoice_id>")

# Receipt endpoints
api.add_resource(Receipt, "/receipts")
api.add_resource(ReceiptResource, "/receipts/<int:receipt_id>")

# Supplier endpoints
api.add_resource(Supplier, "/suppliers")
api.add_resource(SupplierResource, "/suppliers/<int:supplier_id>")

# Purchase Order endpoints
api.add_resource(PurchaseOrder, "/purchaseorders")
api.add_resource(PurchaseOrderResource, "/purchaseorders/<int:po_id>")

# Stock Transaction endpoints
api.add_resource(StockTransaction, "/stocktransactions")
api.add_resource(StockTransactionResource, "/stocktransactions/<int:transaction_id>")

# Project endpoints
api.add_resource(Project, "/projects")
api.add_resource(ProjectResource, "/projects/<int:project_id>")

if __name__ == "__main__":
    app.run(debug = True)