# resources/email_utils.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import formatdate

def send_email_with_pdf(to_email, subject, html_content, pdf_buffer, pdf_filename, cc_email=None):
    """Send email with PDF attachment using SMTP"""
    
    # SMTP Configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    from_email = os.getenv("EMAIL_FROM")
    password = os.getenv("EMAIL_PASSWORD")
    
    if not from_email or not password:
        print("Warning: EMAIL_FROM or EMAIL_PASSWORD not set. Email not sent.")
        return {"error": "Email configuration incomplete"}
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)
    
    if cc_email:
        msg['Cc'] = cc_email
    
    # Attach HTML body
    msg.attach(MIMEText(html_content, 'html'))
    
    # Attach PDF
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_buffer.getvalue())
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f'attachment; filename="{pdf_filename}"'
    )
    msg.attach(part)
    
    try:
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return {"status": 200, "message": "Email sent successfully!"}
    except Exception as e:
        return {"error": str(e)}


def send_quotation_email(quotation, pdf_buffer, to_email=None):
    """Send quotation email with PDF attachment"""
    
    customer = quotation.customer
    if not to_email and customer:
        to_email = customer.email
    
    if not to_email:
        return {"error": "No email address provided"}
    
    subject = f"Quotation {quotation.quote_number} from LAMPS91 Energies Ltd"
    
    html_content = f"""
    <html>
    <body>
        <h2>Dear {customer.customer_name if customer else 'Customer'},</h2>
        <p>Thank you for your interest in LAMPS91 Energies Ltd.</p>
        <p>Please find attached your quotation <strong>{quotation.quote_number}</strong>.</p>
        <p><strong>Project:</strong> {quotation.project_name or 'N/A'}</p>
        <p><strong>Grand Total:</strong> KES {float(quotation.grand_total or 0):,.2f}</p>
        <br>
        <p><em>This is a system-generated email. For any queries, please contact us at info@lamps91.co.ke</em></p>
        <p>LAMPS91 Energies Ltd</p>
    </body>
    </html>
    """
    
    filename = f"quotation_{quotation.quote_number}.pdf"
    return send_email_with_pdf(to_email, subject, html_content, pdf_buffer, filename)


def send_invoice_email(invoice, pdf_buffer, to_email=None):
    """Send invoice email with PDF attachment"""
    
    customer = invoice.customer
    if not to_email and customer:
        to_email = customer.email
    
    if not to_email:
        return {"error": "No email address provided"}
    
    subject = f"Invoice {invoice.invoice_number} from LAMPS91 Energies Ltd"
    
    html_content = f"""
    <html>
    <body>
        <h2>Dear {customer.customer_name if customer else 'Customer'},</h2>
        <p>Please find attached your invoice <strong>{invoice.invoice_number}</strong>.</p>
        <p><strong>Invoice Total:</strong> KES {float(invoice.invoice_total or 0):,.2f}</p>
        <p><strong>Due Date:</strong> {invoice.due_date or 'N/A'}</p>
        <p><strong>Status:</strong> {invoice.status.upper()}</p>
        <br>
        <p><em>This is a system-generated email. For any queries, please contact us at info@lamps91.co.ke</em></p>
        <p>LAMPS91 Energies Ltd</p>
    </body>
    </html>
    """
    
    filename = f"invoice_{invoice.invoice_number}.pdf"
    return send_email_with_pdf(to_email, subject, html_content, pdf_buffer, filename)


def send_receipt_email(receipt, pdf_buffer, to_email=None):
    """Send receipt email with PDF attachment"""
    
    customer = receipt.customer
    if not to_email and customer:
        to_email = customer.email
    
    if not to_email:
        return {"error": "No email address provided"}
    
    subject = f"Payment Receipt {receipt.receipt_number} from LAMPS91 Energies Ltd"
    
    html_content = f"""
    <html>
    <body>
        <h2>Dear {customer.customer_name if customer else 'Customer'},</h2>
        <p>We acknowledge receipt of your payment.</p>
        <p>Please find attached your receipt <strong>{receipt.receipt_number}</strong>.</p>
        <p><strong>Amount Received:</strong> KES {float(receipt.amount_received or 0):,.2f}</p>
        <p><strong>Payment Method:</strong> {receipt.payment_method.upper()}</p>
        <br>
        <p><em>This is a system-generated email. For any queries, please contact us at info@lamps91.co.ke</em></p>
        <p>LAMPS91 Energies Ltd</p>
    </body>
    </html>
    """
    
    filename = f"receipt_{receipt.receipt_number}.pdf"
    return send_email_with_pdf(to_email, subject, html_content, pdf_buffer, filename)