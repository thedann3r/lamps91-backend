# resources/whatsapp.py
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db, Quotations, Invoices, Receipts, CompanySettings
from resources.decorators import sales_required, finance_required
from urllib.parse import quote


def generate_whatsapp_link(phone, message):
    """Generate WhatsApp share link"""
    # Clean phone number (remove spaces, +, etc.)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Encode message
    encoded_message = quote(message)
    
    return f"https://wa.me/{clean_phone}?text={encoded_message}"


class SendQuotationWhatsApp(Resource):
    @jwt_required()
    @sales_required
    def get(self, quotation_id):
        quotation = Quotations.query.filter_by(id=quotation_id, deleted_at=None).first()
        
        if not quotation:
            return {"error": "Quotation not found!"}, 404
        
        customer = quotation.customer
        if not customer or not customer.phone:
            return {"error": "Customer phone number not available!"}, 400
        
        company = CompanySettings.query.first()
        company_name = company.company_name if company else "LAMPS91 Energies Ltd"
        
        message = f"""Hello {customer.customer_name},

Please find your quotation *{quotation.quote_number}* from {company_name}.

Project: {quotation.project_name or 'N/A'}
Grand Total: KES {float(quotation.grand_total or 0):,.2f}
Valid Until: {quotation.valid_until or 'N/A'}

For any queries, contact us at {company.phone if company else '0118401463'}.

Thank you!"""
        
        link = generate_whatsapp_link(customer.phone, message)
        
        return {
            "whatsapp_link": link,
            "phone": customer.phone,
            "message": message
        }, 200


class SendInvoiceWhatsApp(Resource):
    @jwt_required()
    @finance_required
    def get(self, invoice_id):
        invoice = Invoices.query.filter_by(id=invoice_id, deleted_at=None).first()
        
        if not invoice:
            return {"error": "Invoice not found!"}, 404
        
        customer = invoice.customer
        if not customer or not customer.phone:
            return {"error": "Customer phone number not available!"}, 400
        
        company = CompanySettings.query.first()
        
        message = f"""Hello {customer.customer_name},

Your invoice *{invoice.invoice_number}* is ready.

Invoice Total: KES {float(invoice.invoice_total or 0):,.2f}
Balance Due: KES {float(invoice.balance_due or 0):,.2f}
Due Date: {invoice.due_date or 'N/A'}

For any queries, contact us at {company.phone if company else '0118401463'}.

Thank you!"""
        
        link = generate_whatsapp_link(customer.phone, message)
        
        return {
            "whatsapp_link": link,
            "phone": customer.phone,
            "message": message
        }, 200


class SendReceiptWhatsApp(Resource):
    @jwt_required()
    @finance_required
    def get(self, receipt_id):
        receipt = Receipts.query.filter_by(id=receipt_id, deleted_at=None).first()
        
        if not receipt:
            return {"error": "Receipt not found!"}, 404
        
        customer = receipt.customer
        if not customer or not customer.phone:
            return {"error": "Customer phone number not available!"}, 400
        
        company = CompanySettings.query.first()
        
        message = f"""Hello {customer.customer_name},

We acknowledge receipt of your payment.

Receipt No: *{receipt.receipt_number}*
Amount Received: KES {float(receipt.amount_received or 0):,.2f}
Payment Method: {receipt.payment_method.upper()}

Thank you for your business!"""
        
        link = generate_whatsapp_link(customer.phone, message)
        
        return {
            "whatsapp_link": link,
            "phone": customer.phone,
            "message": message
        }, 200