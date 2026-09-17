# resources/client_lpos.py
from flask import request, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ClientLPO, Quotations, Customers, Users
from resources.decorators import sales_required, admin_required, finance_required
from resources.pdf_generator import generate_lpo_pdf
from datetime import datetime
from io import BytesIO
import os
import uuid


class ClientLPOList(Resource):
    @jwt_required()
    @sales_required
    def get(self):
        """Get all LPOs"""
        lpos = ClientLPO.query.filter_by(deleted_at=None).all()
        return [lpo.to_dict() for lpo in lpos], 200
    
    @jwt_required()
    @sales_required
    def post(self):
        """
        Create a new LPO
        Can be created:
        1. From a quotation (generate LPO for client to sign)
        2. With an uploaded document (client's signed LPO)
        """
        data = request.get_json()
        
        # Validate required fields
        required_fields = {"quotation_id"}
        if not data or not all(field in data for field in required_fields):
            return {"error": "Missing required fields: quotation_id"}, 400
        
        # Check quotation exists
        quotation = Quotations.query.filter_by(id=data["quotation_id"], deleted_at=None).first()
        if not quotation:
            return {"error": "Quotation not found!"}, 404
        
        # Check if LPO already exists for this quotation
        existing = ClientLPO.query.filter_by(quotation_id=data["quotation_id"], deleted_at=None).first()
        if existing:
            return {"error": "An LPO already exists for this quotation!"}, 400
        
        # Auto-generate LPO number if not provided
        lpo_number = data.get("lpo_number")
        if not lpo_number:
            last_lpo = ClientLPO.query.order_by(ClientLPO.id.desc()).first()
            last_num = int(last_lpo.lpo_number.split("-")[1]) if last_lpo and last_lpo.lpo_number else 0
            lpo_number = f"LPO-{last_num + 1:04d}"
        
        # Check for duplicate LPO number
        if ClientLPO.query.filter_by(lpo_number=lpo_number, deleted_at=None).first():
            return {"error": "LPO number already exists!"}, 400
        
        lpo = ClientLPO(
            lpo_number=lpo_number,
            customer_id=quotation.customer_id,
            quotation_id=quotation.id,
            lpo_date=datetime.strptime(data["lpo_date"], "%Y-%m-%d").date() if data.get("lpo_date") else datetime.utcnow().date(),
            lpo_value=float(data.get("lpo_value", quotation.grand_total or 0)),
            lpo_document_url=data.get("lpo_document_url"),  # Uploaded document URL
            notes=data.get("notes"),
            status="pending",
        )
        
        db.session.add(lpo)
        db.session.commit()
        
        return lpo.to_dict(), 201


class ClientLPOResource(Resource):
    @jwt_required()
    @sales_required
    def get(self, lpo_id):
        """Get LPO details"""
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        return lpo.to_dict(), 200
    
    @jwt_required()
    @sales_required
    def patch(self, lpo_id):
        """Update LPO details"""
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        data = request.get_json()
        
        if "lpo_number" in data:
            # Check duplicate
            existing = ClientLPO.query.filter(
                ClientLPO.lpo_number == data["lpo_number"],
                ClientLPO.id != lpo_id,
                ClientLPO.deleted_at == None
            ).first()
            if existing:
                return {"error": "LPO number already exists!"}, 400
            lpo.lpo_number = data["lpo_number"]
        
        if "lpo_date" in data:
            lpo.lpo_date = datetime.strptime(data["lpo_date"], "%Y-%m-%d").date()
        if "lpo_value" in data:
            lpo.lpo_value = float(data["lpo_value"])
        if "lpo_document_url" in data:
            lpo.lpo_document_url = data["lpo_document_url"]
        if "status" in data:
            lpo.status = data["status"]
        if "notes" in data:
            lpo.notes = data["notes"]
        
        db.session.commit()
        return lpo.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def delete(self, lpo_id):
        """Soft delete LPO"""
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        lpo.deleted_at = datetime.utcnow()
        db.session.commit()
        return {"message": "LPO deleted successfully!"}, 200


