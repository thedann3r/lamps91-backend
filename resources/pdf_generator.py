# resources/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.fonts import addMapping
from io import BytesIO
from datetime import datetime
import os

def generate_quotation_pdf(quotation, company_info=None):
    """Generate PDF for a quotation"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Company info (default if not provided)
    if not company_info:
        company_info = {
            "name": "LAMPS91 Energies Ltd",
            "address": "P.O. Box 12345, Nairobi",
            "phone": "+254 700 000 000",
            "email": "info@lamps91.co.ke",
            "kra_pin": "A123456789Z"
        }
    
    elements = []
    
    # Header
    elements.append(Paragraph("LAMPS91 ENERGIES LTD", title_style))
    elements.append(Paragraph(company_info["address"], normal_style))
    elements.append(Paragraph(f"Tel: {company_info['phone']} | Email: {company_info['email']}", normal_style))
    elements.append(Paragraph(f"KRA PIN: {company_info['kra_pin']}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Title
    elements.append(Paragraph("QUOTATION", styles['Heading1']))
    elements.append(Spacer(1, 5*mm))
    
    # Quotation details
    quote_number = quotation.quote_number or f"QUOTE-{quotation.id:04d}"
    elements.append(Paragraph(f"Quote No: {quote_number}", normal_style))
    elements.append(Paragraph(f"Date: {quotation.quote_date or datetime.now().date()}", normal_style))
    elements.append(Paragraph(f"Valid Until: {quotation.valid_until or 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = quotation.customer
    elements.append(Paragraph("Customer Details:", heading_style))
    elements.append(Paragraph(f"Name: {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Contact: {customer.contact_person if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Phone: {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Email: {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"KRA PIN: {customer.kra_pin if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Project details
    if quotation.project_name:
        elements.append(Paragraph(f"Project: {quotation.project_name}", normal_style))
    if quotation.site_location:
        elements.append(Paragraph(f"Site Location: {quotation.site_location}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Item Description", "Qty", "Unit Price (KES)", "Discount (KES)", "Total (KES)"]]
    for item in quotation.items:
        items_data.append([
            item.item_description[:40],
            str(item.quantity),
            f"{float(item.unit_price or 0):,.2f}",
            f"{float(item.discount or 0):,.2f}",
            f"{float(item.line_total or 0):,.2f}"
        ])
    
    table = Table(items_data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm, 35*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sub Total:", "", "", "", f"{float(quotation.sub_total or 0):,.2f}"],
        ["VAT Exempt Total:", "", "", "", f"{float(quotation.vat_exempt_total or 0):,.2f}"],
        ["VATable Total:", "", "", "", f"{float(quotation.vatable_total or 0):,.2f}"],
        ["VAT (16%):", "", "", "", f"{float(quotation.vat_amount or 0):,.2f}"],
        ["GRAND TOTAL:", "", "", "", f"{float(quotation.grand_total or 0):,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm, 35*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))
    
    # Terms and Conditions
    if quotation.terms_conditions:
        elements.append(Paragraph("Terms & Conditions:", heading_style))
        elements.append(Paragraph(quotation.terms_conditions, normal_style))
    
    # Footer
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Prepared by: {quotation.prepared_by.name if quotation.prepared_by else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Authorized by: {quotation.authorized_by or 'N/A'}", normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(invoice, company_info=None):
    """Generate PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    if not company_info:
        company_info = {
            "name": "LAMPS91 Energies Ltd",
            "address": "P.O. Box 12345, Nairobi",
            "phone": "+254 700 000 000",
            "email": "info@lamps91.co.ke",
            "kra_pin": "A123456789Z"
        }
    
    elements = []
    
    # Header
    elements.append(Paragraph("LAMPS91 ENERGIES LTD", title_style))
    elements.append(Paragraph(company_info["address"], normal_style))
    elements.append(Paragraph(f"Tel: {company_info['phone']} | Email: {company_info['email']}", normal_style))
    elements.append(Paragraph(f"KRA PIN: {company_info['kra_pin']}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Title
    elements.append(Paragraph("TAX INVOICE", styles['Heading1']))
    elements.append(Spacer(1, 5*mm))
    
    # Invoice details
    invoice_number = invoice.invoice_number or f"INV-{invoice.id:04d}"
    elements.append(Paragraph(f"Invoice No: {invoice_number}", normal_style))
    elements.append(Paragraph(f"Date: {invoice.invoice_date or datetime.now().date()}", normal_style))
    elements.append(Paragraph(f"Due Date: {invoice.due_date or 'N/A'}", normal_style))
    elements.append(Paragraph(f"Reference: {invoice.reference or 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = invoice.customer
    elements.append(Paragraph("Customer Details:", heading_style))
    elements.append(Paragraph(f"Name: {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Contact: {customer.contact_person if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Phone: {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Email: {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"KRA PIN: {customer.kra_pin if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Item Description", "Qty", "Unit Price (KES)", "Discount (KES)", "Total (KES)"]]
    for item in invoice.invoice_items:
        items_data.append([
            item.item_description[:40],
            str(item.quantity),
            f"{float(item.unit_price or 0):,.2f}",
            f"{float(item.discount or 0):,.2f}",
            f"{float(item.line_total or 0):,.2f}"
        ])
    
    table = Table(items_data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm, 35*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sub Total:", "", "", "", f"{float(invoice.sub_total or 0):,.2f}"],
        ["VAT Exempt Total:", "", "", "", f"{float(invoice.vat_exempt_total or 0):,.2f}"],
        ["VATable Total:", "", "", "", f"{float(invoice.vatable_total or 0):,.2f}"],
        ["VAT (16%):", "", "", "", f"{float(invoice.vat_amount or 0):,.2f}"],
        ["INVOICE TOTAL:", "", "", "", f"{float(invoice.invoice_total or 0):,.2f}"],
        ["Amount Paid:", "", "", "", f"{float(invoice.amount_paid or 0):,.2f}"],
        ["Balance Due:", "", "", "", f"{float(invoice.balance_due or 0):,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm, 35*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))
    
    # Status
    elements.append(Paragraph(f"Status: {invoice.status.upper()}", heading_style))
    elements.append(Paragraph(f"Payment Method: Bank Transfer / M-Pesa / Cash", normal_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(receipt, company_info=None):
    """Generate PDF for a receipt"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    if not company_info:
        company_info = {
            "name": "LAMPS91 Energies Ltd",
            "address": "P.O. Box 12345, Nairobi",
            "phone": "+254 700 000 000",
            "email": "info@lamps91.co.ke",
            "kra_pin": "A123456789Z"
        }
    
    elements = []
    
    # Header
    elements.append(Paragraph("LAMPS91 ENERGIES LTD", title_style))
    elements.append(Paragraph(company_info["address"], normal_style))
    elements.append(Paragraph(f"Tel: {company_info['phone']} | Email: {company_info['email']}", normal_style))
    elements.append(Paragraph(f"KRA PIN: {company_info['kra_pin']}", normal_style))
    elements.append(Spacer(1, 10*mm))
    
    # Title
    elements.append(Paragraph("PAYMENT RECEIPT", styles['Heading1']))
    elements.append(Spacer(1, 5*mm))
    
    # Receipt details
    receipt_number = receipt.receipt_number or f"REC-{receipt.id:04d}"
    elements.append(Paragraph(f"Receipt No: {receipt_number}", normal_style))
    elements.append(Paragraph(f"Date: {receipt.receipt_date or datetime.now().date()}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = receipt.customer
    elements.append(Paragraph("Received From:", heading_style))
    elements.append(Paragraph(f"Name: {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Phone: {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"Email: {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Payment details
    elements.append(Paragraph("Payment Details:", heading_style))
    elements.append(Paragraph(f"Amount Received: KES {float(receipt.amount_received or 0):,.2f}", normal_style))
    elements.append(Paragraph(f"Payment Method: {receipt.payment_method.upper()}", normal_style))
    if receipt.transaction_reference:
        elements.append(Paragraph(f"Transaction Ref: {receipt.transaction_reference}", normal_style))
    if receipt.invoice_id:
        invoice = receipt.invoice
        if invoice:
            elements.append(Paragraph(f"Invoice No: {invoice.invoice_number}", normal_style))
            elements.append(Paragraph(f"Balance Due: KES {float(invoice.balance_due or 0):,.2f}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Footer
    elements.append(Paragraph(f"Received by: {receipt.received_by or 'N/A'}", normal_style))
    if receipt.notes:
        elements.append(Paragraph(f"Notes: {receipt.notes}", normal_style))
    
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("Thank you for your payment!", heading_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer