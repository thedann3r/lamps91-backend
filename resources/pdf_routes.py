# resources/pdf_routes.py
from flask import send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db, Quotations, Invoices, Receipts
from resources.decorators import sales_required, finance_required
from resources.pdf_generator import generate_quotation_pdf, generate_invoice_pdf, generate_receipt_pdf
from datetime import datetime

class QuotationPDF(Resource):
    @jwt_required()
    @sales_required
    def get(self, quotation_id):
        quotation = Quotations.query.filter_by(id=quotation_id, deleted_at=None).first()
        if not quotation:
            return {"error": "Quotation not found!"}, 404
        
        pdf_buffer = generate_quotation_pdf(quotation)
        filename = f"quotation_{quotation.quote_number or quotation_id}.pdf"
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


class InvoicePDF(Resource):
    @jwt_required()
    @finance_required
    def get(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        if not invoice:
            return {"error": "Invoice not found!"}, 404
        
        pdf_buffer = generate_invoice_pdf(invoice)
        filename = f"invoice_{invoice.invoice_number or invoice_id}.pdf"
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


class ReceiptPDF(Resource):
    @jwt_required()
    @finance_required
    def get(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()
        if not receipt:
            return {"error": "Receipt not found!"}, 404
        
        pdf_buffer = generate_receipt_pdf(receipt)
        filename = f"receipt_{receipt.receipt_number or receipt_id}.pdf"
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')