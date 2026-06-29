from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin


db = SQLAlchemy()


class Users(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="sales_officer")
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotations = db.relationship("Quotations", back_populates="prepared_by", lazy=True)

    serialize_rules = ("-password", "-quotations.prepared_by")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
        }


class Customers(db.Model, SerializerMixin):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    kra_pin = db.Column(db.String(50), nullable=True)
    physical_address = db.Column(db.Text, nullable=True)
    county = db.Column(db.String(100), nullable=True)
    customer_type = db.Column(db.String(50), nullable=False, default="commercial")
    outstanding_balance = db.Column(db.Float, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotations = db.relationship("Quotations", back_populates="customer", lazy=True)

    serialize_rules = ("-quotations.customer",)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "kra_pin": self.kra_pin,
            "physical_address": self.physical_address,
            "county": self.county,
            "customer_type": self.customer_type,
            "outstanding_balance": self.outstanding_balance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Products(db.Model, SerializerMixin):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    unit = db.Column(db.String(50), nullable=False, default="pcs")
    buying_price = db.Column(db.Float, default=0)
    selling_price = db.Column(db.Float, nullable=False)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    current_stock = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotation_items = db.relationship("QuotationItems", back_populates="product", lazy=True)

    serialize_rules = ("-quotation_items.product",)

    def to_dict(self):
        return {
            "id": self.id,
            "item_code": self.item_code,
            "product_name": self.product_name,
            "category": self.category,
            "brand": self.brand,
            "unit": self.unit,
            "buying_price": self.buying_price,
            "selling_price": self.selling_price,
            "vat_status": self.vat_status,
            "current_stock": self.current_stock,
            "reorder_level": self.reorder_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Quotations(db.Model, SerializerMixin):
    __tablename__ = "quotations"

    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    quote_date = db.Column(db.Date, default=date.today)
    valid_until = db.Column(db.Date, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    project_name = db.Column(db.String(150), nullable=True)
    site_location = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default="draft")
    sub_total = db.Column(db.Float, default=0)
    vat_exempt_total = db.Column(db.Float, default=0)
    vatable_total = db.Column(db.Float, default=0)
    vat_amount = db.Column(db.Float, default=0)
    grand_total = db.Column(db.Float, default=0)
    terms_conditions = db.Column(db.Text, nullable=True)
    prepared_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    authorized_by = db.Column(db.String(100), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="quotations")
    prepared_by = db.relationship("Users", back_populates="quotations")
    items = db.relationship("QuotationItems", back_populates="quotation", lazy=True, cascade="all, delete-orphan")

    serialize_rules = ("-customer.quotations", "-items.quotation", "-prepared_by.quotations")

    def to_dict(self):
        return {
            "id": self.id,
            "quote_number": self.quote_number,
            "quote_date": self.quote_date.isoformat() if self.quote_date else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "project_name": self.project_name,
            "site_location": self.site_location,
            "status": self.status,
            "sub_total": self.sub_total,
            "vat_exempt_total": self.vat_exempt_total,
            "vatable_total": self.vatable_total,
            "vat_amount": self.vat_amount,
            "grand_total": self.grand_total,
            "terms_conditions": self.terms_conditions,
            "authorized_by": self.authorized_by,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QuotationItems(db.Model, SerializerMixin):
    __tablename__ = "quotation_items"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    item_description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0)
    discount = db.Column(db.Float, default=0)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    line_total = db.Column(db.Float, default=0)

    quotation = db.relationship("Quotations", back_populates="items")
    product = db.relationship("Products", back_populates="quotation_items")

    serialize_rules = ("-quotation.items", "-product.quotation_items")

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_id": self.quotation_id,
            "product_id": self.product_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount": self.discount,
            "vat_status": self.vat_status,
            "line_total": self.line_total,
        }