from datetime import datetime
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Customers, Products, Quotations, QuotationItems, SalesOrders, Invoices, InvoiceItems, Receipts, Suppliers, PurchaseOrders, PurchaseOrderItems, StockTransactions, Projects

VAT_RATE = 0.16
VAT_EXEMPT_CATEGORIES = {"solar panels", "inverters", "batteries"}


def clean_text(value):
    if value is None:
        return None
    return str(value).strip()


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def get_vat_status(category, vat_status=None):
    if vat_status:
        return clean_text(vat_status).lower()

    if category and clean_text(category).lower() in VAT_EXEMPT_CATEGORIES:
        return "exempt"

    return "vatable"


def calculate_quote_totals(quotation):
    sub_total = 0
    vat_exempt_total = 0
    vatable_total = 0

    for item in quotation.items:
        gross_total = item.quantity * item.unit_price
        item.line_total = gross_total - item.discount
        sub_total += item.line_total

        if item.vat_status == "exempt":
            vat_exempt_total += item.line_total
        else:
            vatable_total += item.line_total

    quotation.sub_total = sub_total
    quotation.vat_exempt_total = vat_exempt_total
    quotation.vatable_total = vatable_total
    quotation.vat_amount = vatable_total * VAT_RATE
    quotation.grand_total = sub_total + quotation.vat_amount


class Customer(Resource):
    def get(self):
        customers = Customers.query.filter_by(deleted_at=None).all()
        return [customer.to_dict() for customer in customers], 200

    def post(self):
        data = request.get_json()
        required_fields = {"customer_name", "phone"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 422

        new_customer = Customers(
            customer_name=clean_text(data.get("customer_name")),
            contact_person=clean_text(data.get("contact_person")),
            phone=clean_text(data.get("phone")),
            email=clean_text(data.get("email")),
            kra_pin=clean_text(data.get("kra_pin")),
            physical_address=clean_text(data.get("physical_address")),
            county=clean_text(data.get("county")),
            customer_type=clean_text(data.get("customer_type")) or "commercial",
        )

        db.session.add(new_customer)
        db.session.commit()

        return new_customer.to_dict(), 201


class CustomerResource(Resource):
    def get(self, customer_id):
        customer = Customers.query.filter_by(id=customer_id, deleted_at=None).first()

        if not customer:
            return {"error": "Customer not found!"}, 404

        return customer.to_dict(), 200

    def patch(self, customer_id):
        customer = Customers.query.filter_by(id=customer_id, deleted_at=None).first()

        if not customer:
            return {"error": "Customer not found!"}, 404

        data = request.get_json()

        for field in [
            "customer_name",
            "contact_person",
            "phone",
            "email",
            "kra_pin",
            "physical_address",
            "county",
            "customer_type",
        ]:
            if field in data:
                setattr(customer, field, clean_text(data.get(field)))

        db.session.commit()

        return customer.to_dict(), 200

    def delete(self, customer_id):
        customer = Customers.query.filter_by(id=customer_id, deleted_at=None).first()

        if not customer:
            return {"error": "Customer not found!"}, 404

        customer.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Customer deleted successfully!"}, 200


class Product(Resource):
    def get(self):
        products = Products.query.filter_by(deleted_at=None).all()
        return [product.to_dict() for product in products], 200

    def post(self):
        data = request.get_json()
        required_fields = {"item_code", "product_name", "category", "selling_price"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 422

        if Products.query.filter_by(item_code=clean_text(data.get("item_code"))).first():
            return {"error": "Item code already exists!"}, 400

        try:
            selling_price = float(data.get("selling_price"))
            buying_price = float(data.get("buying_price", 0))
            current_stock = int(data.get("current_stock", 0))
            reorder_level = int(data.get("reorder_level", 0))

        except ValueError:
            return {"error": "Prices and stock values must be valid numbers!"}, 400

        category = clean_text(data.get("category"))
        new_product = Products(
            item_code=clean_text(data.get("item_code")),
            product_name=clean_text(data.get("product_name")),
            category=category,
            brand=clean_text(data.get("brand")),
            unit=clean_text(data.get("unit")) or "pcs",
            buying_price=buying_price,
            selling_price=selling_price,
            vat_status=get_vat_status(category, data.get("vat_status")),
            current_stock=current_stock,
            reorder_level=reorder_level,
        )

        db.session.add(new_product)
        db.session.commit()

        return new_product.to_dict(), 201


class ProductResource(Resource):
    def get(self, product_id):
        product = Products.query.filter_by(id=product_id, deleted_at=None).first()

        if not product:
            return {"error": "Product not found!"}, 404

        return product.to_dict(), 200

    def patch(self, product_id):
        product = Products.query.filter_by(id=product_id, deleted_at=None).first()

        if not product:
            return {"error": "Product not found!"}, 404

        data = request.get_json()

        text_fields = ["item_code", "product_name", "category", "brand", "unit", "vat_status"]
        for field in text_fields:
            if field in data:
                setattr(product, field, clean_text(data.get(field)))

        numeric_fields = ["buying_price", "selling_price"]
        for field in numeric_fields:
            if field in data:
                setattr(product, field, float(data.get(field)))

        stock_fields = ["current_stock", "reorder_level"]
        for field in stock_fields:
            if field in data:
                setattr(product, field, int(data.get(field)))

        db.session.commit()

        return product.to_dict(), 200

    def delete(self, product_id):
        product = Products.query.filter_by(id=product_id, deleted_at=None).first()

        if not product:
            return {"error": "Product not found!"}, 404

        product.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Product deleted successfully!"}, 200


class Quotation(Resource):
    def get(self):
        quotations = Quotations.query.filter_by(deleted_at=None).all()
        return [quotation.to_dict() for quotation in quotations], 200
    
    def post(self):
        data = request.get_json()
        required_fields = {"quote_number", "customer_id", "items"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 422

        customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
        if not customer:
            return {"error": "Customer not found!"}, 404

        if Quotations.query.filter_by(quote_number=clean_text(data.get("quote_number"))).first():
            return {"error": "Quote number already exists!"}, 400

        if not data.get("items"):
            return {"error": "A quotation must have at least one item!"}, 400

        quotation = Quotations(
            quote_number=clean_text(data.get("quote_number")),
            quote_date=parse_date(data.get("quote_date")) or datetime.utcnow().date(),
            valid_until=parse_date(data.get("valid_until")),
            customer_id=customer.id,
            project_name=clean_text(data.get("project_name")),
            site_location=clean_text(data.get("site_location")),
            terms_conditions=clean_text(data.get("terms_conditions")),
            authorized_by=clean_text(data.get("authorized_by")),
        )

        db.session.add(quotation)
        db.session.flush()

        for item in data.get("items", []):
            product = None
            product_id = item.get("product_id")
            if product_id:
                product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                if not product:
                    return {"error": f"Product with id {product_id} not found!"}, 404

            item_description = clean_text(item.get("item_description"))
            if not item_description and not product:
                return {"error": "Each custom quotation item needs an item_description!"}, 422

            try:
                quantity = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", product.selling_price if product else 0))
                discount = float(item.get("discount", 0))
            except ValueError:
                return {"error": "Quantity, unit price, and discount must be valid numbers!"}, 400

            quote_item = QuotationItems(
                quotation_id=quotation.id,
                product_id=product.id if product else None,
                item_description=item_description or product.product_name,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                vat_status=get_vat_status(product.category if product else None, item.get("vat_status") or (product.vat_status if product else None)),
            )
            db.session.add(quote_item)

        db.session.flush()
        calculate_quote_totals(quotation)
        db.session.commit()

        return quotation.to_dict(), 201
    
class QuotationResource(Resource):
    def get(self, quotation_id):
        quotation = Quotations.query.filter_by(id=quotation_id, deleted_at=None).first()

        if not quotation:
            return {"error": "Quotation not found!"}, 404

        return quotation.to_dict(), 200

    def delete(self, quotation_id):
        quotation = Quotations.query.filter_by(id=quotation_id, deleted_at=None).first()

        if not quotation:
            return {"error": "Quotation not found!"}, 404

        quotation.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Quotation deleted successfully!"}, 200


# ==================== SALES ORDER RESOURCES ====================

class SalesOrder(Resource):
    def get(self):
        orders = SalesOrders.query.filter_by(deleted_at=None).all()
        return [order.to_dict() for order in orders], 200

    def post(self):
        data = request.get_json()
        required_fields = {"customer_id"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 422

        customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
        if not customer:
            return {"error": "Customer not found!"}, 404

        # Generate SO number if not provided
        if not data.get("so_number"):
            last_order = SalesOrders.query.order_by(SalesOrders.id.desc()).first()
            last_num = int(last_order.so_number.split("-")[1]) if last_order and last_order.so_number else 0
            data["so_number"] = f"SO-{last_num + 1:04d}"

        order = SalesOrders(
            so_number=clean_text(data.get("so_number")),
            so_date=parse_date(data.get("so_date")) or datetime.utcnow().date(),
            customer_id=customer.id,
            quotation_id=data.get("quotation_id"),
            project_name=clean_text(data.get("project_name")),
            delivery_date=parse_date(data.get("delivery_date")),
            inventory_reserved=data.get("inventory_reserved", False),
            installation_team=clean_text(data.get("installation_team")),
            status=clean_text(data.get("status")) or "pending",
            total_amount=float(data.get("total_amount", 0)),
            notes=clean_text(data.get("notes")),
        )

        db.session.add(order)
        db.session.commit()

        return order.to_dict(), 201


class SalesOrderResource(Resource):
    def get(self, order_id):
        order = SalesOrders.query.filter_by(id=order_id, deleted_at=None).first()

        if not order:
            return {"error": "Sales order not found!"}, 404

        return order.to_dict(), 200

    def patch(self, order_id):
        order = SalesOrders.query.filter_by(id=order_id, deleted_at=None).first()

        if not order:
            return {"error": "Sales order not found!"}, 404

        data = request.get_json()

        text_fields = ["so_number", "project_name", "installation_team", "status", "notes"]
        for field in text_fields:
            if field in data:
                setattr(order, field, clean_text(data.get(field)))

        date_fields = ["so_date", "delivery_date"]
        for field in date_fields:
            if field in data:
                setattr(order, field, parse_date(data.get(field)))

        if "inventory_reserved" in data:
            order.inventory_reserved = bool(data.get("inventory_reserved"))

        if "total_amount" in data:
            order.total_amount = float(data.get("total_amount"))

        if "customer_id" in data:
            customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
            if not customer:
                return {"error": "Customer not found!"}, 404
            order.customer_id = customer.id

        if "quotation_id" in data:
            order.quotation_id = data.get("quotation_id")

        db.session.commit()

        return order.to_dict(), 200

    def delete(self, order_id):
        order = SalesOrders.query.filter_by(id=order_id, deleted_at=None).first()

        if not order:
            return {"error": "Sales order not found!"}, 404

        order.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Sales order deleted successfully!"}, 200


# ==================== INVOICE RESOURCES ====================

def calculate_invoice_totals(invoice):
    sub_total = 0
    vat_exempt_total = 0
    vatable_total = 0

    for item in invoice.invoice_items:
        gross_total = item.quantity * item.unit_price
        item.line_total = gross_total - item.discount
        sub_total += item.line_total

        if item.vat_status == "exempt":
            vat_exempt_total += item.line_total
        else:
            vatable_total += item.line_total

    invoice.sub_total = sub_total
    invoice.vat_exempt_total = vat_exempt_total
    invoice.vatable_total = vatable_total
    invoice.vat_amount = vatable_total * VAT_RATE
    invoice.invoice_total = sub_total + invoice.vat_amount
    invoice.balance_due = invoice.invoice_total - (invoice.amount_paid or 0)


class Invoice(Resource):
    def get(self):
        invoices = Invoices.query.filter_by(deleted_at=None).all()
        return [invoice.to_dict() for invoice in invoices], 200

    def post(self):
        data = request.get_json()
        required_fields = {"customer_id", "items"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
        if not customer:
            return {"error": "Customer not found!"}, 404

        if not data.get("items"):
            return {"error": "An invoice must have at least one item!"}, 400

        # Generate invoice number if not provided
        if not data.get("invoice_number"):
            last_invoice = Invoices.query.order_by(Invoices.id.desc()).first()
            last_num = int(last_invoice.invoice_number.split("-")[1]) if last_invoice and last_invoice.invoice_number else 0
            data["invoice_number"] = f"INV-{last_num + 1:04d}"

        invoice = Invoices(
            invoice_number=clean_text(data.get("invoice_number")),
            invoice_date=parse_date(data.get("invoice_date")) or datetime.utcnow().date(),
            due_date=parse_date(data.get("due_date")),
            customer_id=customer.id,
            sales_order_id=data.get("sales_order_id"),
            quotation_id=data.get("quotation_id"),
            reference=clean_text(data.get("reference")),
            amount_paid=float(data.get("amount_paid", 0)),
            status=clean_text(data.get("status")) or "pending",
            notes=clean_text(data.get("notes")),
        )

        db.session.add(invoice)
        db.session.flush()

        for item in data.get("items", []):
            product = None
            product_id = item.get("product_id")
            if product_id:
                product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                if not product:
                    return {"error": f"Product with id {product_id} not found!"}, 404

            item_description = clean_text(item.get("item_description"))
            if not item_description and not product:
                return {"error": "Each invoice item needs an item_description!"}, 422

            try:
                quantity = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", product.selling_price if product else 0))
                discount = float(item.get("discount", 0))
            except ValueError:
                return {"error": "Quantity, unit price, and discount must be valid numbers!"}, 400

            invoice_item = InvoiceItems(
                invoice_id=invoice.id,
                product_id=product.id if product else None,
                item_description=item_description or product.product_name,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                vat_status=get_vat_status(product.category if product else None, item.get("vat_status") or (product.vat_status if product else None)),
            )
            db.session.add(invoice_item)

        db.session.flush()
        calculate_invoice_totals(invoice)
        db.session.commit()

        return invoice.to_dict(), 201


class InvoiceResource(Resource):
    def get(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()

        if not invoice:
            return {"error": "Invoice not found!"}, 404

        return invoice.to_dict(), 200

    def patch(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()

        if not invoice:
            return {"error": "Invoice not found!"}, 404

        data = request.get_json()

        text_fields = ["invoice_number", "reference", "status", "notes"]
        for field in text_fields:
            if field in data:
                setattr(invoice, field, clean_text(data.get(field)))

        date_fields = ["invoice_date", "due_date"]
        for field in date_fields:
            if field in data:
                setattr(invoice, field, parse_date(data.get(field)))

        numeric_fields = ["amount_paid"]
        for field in numeric_fields:
            if field in data:
                setattr(invoice, field, float(data.get(field)))

        if "customer_id" in data:
            customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
            if not customer:
                return {"error": "Customer not found!"}, 404
            invoice.customer_id = customer.id

        if "sales_order_id" in data:
            invoice.sales_order_id = data.get("sales_order_id")

        if "quotation_id" in data:
            invoice.quotation_id = data.get("quotation_id")

        # Recalculate totals if items changed
        if "items" in data:
            # Remove existing items
            InvoiceItems.query.filter_by(invoice_id=invoice.id).delete()

            # Add new items
            for item in data.get("items", []):
                product = None
                product_id = item.get("product_id")
                if product_id:
                    product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                    if not product:
                        return {"error": f"Product with id {product_id} not found!"}, 404

                item_description = clean_text(item.get("item_description"))
                if not item_description and not product:
                    return {"error": "Each invoice item needs an item_description!"}, 422

                try:
                    quantity = float(item.get("quantity", 1))
                    unit_price = float(item.get("unit_price", product.selling_price if product else 0))
                    discount = float(item.get("discount", 0))
                except ValueError:
                    return {"error": "Quantity, unit price, and discount must be valid numbers!"}, 400

                invoice_item = InvoiceItems(
                    invoice_id=invoice.id,
                    product_id=product.id if product else None,
                    item_description=item_description or product.product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount=discount,
                    vat_status=get_vat_status(product.category if product else None, item.get("vat_status") or (product.vat_status if product else None)),
                )
                db.session.add(invoice_item)

            db.session.flush()
            calculate_invoice_totals(invoice)

        db.session.commit()

        return invoice.to_dict(), 200

    def delete(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()

        if not invoice:
            return {"error": "Invoice not found!"}, 404

        invoice.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Invoice deleted successfully!"}, 200


# ==================== RECEIPT RESOURCES ====================

class Receipt(Resource):
    def get(self):
        receipts = Receipts.query.filter_by(deleted_at=None).all()
        return [receipt.to_dict() for receipt in receipts], 200

    def post(self):
        data = request.get_json()
        required_fields = {"customer_id", "payment_method", "amount_received"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
        if not customer:
            return {"error": "Customer not found!"}, 404

        # Generate receipt number if not provided
        if not data.get("receipt_number"):
            last_receipt = Receipts.query.order_by(Receipts.id.desc()).first()
            last_num = int(last_receipt.receipt_number.split("-")[1]) if last_receipt and last_receipt.receipt_number else 0
            data["receipt_number"] = f"REC-{last_num + 1:04d}"

        try:
            amount_received = float(data.get("amount_received"))
        except ValueError:
            return {"error": "Amount received must be a valid number!"}, 400

        receipt = Receipts(
            receipt_number=clean_text(data.get("receipt_number")),
            receipt_date=parse_date(data.get("receipt_date")) or datetime.utcnow().date(),
            customer_id=customer.id,
            invoice_id=data.get("invoice_id"),
            payment_method=clean_text(data.get("payment_method")),
            transaction_reference=clean_text(data.get("transaction_reference")),
            amount_received=amount_received,
            outstanding_balance=float(data.get("outstanding_balance", 0)),
            received_by=clean_text(data.get("received_by")),
            notes=clean_text(data.get("notes")),
        )

        db.session.add(receipt)
        db.session.commit()

        # Update invoice balance if invoice_id is provided
        if data.get("invoice_id"):
            invoice = Invoices.query.get(data.get("invoice_id"))
            if invoice:
                invoice.amount_paid = (invoice.amount_paid or 0) + amount_received
                invoice.balance_due = invoice.invoice_total - invoice.amount_paid
                if invoice.balance_due <= 0:
                    invoice.status = "paid"
                db.session.commit()

        # Update customer outstanding balance
        if customer:
            customer.outstanding_balance = (customer.outstanding_balance or 0) - amount_received
            db.session.commit()

        return receipt.to_dict(), 201


class ReceiptResource(Resource):
    def get(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()

        if not receipt:
            return {"error": "Receipt not found!"}, 404

        return receipt.to_dict(), 200

    def patch(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()

        if not receipt:
            return {"error": "Receipt not found!"}, 404

        data = request.get_json()

        text_fields = ["receipt_number", "payment_method", "transaction_reference", "received_by", "notes"]
        for field in text_fields:
            if field in data:
                setattr(receipt, field, clean_text(data.get(field)))

        date_fields = ["receipt_date"]
        for field in date_fields:
            if field in data:
                setattr(receipt, field, parse_date(data.get(field)))

        if "amount_received" in data:
            receipt.amount_received = float(data.get("amount_received"))

        if "outstanding_balance" in data:
            receipt.outstanding_balance = float(data.get("outstanding_balance"))

        if "customer_id" in data:
            customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
            if not customer:
                return {"error": "Customer not found!"}, 404
            receipt.customer_id = customer.id

        if "invoice_id" in data:
            receipt.invoice_id = data.get("invoice_id")

        db.session.commit()

        return receipt.to_dict(), 200

    def delete(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()

        if not receipt:
            return {"error": "Receipt not found!"}, 404

        receipt.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Receipt deleted successfully!"}, 200


# ==================== SUPPLIER RESOURCES ====================

class Supplier(Resource):
    def get(self):
        suppliers = Suppliers.query.filter_by(deleted_at=None).all()
        return [supplier.to_dict() for supplier in suppliers], 200

    def post(self):
        data = request.get_json()
        required_fields = {"supplier_name", "phone"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        supplier = Suppliers(
            supplier_name=clean_text(data.get("supplier_name")),
            contact_person=clean_text(data.get("contact_person")),
            phone=clean_text(data.get("phone")),
            email=clean_text(data.get("email")),
            kra_pin=clean_text(data.get("kra_pin")),
            physical_address=clean_text(data.get("physical_address")),
            county=clean_text(data.get("county")),
            products_supplied=clean_text(data.get("products_supplied")),
            outstanding_orders=int(data.get("outstanding_orders", 0)),
            is_active=data.get("is_active", True),
        )

        db.session.add(supplier)
        db.session.commit()

        return supplier.to_dict(), 201


class SupplierResource(Resource):
    def get(self, supplier_id):
        supplier = Suppliers.query.filter_by(id=supplier_id, deleted_at=None).first()

        if not supplier:
            return {"error": "Supplier not found!"}, 404

        return supplier.to_dict(), 200

    def patch(self, supplier_id):
        supplier = Suppliers.query.filter_by(id=supplier_id, deleted_at=None).first()

        if not supplier:
            return {"error": "Supplier not found!"}, 404

        data = request.get_json()

        text_fields = ["supplier_name", "contact_person", "phone", "email", "kra_pin", "physical_address", "county", "products_supplied"]
        for field in text_fields:
            if field in data:
                setattr(supplier, field, clean_text(data.get(field)))

        if "outstanding_orders" in data:
            supplier.outstanding_orders = int(data.get("outstanding_orders"))

        if "is_active" in data:
            supplier.is_active = bool(data.get("is_active"))

        db.session.commit()

        return supplier.to_dict(), 200

    def delete(self, supplier_id):
        supplier = Suppliers.query.filter_by(id=supplier_id, deleted_at=None).first()

        if not supplier:
            return {"error": "Supplier not found!"}, 404

        supplier.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Supplier deleted successfully!"}, 200


# ==================== PURCHASE ORDER RESOURCES ====================

class PurchaseOrder(Resource):
    def get(self):
        purchase_orders = PurchaseOrders.query.filter_by(deleted_at=None).all()
        return [po.to_dict() for po in purchase_orders], 200

    def post(self):
        data = request.get_json()
        required_fields = {"supplier_id", "items"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        supplier = Suppliers.query.filter_by(id=data.get("supplier_id"), deleted_at=None).first()
        if not supplier:
            return {"error": "Supplier not found!"}, 404

        if not data.get("items"):
            return {"error": "A purchase order must have at least one item!"}, 400

        # Generate PO number if not provided
        if not data.get("po_number"):
            last_po = PurchaseOrders.query.order_by(PurchaseOrders.id.desc()).first()
            last_num = int(last_po.po_number.split("-")[1]) if last_po and last_po.po_number else 0
            data["po_number"] = f"PO-{last_num + 1:04d}"

        po = PurchaseOrders(
            po_number=clean_text(data.get("po_number")),
            po_date=parse_date(data.get("po_date")) or datetime.utcnow().date(),
            supplier_id=supplier.id,
            required_date=parse_date(data.get("required_date")),
            expected_delivery=parse_date(data.get("expected_delivery")),
            status=clean_text(data.get("status")) or "open",
            total_amount=float(data.get("total_amount", 0)),
            notes=clean_text(data.get("notes")),
        )

        db.session.add(po)
        db.session.flush()

        total = 0
        for item in data.get("items", []):
            product = None
            product_id = item.get("product_id")
            if product_id:
                product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                if not product:
                    return {"error": f"Product with id {product_id} not found!"}, 404

            item_description = clean_text(item.get("item_description"))
            if not item_description and not product:
                return {"error": "Each purchase order item needs an item_description!"}, 422

            try:
                quantity_ordered = float(item.get("quantity_ordered", 1))
                unit_price = float(item.get("unit_price", 0))
            except ValueError:
                return {"error": "Quantity and unit price must be valid numbers!"}, 400

            line_total = quantity_ordered * unit_price
            total += line_total

            po_item = PurchaseOrderItems(
                purchase_order_id=po.id,
                product_id=product.id if product else None,
                item_description=item_description or product.product_name,
                quantity_ordered=quantity_ordered,
                quantity_received=float(item.get("quantity_received", 0)),
                unit_price=unit_price,
                line_total=line_total,
            )
            db.session.add(po_item)

        po.total_amount = total
        db.session.commit()

        return po.to_dict(), 201


class PurchaseOrderResource(Resource):
    def get(self, po_id):
        po = PurchaseOrders.query.filter_by(id=po_id, deleted_at=None).first()

        if not po:
            return {"error": "Purchase order not found!"}, 404

        return po.to_dict(), 200

    def patch(self, po_id):
        po = PurchaseOrders.query.filter_by(id=po_id, deleted_at=None).first()

        if not po:
            return {"error": "Purchase order not found!"}, 404

        data = request.get_json()

        text_fields = ["po_number", "status", "notes"]
        for field in text_fields:
            if field in data:
                setattr(po, field, clean_text(data.get(field)))

        date_fields = ["po_date", "required_date", "expected_delivery"]
        for field in date_fields:
            if field in data:
                setattr(po, field, parse_date(data.get(field)))

        if "total_amount" in data:
            po.total_amount = float(data.get("total_amount"))

        if "supplier_id" in data:
            supplier = Suppliers.query.filter_by(id=data.get("supplier_id"), deleted_at=None).first()
            if not supplier:
                return {"error": "Supplier not found!"}, 404
            po.supplier_id = supplier.id

        if "items" in data:
            PurchaseOrderItems.query.filter_by(purchase_order_id=po.id).delete()
            total = 0

            for item in data.get("items", []):
                product = None
                product_id = item.get("product_id")
                if product_id:
                    product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                    if not product:
                        return {"error": f"Product with id {product_id} not found!"}, 404

                item_description = clean_text(item.get("item_description"))
                if not item_description and not product:
                    return {"error": "Each purchase order item needs an item_description!"}, 422

                try:
                    quantity_ordered = float(item.get("quantity_ordered", 1))
                    unit_price = float(item.get("unit_price", 0))
                except ValueError:
                    return {"error": "Quantity and unit price must be valid numbers!"}, 400

                line_total = quantity_ordered * unit_price
                total += line_total

                po_item = PurchaseOrderItems(
                    purchase_order_id=po.id,
                    product_id=product.id if product else None,
                    item_description=item_description or product.product_name,
                    quantity_ordered=quantity_ordered,
                    quantity_received=float(item.get("quantity_received", 0)),
                    unit_price=unit_price,
                    line_total=line_total,
                )
                db.session.add(po_item)

            po.total_amount = total

        db.session.commit()

        return po.to_dict(), 200

    def delete(self, po_id):
        po = PurchaseOrders.query.filter_by(id=po_id, deleted_at=None).first()

        if not po:
            return {"error": "Purchase order not found!"}, 404

        po.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Purchase order deleted successfully!"}, 200


# ==================== STOCK TRANSACTION RESOURCES ====================

class StockTransaction(Resource):
    def get(self):
        transactions = StockTransactions.query.filter_by(deleted_at=None).all()
        return [transaction.to_dict() for transaction in transactions], 200

    def post(self):
        data = request.get_json()
        required_fields = {"transaction_type", "product_id", "quantity_change"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        product = Products.query.filter_by(id=data.get("product_id"), deleted_at=None).first()
        if not product:
            return {"error": "Product not found!"}, 404

        try:
            quantity_change = float(data.get("quantity_change"))
        except ValueError:
            return {"error": "Quantity change must be a valid number!"}, 400

        # Get current stock before transaction
        quantity_before = product.current_stock

        # Calculate quantity after
        transaction_type = clean_text(data.get("transaction_type"))
        if transaction_type in ["grn", "adjustment_positive", "return"]:
            quantity_after = quantity_before + quantity_change
        elif transaction_type in ["issue", "adjustment_negative", "transfer_out"]:
            quantity_after = quantity_before - abs(quantity_change)
        else:
            return {"error": f"Invalid transaction type: {transaction_type}"}, 400

        if quantity_after < 0:
            return {"error": "Insufficient stock! Transaction would result in negative stock."}, 400

        transaction = StockTransactions(
            transaction_type=transaction_type,
            product_id=product.id,
            reference_number=clean_text(data.get("reference_number")),
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            unit_cost=float(data.get("unit_cost", product.buying_price or 0)),
            notes=clean_text(data.get("notes")),
            performed_by=data.get("performed_by"),
        )

        db.session.add(transaction)

        # Update product stock
        product.current_stock = quantity_after

        db.session.commit()

        return transaction.to_dict(), 201


class StockTransactionResource(Resource):
    def get(self, transaction_id):
        transaction = StockTransactions.query.filter_by(id=transaction_id, deleted_at=None).first()

        if not transaction:
            return {"error": "Stock transaction not found!"}, 404

        return transaction.to_dict(), 200

    def delete(self, transaction_id):
        transaction = StockTransactions.query.filter_by(id=transaction_id, deleted_at=None).first()

        if not transaction:
            return {"error": "Stock transaction not found!"}, 404

        transaction.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Stock transaction deleted successfully!"}, 200


# ==================== PROJECT RESOURCES ====================

class Project(Resource):
    def get(self):
        projects = Projects.query.filter_by(deleted_at=None).all()
        return [project.to_dict() for project in projects], 200

    def post(self):
        data = request.get_json()
        required_fields = {"project_name", "customer_id"}

        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields!"}, 400

        customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
        if not customer:
            return {"error": "Customer not found!"}, 404

        project = Projects(
            project_name=clean_text(data.get("project_name")),
            customer_id=customer.id,
            location=clean_text(data.get("location")),
            contract_value=float(data.get("contract_value", 0)),
            start_date=parse_date(data.get("start_date")),
            end_date=parse_date(data.get("end_date")),
            assigned_engineer=clean_text(data.get("assigned_engineer")),
            assigned_technicians=clean_text(data.get("assigned_technicians")),
            materials_consumed=float(data.get("materials_consumed", 0)),
            invoices_raised=float(data.get("invoices_raised", 0)),
            payments_received=float(data.get("payments_received", 0)),
            profitability=float(data.get("profitability", 0)),
            status=clean_text(data.get("status")) or "planning",
            notes=clean_text(data.get("notes")),
        )

        db.session.add(project)
        db.session.commit()

        return project.to_dict(), 201


class ProjectResource(Resource):
    def get(self, project_id):
        project = Projects.query.filter_by(id=project_id, deleted_at=None).first()

        if not project:
            return {"error": "Project not found!"}, 404

        return project.to_dict(), 200

    def patch(self, project_id):
        project = Projects.query.filter_by(id=project_id, deleted_at=None).first()

        if not project:
            return {"error": "Project not found!"}, 404

        data = request.get_json()

        text_fields = ["project_name", "location", "assigned_engineer", "assigned_technicians", "status", "notes"]
        for field in text_fields:
            if field in data:
                setattr(project, field, clean_text(data.get(field)))

        date_fields = ["start_date", "end_date"]
        for field in date_fields:
            if field in data:
                setattr(project, field, parse_date(data.get(field)))

        numeric_fields = ["contract_value", "materials_consumed", "invoices_raised", "payments_received", "profitability"]
        for field in numeric_fields:
            if field in data:
                setattr(project, field, float(data.get(field)))

        if "customer_id" in data:
            customer = Customers.query.filter_by(id=data.get("customer_id"), deleted_at=None).first()
            if not customer:
                return {"error": "Customer not found!"}, 404
            project.customer_id = customer.id

        db.session.commit()

        return project.to_dict(), 200

    def delete(self, project_id):
        project = Projects.query.filter_by(id=project_id, deleted_at=None).first()

        if not project:
            return {"error": "Project not found!"}, 404

        project.deleted_at = datetime.utcnow()
        db.session.commit()

        return {"message": "Project deleted successfully!"}, 200