class ClientLPOApprove(Resource):
    """Approve or reject an LPO"""
    
    @jwt_required()
    @admin_required
    def post(self, lpo_id):
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        data = request.get_json()
        status = data.get("status", "approved")
        
        if status not in ["approved", "rejected"]:
            return {"error": "Status must be 'approved' or 'rejected'"}, 400
        
        lpo.status = status
        lpo.approved_by_id = int(get_jwt_identity())
        
        if data.get("notes"):
            lpo.notes = (lpo.notes or "") + f"\n[{datetime.utcnow().date()}] {data['notes']}"
        
        db.session.commit()
        return lpo.to_dict(), 200


class ClientLPOUpload(Resource):
    """Upload the client's signed LPO document"""
    
    @jwt_required()
    @sales_required
    def post(self, lpo_id):
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        if 'file' not in request.files:
            return {"error": "No file provided!"}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {"error": "No file selected!"}, 400
        
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return {"error": "Only PDF, JPG, JPEG, PNG files are allowed!"}, 400
        
        # Save file
        upload_dir = "uploads/lpos"
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"{lpo.lpo_number}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Update LPO with document URL
        lpo.lpo_document_url = file_path
        db.session.commit()
        
        return {
            "message": "LPO document uploaded successfully!",
            "lpo": lpo.to_dict(),
            "file_path": file_path
        }, 200


class ClientLPOGeneratePDF(Resource):
    """Generate LPO PDF from quotation for client to sign"""
    
    @jwt_required()
    @sales_required
    def get(self, lpo_id):
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        # Generate PDF
        pdf_buffer = generate_lpo_pdf(lpo)
        filename = f"lpo_{lpo.lpo_number}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )


class ClientLPOConvertToInvoice(Resource):
    """Convert approved LPO to an invoice"""
    
    @jwt_required()
    @finance_required
    def post(self, lpo_id):
        from models import Invoices, InvoiceItems
        
        lpo = ClientLPO.query.filter_by(id=lpo_id, deleted_at=None).first()
        if not lpo:
            return {"error": "LPO not found!"}, 404
        
        if lpo.status != "approved":
            return {"error": "Only approved LPOs can be converted to invoices!"}, 400
        
        # Check if invoice already exists
        if lpo.invoice:
            return {"error": "Invoice already exists for this LPO!"}, 400
        
        quotation = lpo.quotation
        if not quotation:
            return {"error": "Quotation not found!"}, 404
        
        # Generate invoice number
        last_invoice = Invoices.query.order_by(Invoices.id.desc()).first()
        last_num = int(last_invoice.invoice_number.split("-")[1]) if last_invoice and last_invoice.invoice_number else 0
        invoice_number = f"INV-{last_num + 1:04d}"
        
        # Create invoice from quotation
        invoice = Invoices(
            invoice_number=invoice_number,
            invoice_date=datetime.utcnow().date(),
            due_date=datetime.utcnow().date() + timedelta(days=30),
            customer_id=lpo.customer_id,
            quotation_id=quotation.id,
            reference=f"LPO: {lpo.lpo_number} | Quote: {quotation.quote_number}",
            status="pending",
            amount_paid=0,
        )
        
        db.session.add(invoice)
        db.session.flush()
        
        # Copy items from quotation
        for item in quotation.items:
            invoice_item = InvoiceItems(
                invoice_id=invoice.id,
                product_id=item.product_id,
                item_description=item.item_description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                vat_status=item.vat_status,
                line_total=item.line_total,
            )
            db.session.add(invoice_item)
        
        db.session.flush()
        calculate_invoice_totals(invoice)
        db.session.commit()
        
        return {
            "message": "Invoice generated from LPO successfully!",
            "invoice": invoice.to_dict(),
            "lpo": lpo.to_dict()
        }, 201