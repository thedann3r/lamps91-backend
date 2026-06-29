from datetime import datetime
from flask import request
from flask_restful import Resource
from models import db, Customers, Products, Quotations, QuotationItems


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

        if not data.get("items"):
            return {"error": "A quotation must have at least one item!"}, 400

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