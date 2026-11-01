# resources/supplier_invoices.py
from flask import request, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, SupplierInvoices, SupplierInvoiceItems, Suppliers, PurchaseOrders, SupplierPayments
from resources.decorators import finance_required, store_required, admin_required
from resources.pdf_generator import generate_supplier_invoice_pdf
from datetime import datetime, date


class SupplierInvoiceList(Resource):
    """List all supplier invoices or create new"""
    
    @jwt_required()
    @finance_required
    def get(self):
        invoices = SupplierInvoices.query.filter_by(deleted_at=None).order_by(
            SupplierInvoices.created_at.desc()
        ).all()
        return [inv.to_dict() for inv in invoices], 200
    
    @jwt_required()
    @finance_required
    def post(self):
        data = request.get_json()
        
        # Validate required fields
        required_fields = {"supplier_id", "invoice_number", "items"}
        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields: supplier_id, invoice_number, items"}, 400
        
        # Check supplier exists
        supplier = Suppliers.query.filter_by(id=data["supplier_id"], deleted_at=None).first()
        if not supplier:
            return {"error": "Supplier not found!"}, 404
        
        # Check duplicate invoice number
        if SupplierInvoices.query.filter_by(invoice_number=data["invoice_number"], deleted_at=None).first():
            return {"error": "Invoice number already exists!"}, 400
        
        # Check PO exists if provided
        po = None
        if data.get("purchase_order_id"):
            po = PurchaseOrders.query.filter_by(id=data["purchase_order_id"], deleted_at=None).first()
            if not po:
                return {"error": "Purchase Order not found!"}, 404
        
        # Create invoice
        invoice = SupplierInvoices(
            invoice_number=data["invoice_number"].strip(),
            supplier_id=supplier.id,
            purchase_order_id=po.id if po else None,
            invoice_date=datetime.strptime(data["invoice_date"], "%Y-%m-%d").date() if data.get("invoice_date") else date.today(),
            due_date=datetime.strptime(data["due_date"], "%Y-%m-%d").date() if data.get("due_date") else None,
            reference=data.get("reference"),
            status="pending",
            notes=data.get("notes"),
        )
        
        db.session.add(invoice)
        db.session.flush()
        
        # Add items and calculate totals
        sub_total = 0
        vat_amount = 0
        
        for item in data.get("items", []):
            try:
                quantity = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", 0))
            except ValueError:
                return {"error": "Quantity and unit price must be valid numbers!"}, 400
            
            line_total = quantity * unit_price
            sub_total += line_total
            
            vat_status = item.get("vat_status", "vatable")
            if vat_status == "vatable":
                vat_amount += line_total * 0.16
            
            invoice_item = SupplierInvoiceItems(
                supplier_invoice_id=invoice.id,
                product_id=item.get("product_id"),
                item_description=item.get("item_description", ""),
                quantity=quantity,
                unit_price=unit_price,
                vat_status=vat_status,
                line_total=line_total,
            )
            db.session.add(invoice_item)
        
        invoice.sub_total = sub_total
        invoice.vat_amount = vat_amount
        invoice.invoice_total = sub_total + vat_amount
        invoice.balance_due = invoice.invoice_total
        
        db.session.commit()
        
        return invoice.to_dict(), 201


class SupplierInvoiceResource(Resource):
    """Get, update, or delete a specific supplier invoice"""
    
    @jwt_required()
    @finance_required
    def get(self, invoice_id):
        invoice = SupplierInvoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Supplier invoice not found!"}, 404
        return invoice.to_dict(), 200
    
    @jwt_required()
    @finance_required
    def patch(self, invoice_id):
        invoice = SupplierInvoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Supplier invoice not found!"}, 404
        
        data = request.get_json()
        
        if "invoice_date" in data:
            invoice.invoice_date = datetime.strptime(data["invoice_date"], "%Y-%m-%d").date()
        if "due_date" in data:
            invoice.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        if "reference" in data:
            invoice.reference = data["reference"]
        if "notes" in data:
            invoice.notes = data["notes"]
        if "status" in data:
            invoice.status = data["status"]
        
        invoice.updated_at = datetime.utcnow()
        db.session.commit()
        
        return invoice.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def delete(self, invoice_id):
        invoice = SupplierInvoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Supplier invoice not found!"}, 404
        
        invoice.deleted_at = datetime.utcnow()
        db.session.commit()
        return {"message": "Supplier invoice deleted successfully!"}, 200


class SupplierInvoicePDF(Resource):
    """Generate PDF for supplier invoice"""
    
    @jwt_required()
    @finance_required
    def get(self, invoice_id):
        invoice = SupplierInvoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Supplier invoice not found!"}, 404
        
        pdf_buffer = generate_supplier_invoice_pdf(invoice)
        filename = f"supplier_invoice_{invoice.invoice_number}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )


class SupplierPaymentList(Resource):
    """List all supplier payments or create new"""
    
    @jwt_required()
    @finance_required
    def get(self):
        payments = SupplierPayments.query.filter_by(deleted_at=None).order_by(
            SupplierPayments.created_at.desc()
        ).all()
        return [p.to_dict() for p in payments], 200
    
    @jwt_required()
    @finance_required
    def post(self):
        data = request.get_json()
        
        required_fields = {"supplier_invoice_id", "payment_method", "amount_paid"}
        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields: supplier_invoice_id, payment_method, amount_paid"}, 400
        
        # Check invoice exists
        invoice = SupplierInvoices.query.filter_by(id=data["supplier_invoice_id"], deleted_at=None).first()
        if not invoice:
            return {"error": "Supplier invoice not found!"}, 404
        
        try:
            amount_paid = float(data["amount_paid"])
        except ValueError:
            return {"error": "Amount paid must be a valid number!"}, 400
        
        # Check if amount exceeds remaining balance
        if amount_paid > invoice.balance_due:
            return {"error": f"Amount exceeds balance due of {invoice.balance_due}"}, 400
        
        # Generate payment number
        last_payment = SupplierPayments.query.order_by(SupplierPayments.id.desc()).first()
        last_num = int(last_payment.payment_number.split("-")[1]) if last_payment and last_payment.payment_number else 0
        payment_number = f"SPAY-{last_num + 1:04d}"
        
        # Create payment
        payment = SupplierPayments(
            payment_number=payment_number,
            supplier_invoice_id=invoice.id,
            supplier_id=invoice.supplier_id,
            payment_date=datetime.strptime(data["payment_date"], "%Y-%m-%d").date() if data.get("payment_date") else date.today(),
            payment_method=data["payment_method"],
            transaction_reference=data.get("transaction_reference"),
            amount_paid=amount_paid,
            paid_by_id=int(get_jwt_identity()),
            notes=data.get("notes"),
        )
        
        # Update invoice balance
        invoice.amount_paid = float(invoice.amount_paid or 0) + amount_paid
        invoice.balance_due = float(invoice.invoice_total or 0) - invoice.amount_paid
        
        if invoice.balance_due <= 0:
            invoice.status = "paid"
        else:
            invoice.status = "partial_paid"
        
        payment.balance_due = invoice.balance_due
        
        db.session.add(payment)
        db.session.commit()
        
        return payment.to_dict(), 201


class SupplierPaymentResource(Resource):
    """Get or delete a specific supplier payment"""
    
    @jwt_required()
    @finance_required
    def get(self, payment_id):
        payment = SupplierPayments.query.filter_by(id=payment_id, deleted_at=None).first()
        if not payment:
            return {"error": "Supplier payment not found!"}, 404
        return payment.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def delete(self, payment_id):
        payment = SupplierPayments.query.filter_by(id=payment_id, deleted_at=None).first()
        if not payment:
            return {"error": "Supplier payment not found!"}, 404
        
        # Reverse invoice balance
        invoice = payment.supplier_invoice
        if invoice:
            invoice.amount_paid = float(invoice.amount_paid or 0) - payment.amount_paid
            invoice.balance_due = float(invoice.invoice_total or 0) - invoice.amount_paid
            
            if invoice.balance_due <= 0:
                invoice.status = "paid"
            elif invoice.amount_paid > 0:
                invoice.status = "partial_paid"
            else:
                invoice.status = "pending"
        
        payment.deleted_at = datetime.utcnow()
        db.session.commit()
        
        return {"message": "Supplier payment deleted successfully!"}, 200