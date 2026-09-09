# resources/email_routes.py
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db, Quotations, Invoices, Receipts
from resources.decorators import sales_required, finance_required
from resources.pdf_generator import generate_quotation_pdf, generate_invoice_pdf, generate_receipt_pdf
from resources.email_utils import send_quotation_email, send_invoice_email, send_receipt_email

class SendQuotationEmail(Resource):
    @jwt_required()
    @sales_required
    def post(self, quotation_id):
        quotation = Quotations.query.filter_by(id=quotation_id, deleted_at=None).first()
        if not quotation:
            return {"error": "Quotation not found!"}, 404
        
        # Get email from request or use customer email
        data = request.get_json() or {}
        to_email = data.get('email')
        
        # Generate PDF
        pdf_buffer = generate_quotation_pdf(quotation)
        
        # Send email
        result = send_quotation_email(quotation, pdf_buffer, to_email)
        return result, 200 if 'status' in result else 500


class SendInvoiceEmail(Resource):
    @jwt_required()
    @finance_required
    def post(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Invoice not found!"}, 404
        
        data = request.get_json() or {}
        to_email = data.get('email')
        
        pdf_buffer = generate_invoice_pdf(invoice)
        result = send_invoice_email(invoice, pdf_buffer, to_email)
        return result, 200 if 'status' in result else 500


class SendReceiptEmail(Resource):
    @jwt_required()
    @finance_required
    def post(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()
        if not receipt:
            return {"error": "Receipt not found!"}, 404
        
        data = request.get_json() or {}
        to_email = data.get('email')
        
        pdf_buffer = generate_receipt_pdf(receipt)
        result = send_receipt_email(receipt, pdf_buffer, to_email)
        return result, 200 if 'status' in result else 500