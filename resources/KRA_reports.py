# resources/kra_reports.py
from flask import request, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db, Invoices, Customers, Receipts
from resources.decorators import admin_required, finance_required
from datetime import datetime
from sqlalchemy import extract
import csv
from io import StringIO


class KRAVATReport(Resource):
    """
    KRA VAT Report for monthly filing
    Generates a comprehensive VAT report for KRA compliance
    """
    
    @jwt_required()
    @finance_required
    def get(self):
        # Get period from query params
        year = request.args.get('year', datetime.utcnow().year, type=int)
        month = request.args.get('month', datetime.utcnow().month, type=int)
        
        # Validate month
        if month < 1 or month > 12:
            return {"error": "Invalid month! Must be between 1 and 12."}, 400
        
        # Query invoices for the period
        invoices = Invoices.query.filter(
            extract('year', Invoices.invoice_date) == year,
            extract('month', Invoices.invoice_date) == month,
            Invoices.deleted_at == None
        ).all()
        
        if not invoices:
            return {
                "period": {"year": year, "month": month},
                "message": "No invoices found for this period",
                "summary": {
                    "total_sales": 0,
                    "total_vat": 0,
                    "total_exempt": 0,
                    "total_vatable": 0,
                    "invoice_count": 0
                }
            }, 200
        
        # Calculate totals
        total_sales = 0
        total_vat = 0
        total_exempt = 0
        total_vatable = 0
        
        for inv in invoices:
            total_sales += float(inv.invoice_total or 0)
            total_vat += float(inv.vat_amount or 0)
            total_exempt += float(inv.vat_exempt_total or 0)
            total_vatable += float(inv.vatable_total or 0)
        
        # Per-invoice breakdown
        invoice_details = []
        for inv in invoices:
            invoice_details.append({
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
                "customer_name": inv.customer.customer_name if inv.customer else "Unknown",
                "customer_kra_pin": inv.customer.kra_pin if inv.customer else None,
                "sub_total": float(inv.sub_total or 0),
                "vatable_total": float(inv.vatable_total or 0),
                "vat_exempt_total": float(inv.vat_exempt_total or 0),
                "vat_amount": float(inv.vat_amount or 0),
                "invoice_total": float(inv.invoice_total or 0),
                "status": inv.status
            })
        
        return {
            "company": {
                "name": "LAMPS91 Energies Ltd",
                "kra_pin": "A123456789Z",  # Update with real PIN
                "period": f"{year}-{month:02d}"
            },
            "summary": {
                "total_invoices": len(invoices),
                "total_sales": round(total_sales, 2),
                "total_vat": round(total_vat, 2),
                "total_vat_exempt": round(total_exempt, 2),
                "total_vatable": round(total_vatable, 2),
                "vat_rate": "16%",
                "net_sales": round(total_sales - total_vat, 2)
            },
            "invoices": invoice_details
        }, 200


class KRAVATReportCSV(Resource):
    """
    KRA VAT Report in CSV format for filing
    """
    
    @jwt_required()
    @finance_required
    def get(self):
        year = request.args.get('year', datetime.utcnow().year, type=int)
        month = request.args.get('month', datetime.utcnow().month, type=int)
        
        invoices = Invoices.query.filter(
            extract('year', Invoices.invoice_date) == year,
            extract('month', Invoices.invoice_date) == month,
            Invoices.deleted_at == None
        ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Invoice Number", "Invoice Date", "Customer Name", "Customer KRA PIN",
            "Sub Total", "VATable Total", "VAT Exempt Total", "VAT Amount", "Invoice Total", "Status"
        ])
        
        # Data
        for inv in invoices:
            writer.writerow([
                inv.invoice_number,
                inv.invoice_date.isoformat() if inv.invoice_date else "",
                inv.customer.customer_name if inv.customer else "",
                inv.customer.kra_pin if inv.customer else "",
                float(inv.sub_total or 0),
                float(inv.vatable_total or 0),
                float(inv.vat_exempt_total or 0),
                float(inv.vat_amount or 0),
                float(inv.invoice_total or 0),
                inv.status
            ])
        
        # Summary
        writer.writerow([])
        writer.writerow(["SUMMARY", "", "", "", "", "", "", "", "", ""])
        writer.writerow(["Total Invoices", len(invoices)])
        writer.writerow(["Total VATable Sales", sum(float(i.vatable_total or 0) for i in invoices)])
        writer.writerow(["Total VAT Exempt Sales", sum(float(i.vat_exempt_total or 0) for i in invoices)])
        writer.writerow(["Total VAT Collected", sum(float(i.vat_amount or 0) for i in invoices)])
        writer.writerow(["Total Sales", sum(float(i.invoice_total or 0) for i in invoices)])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=kra_vat_report_{year}_{month:02d}.csv'
        return response


class KRAVATReportExcel(Resource):
    """
    KRA VAT Report in Excel format for filing
    """
    
    @jwt_required()
    @finance_required
    def get(self):
        try:
            import openpyxl
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill
        except ImportError:
            return {"error": "openpyxl not installed. Run: pipenv install openpyxl"}, 500
        
        year = request.args.get('year', datetime.utcnow().year, type=int)
        month = request.args.get('month', datetime.utcnow().month, type=int)
        
        invoices = Invoices.query.filter(
            extract('year', Invoices.invoice_date) == year,
            extract('month', Invoices.invoice_date) == month,
            Invoices.deleted_at == None
        ).all()
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "KRA VAT Report"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        title_font = Font(bold=True, size=14)
        
        # Title
        ws['A1'] = "LAMPS91 ENERGIES LTD"
        ws['A1'].font = title_font
        ws['A2'] = f"KRA VAT REPORT - {year}-{month:02d}"
        ws['A2'].font = title_font
        ws['A3'] = f"Company KRA PIN: A123456789Z"
        
        # Headers
        headers = [
            "Invoice Number", "Invoice Date", "Customer Name", "Customer KRA PIN",
            "Sub Total (KES)", "VATable Total (KES)", "VAT Exempt Total (KES)",
            "VAT Amount (KES)", "Invoice Total (KES)", "Status"
        ]
        
        row_num = 5
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row_num, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Data
        row_num += 1
        for inv in invoices:
            ws.cell(row=row_num, column=1, value=inv.invoice_number)
            ws.cell(row=row_num, column=2, value=inv.invoice_date.isoformat() if inv.invoice_date else "")
            ws.cell(row=row_num, column=3, value=inv.customer.customer_name if inv.customer else "")
            ws.cell(row=row_num, column=4, value=inv.customer.kra_pin if inv.customer else "")
            ws.cell(row=row_num, column=5, value=float(inv.sub_total or 0))
            ws.cell(row=row_num, column=6, value=float(inv.vatable_total or 0))
            ws.cell(row=row_num, column=7, value=float(inv.vat_exempt_total or 0))
            ws.cell(row=row_num, column=8, value=float(inv.vat_amount or 0))
            ws.cell(row=row_num, column=9, value=float(inv.invoice_total or 0))
            ws.cell(row=row_num, column=10, value=inv.status)
            row_num += 1
        
        # Summary
        row_num += 2
        ws.cell(row=row_num, column=1, value="SUMMARY").font = Font(bold=True)
        row_num += 1
        summary_data = [
            ("Total Invoices", len(invoices)),
            ("Total VATable Sales (KES)", sum(float(i.vatable_total or 0) for i in invoices)),
            ("Total VAT Exempt Sales (KES)", sum(float(i.vat_exempt_total or 0) for i in invoices)),
            ("Total Output VAT (KES)", sum(float(i.vat_amount or 0) for i in invoices)),
            ("Total Sales (KES)", sum(float(i.invoice_total or 0) for i in invoices)),
        ]
        
        for label, value in summary_data:
            ws.cell(row=row_num, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row_num, column=2, value=value)
            row_num += 1
        
        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column].width = adjusted_width
        
        # Save to buffer
        from io import BytesIO
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Return response
        from flask import send_file
        filename = f"kra_vat_report_{year}_{month:02d}.xlsx"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )