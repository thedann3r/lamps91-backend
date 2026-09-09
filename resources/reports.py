# resources/reports.py
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models import db, Customers, Invoices, Receipts, Quotations, Products
from resources.decorators import admin_required, finance_required
from datetime import datetime, timedelta
from sqlalchemy import func, extract


class SalesReport(Resource):
    """Generate sales report with VAT breakdown"""
    
    @jwt_required()
    @finance_required
    def get(self):
        # Get date range from query params (optional)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Default to last 30 days if not provided
        if not end_date:
            end_date = datetime.utcnow().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Query invoices within date range
        invoices = Invoices.query.filter(
            Invoices.invoice_date >= start_date,
            Invoices.invoice_date <= end_date,
            Invoices.deleted_at == None
        ).all()
        
        # Calculate totals
        total_invoices = len(invoices)
        total_invoice_value = sum(float(inv.invoice_total or 0) for inv in invoices)
        total_vat = sum(float(inv.vat_amount or 0) for inv in invoices)
        total_vat_exempt = sum(float(inv.vat_exempt_total or 0) for inv in invoices)
        total_vatable = sum(float(inv.vatable_total or 0) for inv in invoices)
        total_paid = sum(float(inv.amount_paid or 0) for inv in invoices)
        total_balance = total_invoice_value - total_paid
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_invoices": total_invoices,
                "total_invoice_value": round(total_invoice_value, 2),
                "total_vat": round(total_vat, 2),
                "total_vat_exempt": round(total_vat_exempt, 2),
                "total_vatable": round(total_vatable, 2),
                "total_paid": round(total_paid, 2),
                "total_outstanding": round(total_balance, 2)
            },
            "invoices": [inv.to_dict() for inv in invoices[:20]]  # Limit to 20 for performance
        }, 200


class VATReport(Resource):
    """Generate VAT summary report for KRA"""
    
    @jwt_required()
    @finance_required
    def get(self):
        # Get year and month from query params
        year = request.args.get('year', datetime.utcnow().year, type=int)
        month = request.args.get('month', datetime.utcnow().month, type=int)
        
        # Query invoices for the specified month/year
        invoices = Invoices.query.filter(
            extract('year', Invoices.invoice_date) == year,
            extract('month', Invoices.invoice_date) == month,
            Invoices.deleted_at == None
        ).all()
        
        # Calculate VAT summary
        total_sales = sum(float(inv.invoice_total or 0) for inv in invoices)
        total_vat = sum(float(inv.vat_amount or 0) for inv in invoices)
        total_vat_exempt = sum(float(inv.vat_exempt_total or 0) for inv in invoices)
        total_vatable = sum(float(inv.vatable_total or 0) for inv in invoices)
        
        # VAT breakdown by customer
        customer_vat = {}
        for inv in invoices:
            customer_name = inv.customer.customer_name if inv.customer else "Unknown"
            if customer_name not in customer_vat:
                customer_vat[customer_name] = {
                    "customer_name": customer_name,
                    "customer_id": inv.customer_id,
                    "total_sales": 0,
                    "vat_amount": 0,
                    "vat_exempt": 0
                }
            customer_vat[customer_name]["total_sales"] += float(inv.invoice_total or 0)
            customer_vat[customer_name]["vat_amount"] += float(inv.vat_amount or 0)
            customer_vat[customer_name]["vat_exempt"] += float(inv.vat_exempt_total or 0)
        
        return {
            "period": {
                "year": year,
                "month": month,
                "month_name": datetime(year, month, 1).strftime('%B')
            },
            "summary": {
                "total_sales": round(total_sales, 2),
                "total_vat": round(total_vat, 2),
                "total_vat_exempt": round(total_vat_exempt, 2),
                "total_vatable": round(total_vatable, 2),
                "vat_rate": "16%",
                "invoice_count": len(invoices)
            },
            "customer_breakdown": list(customer_vat.values())
        }, 200


class OutstandingReport(Resource):
    """Get customers with outstanding balances"""
    
    @jwt_required()
    @finance_required
    def get(self):
        customers = Customers.query.filter(
            Customers.deleted_at == None,
            Customers.outstanding_balance > 0
        ).all()
        
        # Sort by highest outstanding balance
        customers.sort(key=lambda c: float(c.outstanding_balance or 0), reverse=True)
        
        return {
            "total_customers": len(customers),
            "total_outstanding": round(sum(float(c.outstanding_balance or 0) for c in customers), 2),
            "customers": [{
                "id": c.id,
                "customer_name": c.customer_name,
                "phone": c.phone,
                "email": c.email,
                "outstanding_balance": float(c.outstanding_balance or 0),
                "invoices_count": len(c.invoices)
            } for c in customers]
        }, 200


class MonthlySalesReport(Resource):
    """Get monthly sales trends"""
    
    @jwt_required()
    @finance_required
    def get(self):
        year = request.args.get('year', datetime.utcnow().year, type=int)
        
        # Get monthly aggregates
        monthly_data = db.session.query(
            extract('month', Invoices.invoice_date).label('month'),
            func.sum(Invoices.invoice_total).label('total_sales'),
            func.sum(Invoices.vat_amount).label('total_vat'),
            func.sum(Invoices.vat_exempt_total).label('vat_exempt'),
            func.sum(Invoices.vatable_total).label('vatable'),
            func.count(Invoices.id).label('invoice_count')
        ).filter(
            extract('year', Invoices.invoice_date) == year,
            Invoices.deleted_at == None
        ).group_by(
            extract('month', Invoices.invoice_date)
        ).all()
        
        # Format results
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        result = []
        for data in monthly_data:
            month_index = int(data.month) - 1
            result.append({
                "month": months[month_index],
                "month_number": int(data.month),
                "total_sales": round(float(data.total_sales or 0), 2),
                "total_vat": round(float(data.total_vat or 0), 2),
                "vat_exempt": round(float(data.vat_exempt or 0), 2),
                "vatable": round(float(data.vatable or 0), 2),
                "invoice_count": data.invoice_count
            })
        
        # Fill in missing months with zeros
        existing_months = {r['month_number'] for r in result}
        for i in range(1, 13):
            if i not in existing_months:
                result.append({
                    "month": months[i-1],
                    "month_number": i,
                    "total_sales": 0,
                    "total_vat": 0,
                    "vat_exempt": 0,
                    "vatable": 0,
                    "invoice_count": 0
                })
        
        result.sort(key=lambda x: x['month_number'])
        
        # Calculate yearly totals
        total_sales = sum(r['total_sales'] for r in result)
        total_vat = sum(r['total_vat'] for r in result)
        total_vat_exempt = sum(r['vat_exempt'] for r in result)
        
        return {
            "year": year,
            "months": result,
            "yearly_totals": {
                "total_sales": round(total_sales, 2),
                "total_vat": round(total_vat, 2),
                "total_vat_exempt": round(total_vat_exempt, 2),
                "average_monthly_sales": round(total_sales / 12, 2) if total_sales > 0 else 0
            }
        }, 200


class DashboardStats(Resource):
    """Get dashboard statistics (for the main dashboard)"""
    
    @jwt_required()
    def get(self):
        # Get counts
        total_customers = Customers.query.filter_by(deleted_at=None).count()
        total_products = Products.query.filter_by(deleted_at=None).count()
        total_quotations = Quotations.query.filter_by(deleted_at=None).count()
        
        # Pending invoices (not paid)
        pending_invoices = Invoices.query.filter(
            Invoices.deleted_at == None,
            Invoices.status.in_(['pending', 'partial_paid'])
        ).all()
        pending_invoices_count = len(pending_invoices)
        pending_invoices_value = sum(float(inv.invoice_total or 0) for inv in pending_invoices)
        
        # Monthly sales (current month)
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        monthly_invoices = Invoices.query.filter(
            extract('year', Invoices.invoice_date) == current_year,
            extract('month', Invoices.invoice_date) == current_month,
            Invoices.deleted_at == None
        ).all()
        monthly_sales = sum(float(inv.invoice_total or 0) for inv in monthly_invoices)
        
        # Inventory value
        products = Products.query.filter_by(deleted_at=None).all()
        inventory_value = sum(float(p.current_stock or 0) * float(p.buying_price or 0) for p in products)
        low_stock = [p for p in products if p.current_stock <= p.reorder_level]
        
        # Recent activity
        recent_quotations = Quotations.query.filter_by(deleted_at=None).order_by(
            Quotations.created_at.desc()
        ).limit(5).all()
        
        recent_payments = Receipts.query.filter_by(deleted_at=None).order_by(
            Receipts.created_at.desc()
        ).limit(5).all()
        
        return {
            "stats": {
                "total_customers": total_customers,
                "total_products": total_products,
                "total_quotations": total_quotations,
                "pending_invoices": {
                    "count": pending_invoices_count,
                    "value": round(pending_invoices_value, 2)
                },
                "monthly_sales": round(monthly_sales, 2),
                "inventory_value": round(inventory_value, 2),
                "low_stock_count": len(low_stock)
            },
            "recent_quotations": [q.to_dict() for q in recent_quotations],
            "recent_payments": [r.to_dict() for r in recent_payments],
            "low_stock_items": [{
                "id": p.id,
                "product_name": p.product_name,
                "current_stock": p.current_stock,
                "reorder_level": p.reorder_level
            } for p in low_stock[:5]]
        }, 200