from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin


db = SQLAlchemy()


def money_value(value):
    return float(value) if value is not None else 0


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
    stock_transactions = db.relationship("StockTransactions", back_populates="user", lazy=True)

    serialize_rules = (
        "-password",
        "-quotations.prepared_by",
        "-stock_transactions.user",
    )

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
    outstanding_balance = db.Column(db.Numeric(12, 2), default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotations = db.relationship("Quotations", back_populates="customer", lazy=True)
    sales_orders = db.relationship("SalesOrders", back_populates="customer", lazy=True)
    invoices = db.relationship("Invoices", back_populates="customer", lazy=True)
    receipts = db.relationship("Receipts", back_populates="customer", lazy=True)
    projects = db.relationship("Projects", back_populates="customer", lazy=True)

    serialize_rules = (
        "-quotations.customer",
        "-sales_orders.customer",
        "-invoices.customer",
        "-receipts.customer",
        "-projects.customer",
    )

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
            "outstanding_balance": money_value(self.outstanding_balance),
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
    buying_price = db.Column(db.Numeric(12, 2), default=0)
    selling_price = db.Column(db.Numeric(12, 2), nullable=False)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    current_stock = db.Column(db.Float, default=0)
    reorder_level = db.Column(db.Float, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotation_items = db.relationship("QuotationItems", back_populates="product", lazy=True)
    invoice_items = db.relationship("InvoiceItems", back_populates="product", lazy=True)
    purchase_order_items = db.relationship("PurchaseOrderItems", back_populates="product", lazy=True)
    stock_transactions = db.relationship("StockTransactions", back_populates="product", lazy=True)

    serialize_rules = (
        "-quotation_items.product",
        "-invoice_items.product",
        "-purchase_order_items.product",
        "-stock_transactions.product",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "item_code": self.item_code,
            "product_name": self.product_name,
            "category": self.category,
            "brand": self.brand,
            "unit": self.unit,
            "buying_price": money_value(self.buying_price),
            "selling_price": money_value(self.selling_price),
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
    sub_total = db.Column(db.Numeric(12, 2), default=0)
    vat_exempt_total = db.Column(db.Numeric(12, 2), default=0)
    vatable_total = db.Column(db.Numeric(12, 2), default=0)
    vat_amount = db.Column(db.Numeric(12, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)
    terms_conditions = db.Column(db.Text, nullable=True)
    prepared_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    authorized_by = db.Column(db.String(100), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="quotations")
    prepared_by = db.relationship("Users", back_populates="quotations")
    items = db.relationship("QuotationItems", back_populates="quotation", lazy=True, cascade="all, delete-orphan")
    sales_order = db.relationship("SalesOrders", back_populates="quotation", uselist=False)
    invoice = db.relationship("Invoices", back_populates="quotation", uselist=False)

    serialize_rules = (
        "-customer.quotations",
        "-prepared_by.quotations",
        "-items.quotation",
        "-sales_order.quotation",
        "-invoice.quotation",
    )

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
            "sub_total": money_value(self.sub_total),
            "vat_exempt_total": money_value(self.vat_exempt_total),
            "vatable_total": money_value(self.vatable_total),
            "vat_amount": money_value(self.vat_amount),
            "grand_total": money_value(self.grand_total),
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
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(12, 2), default=0)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    line_total = db.Column(db.Numeric(12, 2), default=0)

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
            "unit_price": money_value(self.unit_price),
            "discount": money_value(self.discount),
            "vat_status": self.vat_status,
            "line_total": money_value(self.line_total),
        }


class SalesOrders(db.Model, SerializerMixin):
    __tablename__ = "sales_orders"

    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(50), unique=True, nullable=False)
    so_date = db.Column(db.Date, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=True, unique=True)
    project_name = db.Column(db.String(150), nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    inventory_reserved = db.Column(db.Boolean, default=False)
    installation_team = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default="pending")
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="sales_orders")
    quotation = db.relationship("Quotations", back_populates="sales_order")
    invoice = db.relationship("Invoices", back_populates="sales_order", uselist=False)

    serialize_rules = ("-customer.sales_orders", "-quotation.sales_order", "-invoice.sales_order")

    def to_dict(self):
        return {
            "id": self.id,
            "so_number": self.so_number,
            "so_date": self.so_date.isoformat() if self.so_date else None,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "quotation_id": self.quotation_id,
            "project_name": self.project_name,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "inventory_reserved": self.inventory_reserved,
            "installation_team": self.installation_team,
            "status": self.status,
            "total_amount": money_value(self.total_amount),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Invoices(db.Model, SerializerMixin):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    sales_order_id = db.Column(db.Integer, db.ForeignKey("sales_orders.id"), nullable=True, unique=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=True, unique=True)
    reference = db.Column(db.String(100), nullable=True)
    sub_total = db.Column(db.Numeric(12, 2), default=0)
    vat_exempt_total = db.Column(db.Numeric(12, 2), default=0)
    vatable_total = db.Column(db.Numeric(12, 2), default=0)
    vat_amount = db.Column(db.Numeric(12, 2), default=0)
    invoice_total = db.Column(db.Numeric(12, 2), default=0)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)
    balance_due = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(50), default="pending")
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="invoices")
    sales_order = db.relationship("SalesOrders", back_populates="invoice")
    quotation = db.relationship("Quotations", back_populates="invoice")
    receipts = db.relationship("Receipts", back_populates="invoice", lazy=True, cascade="all, delete-orphan")
    invoice_items = db.relationship("InvoiceItems", back_populates="invoice", lazy=True, cascade="all, delete-orphan")

    serialize_rules = (
        "-customer.invoices",
        "-sales_order.invoice",
        "-quotation.invoice",
        "-receipts.invoice",
        "-invoice_items.invoice",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "sales_order_id": self.sales_order_id,
            "quotation_id": self.quotation_id,
            "reference": self.reference,
            "sub_total": money_value(self.sub_total),
            "vat_exempt_total": money_value(self.vat_exempt_total),
            "vatable_total": money_value(self.vatable_total),
            "vat_amount": money_value(self.vat_amount),
            "invoice_total": money_value(self.invoice_total),
            "amount_paid": money_value(self.amount_paid),
            "balance_due": money_value(self.balance_due),
            "status": self.status,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.invoice_items],
            "receipts": [receipt.to_dict() for receipt in self.receipts],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InvoiceItems(db.Model, SerializerMixin):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    item_description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(12, 2), default=0)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    line_total = db.Column(db.Numeric(12, 2), default=0)

    invoice = db.relationship("Invoices", back_populates="invoice_items")
    product = db.relationship("Products", back_populates="invoice_items")

    serialize_rules = ("-invoice.invoice_items", "-product.invoice_items")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "product_id": self.product_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": money_value(self.unit_price),
            "discount": money_value(self.discount),
            "vat_status": self.vat_status,
            "line_total": money_value(self.line_total),
        }


class Receipts(db.Model, SerializerMixin):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    receipt_date = db.Column(db.Date, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_reference = db.Column(db.String(100), nullable=True)
    amount_received = db.Column(db.Numeric(12, 2), nullable=False)
    outstanding_balance = db.Column(db.Numeric(12, 2), default=0)
    received_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="receipts")
    invoice = db.relationship("Invoices", back_populates="receipts")

    serialize_rules = ("-customer.receipts", "-invoice.receipts")

    def to_dict(self):
        return {
            "id": self.id,
            "receipt_number": self.receipt_number,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "invoice_id": self.invoice_id,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "amount_received": money_value(self.amount_received),
            "outstanding_balance": money_value(self.outstanding_balance),
            "received_by": self.received_by,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Suppliers(db.Model, SerializerMixin):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    kra_pin = db.Column(db.String(50), nullable=True)
    physical_address = db.Column(db.Text, nullable=True)
    county = db.Column(db.String(100), nullable=True)
    products_supplied = db.Column(db.Text, nullable=True)
    outstanding_orders = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    purchase_orders = db.relationship("PurchaseOrders", back_populates="supplier", lazy=True)

    serialize_rules = ("-purchase_orders.supplier",)

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_name": self.supplier_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "kra_pin": self.kra_pin,
            "physical_address": self.physical_address,
            "county": self.county,
            "products_supplied": self.products_supplied,
            "outstanding_orders": self.outstanding_orders,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PurchaseOrders(db.Model, SerializerMixin):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    po_date = db.Column(db.Date, default=date.today)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    required_date = db.Column(db.Date, nullable=True)
    expected_delivery = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default="open")
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship("Suppliers", back_populates="purchase_orders")
    items = db.relationship("PurchaseOrderItems", back_populates="purchase_order", lazy=True, cascade="all, delete-orphan")

    serialize_rules = ("-supplier.purchase_orders", "-items.purchase_order")

    def to_dict(self):
        return {
            "id": self.id,
            "po_number": self.po_number,
            "po_date": self.po_date.isoformat() if self.po_date else None,
            "supplier": self.supplier.to_dict() if self.supplier else None,
            "supplier_id": self.supplier_id,
            "required_date": self.required_date.isoformat() if self.required_date else None,
            "expected_delivery": self.expected_delivery.isoformat() if self.expected_delivery else None,
            "status": self.status,
            "total_amount": money_value(self.total_amount),
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PurchaseOrderItems(db.Model, SerializerMixin):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    item_description = db.Column(db.Text, nullable=False)
    quantity_ordered = db.Column(db.Float, nullable=False, default=1)
    quantity_received = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    line_total = db.Column(db.Numeric(12, 2), default=0)

    purchase_order = db.relationship("PurchaseOrders", back_populates="items")
    product = db.relationship("Products", back_populates="purchase_order_items")

    serialize_rules = ("-purchase_order.items", "-product.purchase_order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "product_id": self.product_id,
            "item_description": self.item_description,
            "quantity_ordered": self.quantity_ordered,
            "quantity_received": self.quantity_received,
            "unit_price": money_value(self.unit_price),
            "line_total": money_value(self.line_total),
        }


class StockTransactions(db.Model, SerializerMixin):
    __tablename__ = "stock_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)
    quantity_change = db.Column(db.Float, nullable=False)
    quantity_before = db.Column(db.Float, default=0)
    quantity_after = db.Column(db.Float, default=0)
    unit_cost = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text, nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Products", back_populates="stock_transactions")
    user = db.relationship("Users", back_populates="stock_transactions")

    serialize_rules = ("-product.stock_transactions", "-user.stock_transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_type": self.transaction_type,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "reference_number": self.reference_number,
            "quantity_change": self.quantity_change,
            "quantity_before": self.quantity_before,
            "quantity_after": self.quantity_after,
            "unit_cost": money_value(self.unit_cost),
            "notes": self.notes,
            "performed_by_id": self.performed_by_id,
            "performed_by": self.user.name if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Projects(db.Model, SerializerMixin):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(150), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    contract_value = db.Column(db.Numeric(12, 2), default=0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    assigned_engineer = db.Column(db.String(100), nullable=True)
    assigned_technicians = db.Column(db.String(200), nullable=True)
    materials_consumed = db.Column(db.Numeric(12, 2), default=0)
    invoices_raised = db.Column(db.Numeric(12, 2), default=0)
    payments_received = db.Column(db.Numeric(12, 2), default=0)
    profitability = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(50), default="planning")
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", back_populates="projects")

    serialize_rules = ("-customer.projects",)

    def to_dict(self):
        return {
            "id": self.id,
            "project_name": self.project_name,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "location": self.location,
            "contract_value": money_value(self.contract_value),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "assigned_engineer": self.assigned_engineer,
            "assigned_technicians": self.assigned_technicians,
            "materials_consumed": money_value(self.materials_consumed),
            "invoices_raised": money_value(self.invoices_raised),
            "payments_received": money_value(self.payments_received),
            "profitability": money_value(self.profitability),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VATSettings(db.Model, SerializerMixin):
    __tablename__ = "vat_settings"

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)
    is_exempt = db.Column(db.Boolean, default=False)
    vat_rate = db.Column(db.Float, default=0.16)
    description = db.Column(db.Text, nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    updated_by = db.relationship("Users", backref="vat_updates")

    serialize_rules = ("-updated_by.vat_updates",)

    def to_dict(self):
        return {
            "id": self.id,
            "category_name": self.category_name,
            "is_exempt": self.is_exempt,
            "vat_rate": self.vat_rate,
            "description": self.description,
            "updated_by_id": self.updated_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
class CompanySettings(db.Model, SerializerMixin):
    __tablename__ = "company_settings"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False, default="LAMPS91 Energies Ltd")
    tagline = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    whatsapp_number = db.Column(db.String(50), nullable=True)
    physical_address = db.Column(db.Text, nullable=True)
    postal_address = db.Column(db.String(100), nullable=True)
    kra_pin = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(100), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    
    # Brand colors (hex codes)
    primary_color = db.Column(db.String(20), default="#1E3A8A")  # Blue
    secondary_color = db.Column(db.String(20), default="#F59E0B")  # Gold
    text_color = db.Column(db.String(20), default="#000000")
    
    # Bank details for invoices
    bank_name = db.Column(db.String(100), nullable=True)
    bank_account_name = db.Column(db.String(100), nullable=True)
    bank_account_number = db.Column(db.String(50), nullable=True)
    bank_branch = db.Column(db.String(100), nullable=True)
    mpesa_paybill = db.Column(db.String(50), nullable=True)
    mpesa_account = db.Column(db.String(50), nullable=True)
    
    # Document settings
    quotation_validity_days = db.Column(db.Integer, default=30)
    invoice_due_days = db.Column(db.Integer, default=30)
    default_terms = db.Column(db.Text, nullable=True)
    
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    updated_by = db.relationship("Users", backref="company_settings_updates")

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "tagline": self.tagline,
            "email": self.email,
            "phone": self.phone,
            "whatsapp_number": self.whatsapp_number,
            "physical_address": self.physical_address,
            "postal_address": self.postal_address,
            "kra_pin": self.kra_pin,
            "website": self.website,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "text_color": self.text_color,
            "bank_name": self.bank_name,
            "bank_account_name": self.bank_account_name,
            "bank_account_number": self.bank_account_number,
            "bank_branch": self.bank_branch,
            "mpesa_paybill": self.mpesa_paybill,
            "mpesa_account": self.mpesa_account,
            "quotation_validity_days": self.quotation_validity_days,
            "invoice_due_days": self.invoice_due_days,
            "default_terms": self.default_terms,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ClientLPO(db.Model, SerializerMixin):
    __tablename__ = "client_lpos"

    id = db.Column(db.Integer, primary_key=True)
    lpo_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=False, unique=True)
    lpo_date = db.Column(db.Date, default=date.today)
    lpo_value = db.Column(db.Numeric(12, 2), default=0)
    lpo_document_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected
    notes = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customers", backref="client_lpos")
    quotation = db.relationship("Quotations", backref="client_lpo", uselist=False)
    approved_by = db.relationship("Users", backref="approved_lpos")

    serialize_rules = ("-customer.client_lpos", "-quotation.client_lpo", "-approved_by.approved_lpos")

    def to_dict(self):
        return {
            "id": self.id,
            "lpo_number": self.lpo_number,
            "customer_id": self.customer_id,
            "quotation_id": self.quotation_id,
            "lpo_date": self.lpo_date.isoformat() if self.lpo_date else None,
            "lpo_value": float(self.lpo_value or 0),
            "lpo_document_url": self.lpo_document_url,
            "status": self.status,
            "notes": self.notes,
            "approved_by_id": self.approved_by_id,
            "customer": self.customer.to_dict() if self.customer else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Requisitions(db.Model, SerializerMixin):
    __tablename__ = "requisitions"

    id = db.Column(db.Integer, primary_key=True)
    requisition_number = db.Column(db.String(50), unique=True, nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    justification = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected, converted_to_po
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    requested_by = db.relationship("Users", foreign_keys=[requested_by_id], backref="requisitions")
    approved_by = db.relationship("Users", foreign_keys=[approved_by_id], backref="approved_requisitions")
    purchase_order = db.relationship("PurchaseOrders", backref="requisition", uselist=False)
    items = db.relationship("RequisitionItems", back_populates="requisition", lazy=True, cascade="all, delete-orphan")

    serialize_rules = (
        "-requested_by.requisitions",
        "-approved_by.approved_requisitions",
        "-purchase_order.requisition",
        "-items.requisition",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "requisition_number": self.requisition_number,
            "requested_by_id": self.requested_by_id,
            "requested_by_name": self.requested_by.name if self.requested_by else None,
            "department": self.department,
            "justification": self.justification,
            "status": self.status,
            "approved_by_id": self.approved_by_id,
            "approved_by_name": self.approved_by.name if self.approved_by else None,
            "purchase_order_id": self.purchase_order_id,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RequisitionItems(db.Model, SerializerMixin):
    __tablename__ = "requisition_items"

    id = db.Column(db.Integer, primary_key=True)
    requisition_id = db.Column(db.Integer, db.ForeignKey("requisitions.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    item_description = db.Column(db.Text, nullable=False)
    quantity_requested = db.Column(db.Float, nullable=False, default=1)
    estimated_unit_price = db.Column(db.Numeric(12, 2), default=0)
    line_total = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    requisition = db.relationship("Requisitions", back_populates="items")
    product = db.relationship("Products", backref="requisition_items")

    serialize_rules = ("-requisition.items", "-product.requisition_items")

    def to_dict(self):
        return {
            "id": self.id,
            "requisition_id": self.requisition_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "item_description": self.item_description,
            "quantity_requested": float(self.quantity_requested or 0),
            "estimated_unit_price": float(self.estimated_unit_price or 0),
            "line_total": float(self.line_total or 0),
            "notes": self.notes,
        }


class SupplierInvoices(db.Model, SerializerMixin):
    __tablename__ = "supplier_invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)  # Supplier's invoice number
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    invoice_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=True)
    reference = db.Column(db.String(100), nullable=True)
    sub_total = db.Column(db.Numeric(12, 2), default=0)
    vat_amount = db.Column(db.Numeric(12, 2), default=0)
    invoice_total = db.Column(db.Numeric(12, 2), default=0)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)
    balance_due = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(50), default="pending")  # pending, partial_paid, paid
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = db.relationship("Suppliers", backref="supplier_invoices")
    purchase_order = db.relationship("PurchaseOrders", backref="supplier_invoice", uselist=False)
    items = db.relationship("SupplierInvoiceItems", back_populates="invoice", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("SupplierPayments", back_populates="supplier_invoice", lazy=True, cascade="all, delete-orphan")

    serialize_rules = (
        "-supplier.supplier_invoices",
        "-purchase_order.supplier_invoice",
        "-items.invoice",
        "-payments.supplier_invoice",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.supplier_name if self.supplier else None,
            "purchase_order_id": self.purchase_order_id,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reference": self.reference,
            "sub_total": float(self.sub_total or 0),
            "vat_amount": float(self.vat_amount or 0),
            "invoice_total": float(self.invoice_total or 0),
            "amount_paid": float(self.amount_paid or 0),
            "balance_due": float(self.balance_due or 0),
            "status": self.status,
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
            "payments": [p.to_dict() for p in self.payments],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SupplierInvoiceItems(db.Model, SerializerMixin):
    __tablename__ = "supplier_invoice_items"

    id = db.Column(db.Integer, primary_key=True)
    supplier_invoice_id = db.Column(db.Integer, db.ForeignKey("supplier_invoices.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    item_description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    vat_status = db.Column(db.String(20), default="vatable")  # vatable or exempt
    line_total = db.Column(db.Numeric(12, 2), default=0)

    # Relationships
    invoice = db.relationship("SupplierInvoices", back_populates="items")
    product = db.relationship("Products", backref="supplier_invoice_items")

    serialize_rules = ("-invoice.items", "-product.supplier_invoice_items")

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_invoice_id": self.supplier_invoice_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "item_description": self.item_description,
            "quantity": float(self.quantity or 0),
            "unit_price": float(self.unit_price or 0),
            "vat_status": self.vat_status,
            "line_total": float(self.line_total or 0),
        }


class SupplierPayments(db.Model, SerializerMixin):
    __tablename__ = "supplier_payments"

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_invoice_id = db.Column(db.Integer, db.ForeignKey("supplier_invoices.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, bank_transfer, cheque, mpesa
    transaction_reference = db.Column(db.String(100), nullable=True)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False)
    balance_due = db.Column(db.Numeric(12, 2), default=0)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    supplier_invoice = db.relationship("SupplierInvoices", back_populates="payments")
    supplier = db.relationship("Suppliers", backref="supplier_payments")
    paid_by = db.relationship("Users", backref="supplier_payments_made")

    serialize_rules = ("-supplier_invoice.payments", "-supplier.supplier_payments", "-paid_by.supplier_payments_made")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_number": self.payment_number,
            "supplier_invoice_id": self.supplier_invoice_id,
            "supplier_id": self.supplier_id,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "transaction_reference": self.transaction_reference,
            "amount_paid": float(self.amount_paid or 0),
            "balance_due": float(self.balance_due or 0),
            "paid_by_id": self.paid_by_id,
            "paid_by_name": self.paid_by.name if self.paid_by else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }