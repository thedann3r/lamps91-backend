# resources/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
import os


def get_company_info():
    """Get company info from database or use defaults"""
    try:
        from models import CompanySettings
        settings = CompanySettings.query.first()
        
        if settings:
            return {
                "name": settings.company_name or "LAMPS91 Energies Ltd",
                "tagline": settings.tagline or "",
                "address": settings.physical_address or "P.O. Box 12345, Nairobi",
                "postal_address": settings.postal_address or "",
                "phone": settings.phone or "0118401463",
                "email": settings.email or "info@lamps91.co.ke",
                "whatsapp": settings.whatsapp_number or "254118401463",
                "kra_pin": settings.kra_pin or "A123456789Z",
                "website": settings.website or "",
                "logo_url": settings.logo_url,
                "primary_color": settings.primary_color or "#1E3A8A",
                "secondary_color": settings.secondary_color or "#F59E0B",
                "text_color": settings.text_color or "#000000",
                "bank_name": settings.bank_name,
                "bank_account_name": settings.bank_account_name,
                "bank_account_number": settings.bank_account_number,
                "bank_branch": settings.bank_branch,
                "mpesa_paybill": settings.mpesa_paybill,
                "mpesa_account": settings.mpesa_account,
                "default_terms": settings.default_terms,
            }
    except Exception:
        pass
    
    # Fallback defaults
    return {
        "name": "LAMPS91 Energies Ltd",
        "tagline": "Solar & Electrical Solutions",
        "address": "P.O. Box 12345, Nairobi",
        "postal_address": "",
        "phone": "0118401463",
        "email": "info@lamps91.co.ke",
        "whatsapp": "254118401463",
        "kra_pin": "A123456789Z",
        "website": "",
        "logo_url": None,
        "primary_color": "#1E3A8A",
        "secondary_color": "#F59E0B",
        "text_color": "#000000",
        "bank_name": None,
        "bank_account_name": None,
        "bank_account_number": None,
        "bank_branch": None,
        "mpesa_paybill": None,
        "mpesa_account": None,
        "default_terms": None,
    }


def add_company_header(elements, company):
    """Add branded company header to PDF"""
    primary = colors.HexColor(company.get("primary_color", "#1E3A8A"))
    secondary = colors.HexColor(company.get("secondary_color", "#F59E0B"))
    
    # Logo (if available)
    logo_path = company.get("logo_url")
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=40*mm, height=15*mm)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 3*mm))
        except Exception:
            pass
    
    # Company name with primary color
    company_name_style = ParagraphStyle(
        'CompanyName',
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=primary,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(company["name"].upper(), company_name_style))
    
    # Tagline
    if company.get("tagline"):
        tagline_style = ParagraphStyle(
            'Tagline',
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=secondary,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(company["tagline"], tagline_style))
    
    # Contact info
    contact_style = ParagraphStyle(
        'Contact',
        fontSize=8,
        fontName='Helvetica',
        alignment=TA_CENTER,
        textColor=colors.HexColor("#333333"),
    )
    
    contact_parts = []
    if company.get("address"):
        contact_parts.append(company["address"])
    if company.get("phone"):
        contact_parts.append(f"Tel: {company['phone']}")
    if company.get("email"):
        contact_parts.append(f"Email: {company['email']}")
    
    if contact_parts:
        elements.append(Paragraph(" | ".join(contact_parts), contact_style))
    
    # KRA PIN and WhatsApp
    tax_parts = []
    if company.get("kra_pin"):
        tax_parts.append(f"KRA PIN: {company['kra_pin']}")
    if company.get("whatsapp"):
        tax_parts.append(f"WhatsApp: {company['whatsapp']}")
    
    if tax_parts:
        elements.append(Paragraph(" | ".join(tax_parts), contact_style))
    
    # Horizontal line
    elements.append(Spacer(1, 3*mm))
    line_data = [[""]]
    line_table = Table(line_data, colWidths=[170*mm], rowHeights=[0.5*mm])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 5*mm))


def add_document_title(elements, title, primary_color):
    """Add document title with brand color"""
    primary = colors.HexColor(primary_color)
    title_style = ParagraphStyle(
        'DocTitle',
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=primary,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 5*mm))


def add_payment_details_footer(elements, company):
    """Add payment details footer"""
    if not (company.get("bank_name") or company.get("mpesa_paybill")):
        return
    
    primary = colors.HexColor(company.get("primary_color", "#1E3A8A"))
    footer_heading = ParagraphStyle(
        'FooterHeading',
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=primary,
        alignment=TA_LEFT,
    )
    footer_text = ParagraphStyle(
        'FooterText',
        fontSize=8,
        fontName='Helvetica',
        alignment=TA_LEFT,
    )
    
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("PAYMENT DETAILS", footer_heading))
    
    if company.get("bank_name"):
        elements.append(Paragraph(
            f"Bank: {company['bank_name']} | Account Name: {company.get('bank_account_name', 'N/A')} | "
            f"Account No: {company.get('bank_account_number', 'N/A')} | Branch: {company.get('bank_branch', 'N/A')}",
            footer_text
        ))
    
    if company.get("mpesa_paybill"):
        elements.append(Paragraph(
            f"M-Pesa Paybill: {company['mpesa_paybill']} | Account: {company.get('mpesa_account', 'N/A')}",
            footer_text
        ))


def add_terms_footer(elements, company, terms=None):
    """Add terms and conditions footer"""
    default_terms = company.get("default_terms")
    final_terms = terms or default_terms
    
    if not final_terms:
        return
    
    heading_style = ParagraphStyle(
        'TermsHeading',
        fontSize=9,
        fontName='Helvetica-Bold',
    )
    text_style = ParagraphStyle(
        'TermsText',
        fontSize=8,
        fontName='Helvetica',
    )
    
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("Terms & Conditions:", heading_style))
    elements.append(Paragraph(final_terms, text_style))


def generate_quotation_pdf(quotation, company_info=None):
    """Generate branded PDF for a quotation"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    company = company_info or get_company_info()
    primary = colors.HexColor(company.get("primary_color", "#1E3A8A"))
    secondary = colors.HexColor(company.get("secondary_color", "#F59E0B"))
    
    elements = []
    
    # Branded header
    add_company_header(elements, company)
    
    # Document title
    add_document_title(elements, "QUOTATION", company.get("primary_color", "#1E3A8A"))
    
    # Quotation details
    quote_number = quotation.quote_number or f"QUOTE-{quotation.id:04d}"
    elements.append(Paragraph(f"<b>Quote No:</b> {quote_number}", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {quotation.quote_date or datetime.now().date()}", normal_style))
    elements.append(Paragraph(f"<b>Valid Until:</b> {quotation.valid_until or 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = quotation.customer
    elements.append(Paragraph("Customer Details:", heading_style))
    elements.append(Paragraph(f"<b>Name:</b> {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Contact:</b> {customer.contact_person if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Phone:</b> {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Email:</b> {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>KRA PIN:</b> {customer.kra_pin if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Project details
    if quotation.project_name:
        elements.append(Paragraph(f"<b>Project:</b> {quotation.project_name}", normal_style))
    if quotation.site_location:
        elements.append(Paragraph(f"<b>Site Location:</b> {quotation.site_location}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Item Description", "Qty", "Unit Price (KES)", "Discount (KES)", "Total (KES)"]]
    for item in quotation.items:
        items_data.append([
            item.item_description[:40] if item.item_description else "",
            str(item.quantity),
            f"{float(item.unit_price or 0):,.2f}",
            f"{float(item.discount or 0):,.2f}",
            f"{float(item.line_total or 0):,.2f}"
        ])
    
    table = Table(items_data, colWidths=[75*mm, 18*mm, 30*mm, 27*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sub Total:", "", "", "", f"{float(quotation.sub_total or 0):,.2f}"],
        ["VAT Exempt Total:", "", "", "", f"{float(quotation.vat_exempt_total or 0):,.2f}"],
        ["VATable Total:", "", "", "", f"{float(quotation.vatable_total or 0):,.2f}"],
        ["VAT (16%):", "", "", "", f"{float(quotation.vat_amount or 0):,.2f}"],
        ["GRAND TOTAL:", "", "", "", f"KES {float(quotation.grand_total or 0):,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[75*mm, 18*mm, 30*mm, 27*mm, 30*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TEXTCOLOR', (0, 4), (-1, 4), primary),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#F0F4FF")),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))
    
    # Terms and Conditions
    add_terms_footer(elements, company, quotation.terms_conditions)
    
    # Footer
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"<b>Prepared by:</b> {quotation.prepared_by.name if quotation.prepared_by else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Authorized by:</b> {quotation.authorized_by or 'N/A'}", normal_style))
    
    # Payment details
    add_payment_details_footer(elements, company)
    
    # Thank you note
    elements.append(Spacer(1, 8*mm))
    thank_you_style = ParagraphStyle(
        'ThankYou',
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=secondary,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("Thank you for your business!", thank_you_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(invoice, company_info=None):
    """Generate branded PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    company = company_info or get_company_info()
    primary = colors.HexColor(company.get("primary_color", "#1E3A8A"))
    secondary = colors.HexColor(company.get("secondary_color", "#F59E0B"))
    
    elements = []
    
    # Branded header
    add_company_header(elements, company)
    
    # Document title
    add_document_title(elements, "TAX INVOICE", company.get("primary_color", "#1E3A8A"))
    
    # Invoice details
    invoice_number = invoice.invoice_number or f"INV-{invoice.id:04d}"
    elements.append(Paragraph(f"<b>Invoice No:</b> {invoice_number}", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {invoice.invoice_date or datetime.now().date()}", normal_style))
    elements.append(Paragraph(f"<b>Due Date:</b> {invoice.due_date or 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Reference:</b> {invoice.reference or 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = invoice.customer
    elements.append(Paragraph("Customer Details:", heading_style))
    elements.append(Paragraph(f"<b>Name:</b> {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Contact:</b> {customer.contact_person if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Phone:</b> {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Email:</b> {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>KRA PIN:</b> {customer.kra_pin if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Items table
    items_data = [["Item Description", "Qty", "Unit Price (KES)", "Discount (KES)", "Total (KES)"]]
    for item in invoice.invoice_items:
        items_data.append([
            item.item_description[:40] if item.item_description else "",
            str(item.quantity),
            f"{float(item.unit_price or 0):,.2f}",
            f"{float(item.discount or 0):,.2f}",
            f"{float(item.line_total or 0):,.2f}"
        ])
    
    table = Table(items_data, colWidths=[75*mm, 18*mm, 30*mm, 27*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sub Total:", "", "", "", f"{float(invoice.sub_total or 0):,.2f}"],
        ["VAT Exempt Total:", "", "", "", f"{float(invoice.vat_exempt_total or 0):,.2f}"],
        ["VATable Total:", "", "", "", f"{float(invoice.vatable_total or 0):,.2f}"],
        ["VAT (16%):", "", "", "", f"{float(invoice.vat_amount or 0):,.2f}"],
        ["INVOICE TOTAL:", "", "", "", f"KES {float(invoice.invoice_total or 0):,.2f}"],
        ["Amount Paid:", "", "", "", f"KES {float(invoice.amount_paid or 0):,.2f}"],
        ["Balance Due:", "", "", "", f"KES {float(invoice.balance_due or 0):,.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[75*mm, 18*mm, 30*mm, 27*mm, 30*mm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 4), (-1, 4), 11),
        ('TEXTCOLOR', (0, 4), (-1, 4), primary),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#F0F4FF")),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 6), (-1, 6), colors.red if float(invoice.balance_due or 0) > 0 else colors.green),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 5*mm))
    
    # Status
    status_style = ParagraphStyle(
        'Status',
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.green if invoice.status == "paid" else (colors.red if invoice.status in ["overdue", "pending"] else primary),
    )
    elements.append(Paragraph(f"Status: {invoice.status.upper()}", status_style))
    elements.append(Paragraph(f"Payment Method: Bank Transfer / M-Pesa / Cash", normal_style))
    
    # Payment details
    add_payment_details_footer(elements, company)
    
    # Thank you note
    elements.append(Spacer(1, 8*mm))
    thank_you_style = ParagraphStyle(
        'ThankYou',
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=secondary,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("Thank you for your business!", thank_you_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(receipt, company_info=None):
    """Generate branded PDF for a receipt"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    company = company_info or get_company_info()
    primary = colors.HexColor(company.get("primary_color", "#1E3A8A"))
    secondary = colors.HexColor(company.get("secondary_color", "#F59E0B"))
    
    elements = []
    
    # Branded header
    add_company_header(elements, company)
    
    # Document title
    add_document_title(elements, "PAYMENT RECEIPT", company.get("primary_color", "#1E3A8A"))
    
    # Receipt details
    receipt_number = receipt.receipt_number or f"REC-{receipt.id:04d}"
    elements.append(Paragraph(f"<b>Receipt No:</b> {receipt_number}", normal_style))
    elements.append(Paragraph(f"<b>Date:</b> {receipt.receipt_date or datetime.now().date()}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Customer details
    customer = receipt.customer
    elements.append(Paragraph("Received From:", heading_style))
    elements.append(Paragraph(f"<b>Name:</b> {customer.customer_name if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Phone:</b> {customer.phone if customer else 'N/A'}", normal_style))
    elements.append(Paragraph(f"<b>Email:</b> {customer.email if customer else 'N/A'}", normal_style))
    elements.append(Spacer(1, 5*mm))
    
    # Payment details
    elements.append(Paragraph("Payment Details:", heading_style))
    
    payment_data = [
        ["Amount Received:", f"KES {float(receipt.amount_received or 0):,.2f}"],
        ["Payment Method:", receipt.payment_method.upper()],
    ]
    if receipt.transaction_reference:
        payment_data.append(["Transaction Ref:", receipt.transaction_reference])
    if receipt.invoice_id:
        invoice = receipt.invoice
        if invoice:
            payment_data.append(["Invoice No:", invoice.invoice_number])
            payment_data.append(["Balance Due:", f"KES {float(invoice.balance_due or 0):,.2f}"])
    
    payment_table = Table(payment_data, colWidths=[60*mm, 110*mm])
    payment_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 5*mm))
    
    # Footer
    elements.append(Paragraph(f"<b>Received by:</b> {receipt.received_by or 'N/A'}", normal_style))
    if receipt.notes:
        elements.append(Paragraph(f"<b>Notes:</b> {receipt.notes}", normal_style))
    
    elements.append(Spacer(1, 10*mm))
    
    # Thank you note
    thank_you_style = ParagraphStyle(
        'ThankYou',
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=secondary,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("Thank you for your payment!", thank_you_style))
    
    # Contact info
    elements.append(Spacer(1, 5*mm))
    contact_style = ParagraphStyle(
        'ContactFooter',
        fontSize=8,
        fontName='Helvetica',
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
    )
    if company.get("phone"):
        elements.append(Paragraph(f"For any queries, contact us at {company['phone']}", contact_style))
    if company.get("whatsapp"):
        elements.append(Paragraph(f"WhatsApp: {company['whatsapp']}", contact_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer