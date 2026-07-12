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

class SalesOrders(db.Model, SerializerMixin):
    __tablename__ = "sales_orders"

    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(50), unique=True, nullable=False)
    so_date = db.Column(db.Date, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=True)
    project_name = db.Column(db.String(150), nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    inventory_reserved = db.Column(db.Boolean, default=False)
    installation_team = db.Column(db.String(200), nullable=True)  # Comma-separated names or team ID
    status = db.Column(db.String(50), default="pending")  # pending, approved, delivered, installed, completed
    total_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customers", backref="sales_orders")
    quotation = db.relationship("Quotations", backref="sales_order", uselist=False)
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
            "total_amount": self.total_amount,
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
    sales_order_id = db.Column(db.Integer, db.ForeignKey("sales_orders.id"), nullable=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotations.id"), nullable=True)
    reference = db.Column(db.String(100), nullable=True)  # Quote or SO reference
    
    # Financial fields
    sub_total = db.Column(db.Float, default=0)
    vat_exempt_total = db.Column(db.Float, default=0)
    vatable_total = db.Column(db.Float, default=0)
    vat_amount = db.Column(db.Float, default=0)
    invoice_total = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    balance_due = db.Column(db.Float, default=0)
    
    status = db.Column(db.String(50), default="pending")  # pending, paid, overdue, cancelled
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customers", backref="invoices")
    sales_order = db.relationship("SalesOrders", back_populates="invoice")
    quotation = db.relationship("Quotations", backref="invoice", uselist=False)
    receipts = db.relationship("Receipts", back_populates="invoice", lazy=True, cascade="all, delete-orphan")
    invoice_items = db.relationship("InvoiceItems", back_populates="invoice", lazy=True, cascade="all, delete-orphan")

    serialize_rules = ("-customer.invoices", "-sales_order.invoice", "-quotation.invoice", "-receipts.invoice", "-invoice_items.invoice")

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
            "sub_total": self.sub_total,
            "vat_exempt_total": self.vat_exempt_total,
            "vatable_total": self.vatable_total,
            "vat_amount": self.vat_amount,
            "invoice_total": self.invoice_total,
            "amount_paid": self.amount_paid,
            "balance_due": self.balance_due,
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
    unit_price = db.Column(db.Float, nullable=False, default=0)
    discount = db.Column(db.Float, default=0)
    vat_status = db.Column(db.String(20), nullable=False, default="vatable")
    line_total = db.Column(db.Float, default=0)

    invoice = db.relationship("Invoices", back_populates="invoice_items")
    product = db.relationship("Products", backref="invoice_items")

    serialize_rules = ("-invoice.invoice_items", "-product.invoice_items")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "product_id": self.product_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount": self.discount,
            "vat_status": self.vat_status,
            "line_total": self.line_total,
        }

class Receipts(db.Model, SerializerMixin):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    receipt_date = db.Column(db.Date, default=date.today)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=True)
    
    payment_method = db.Column(db.String(50), nullable=False)  # cash, bank_transfer, cheque, mpesa
    transaction_reference = db.Column(db.String(100), nullable=True)  # M-Pesa code, cheque number, etc.
    amount_received = db.Column(db.Float, nullable=False)
    outstanding_balance = db.Column(db.Float, default=0)
    
    received_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship("Customers", backref="receipts")
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
            "amount_received": self.amount_received,
            "outstanding_balance": self.outstanding_balance,
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
    products_supplied = db.Column(db.Text, nullable=True)  # Comma-separated or JSON
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
    status = db.Column(db.String(50), default="open")  # open, partially_received, closed
    total_amount = db.Column(db.Float, default=0)
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
            "total_amount": self.total_amount,
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
    unit_price = db.Column(db.Float, nullable=False, default=0)
    line_total = db.Column(db.Float, default=0)

    purchase_order = db.relationship("PurchaseOrders", back_populates="items")
    product = db.relationship("Products", backref="purchase_order_items")

    serialize_rules = ("-purchase_order.items", "-product.purchase_order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "product_id": self.product_id,
            "item_description": self.item_description,
            "quantity_ordered": self.quantity_ordered,
            "quantity_received": self.quantity_received,
            "unit_price": self.unit_price,
            "line_total": self.line_total,
        }
    

class StockTransactions(db.Model, SerializerMixin):
    __tablename__ = "stock_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50), nullable=False)  # grn, adjustment, transfer, issue, return, count
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)  # GRN number, PO number, etc.
    quantity_change = db.Column(db.Float, nullable=False)  # Positive for additions, negative for deductions
    quantity_before = db.Column(db.Float, default=0)
    quantity_after = db.Column(db.Float, default=0)
    unit_cost = db.Column(db.Float, default=0)  # Cost per unit at time of transaction
    notes = db.Column(db.Text, nullable=True)
    performed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Products", backref="stock_transactions")
    user = db.relationship("Users", backref="stock_transactions")

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
            "unit_cost": self.unit_cost,
            "notes": self.notes,
            "performed_by": self.user.name if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    

class Projects(db.Model, SerializerMixin):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(150), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    contract_value = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    assigned_engineer = db.Column(db.String(100), nullable=True)
    assigned_technicians = db.Column(db.String(200), nullable=True)  # Comma-separated names
    materials_consumed = db.Column(db.Float, default=0)  # Total cost of materials
    invoices_raised = db.Column(db.Float, default=0)
    payments_received = db.Column(db.Float, default=0)
    profitability = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="planning")  # planning, active, completed
    notes = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customers", backref="projects")

    serialize_rules = ("-customer.projects",)

    def to_dict(self):
        return {
            "id": self.id,
            "project_name": self.project_name,
            "customer": self.customer.to_dict() if self.customer else None,
            "customer_id": self.customer_id,
            "location": self.location,
            "contract_value": self.contract_value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "assigned_engineer": self.assigned_engineer,
            "assigned_technicians": self.assigned_technicians,
            "materials_consumed": self.materials_consumed,
            "invoices_raised": self.invoices_raised,
            "payments_received": self.payments_received,
            "profitability": self.profitability,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }