# resources/requisitions.py
from flask import request, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Requisitions, RequisitionItems, Products, PurchaseOrders, PurchaseOrderItems, Suppliers
from resources.decorators import store_required, admin_required
from resources.pdf_generator import generate_requisition_pdf
from datetime import datetime, date


class RequisitionList(Resource):
    """List all requisitions or create new"""
    
    @jwt_required()
    @store_required
    def get(self):
        """Get all requisitions"""
        requisitions = Requisitions.query.filter_by(deleted_at=None).order_by(
            Requisitions.created_at.desc()
        ).all()
        return [r.to_dict() for r in requisitions], 200
    
    @jwt_required()
    @store_required
    def post(self):
        """Create a new requisition"""
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get("items"):
            return {"error": "Missing required fields: items"}, 400
        
        current_user_id = get_jwt_identity()
        
        # Generate requisition number
        last_req = Requisitions.query.order_by(Requisitions.id.desc()).first()
        last_num = int(last_req.requisition_number.split("-")[1]) if last_req and last_req.requisition_number else 0
        requisition_number = f"REQ-{last_num + 1:04d}"
        
        # Create requisition
        requisition = Requisitions(
            requisition_number=requisition_number,
            requested_by_id=int(current_user_id),
            department=data.get("department"),
            justification=data.get("justification"),
            status="pending",
        )
        
        db.session.add(requisition)
        db.session.flush()
        
        # Add items
        total = 0
        for item in data.get("items", []):
            product = None
            product_id = item.get("product_id")
            if product_id:
                product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                if not product:
                    return {"error": f"Product with id {product_id} not found!"}, 404
            
            item_description = item.get("item_description")
            if not item_description and not product:
                return {"error": "Each item needs an item_description or product_id!"}, 422
            
            try:
                quantity = float(item.get("quantity_requested", 1))
                unit_price = float(item.get("estimated_unit_price", product.buying_price if product else 0))
            except ValueError:
                return {"error": "Quantity and unit price must be valid numbers!"}, 400
            
            line_total = quantity * unit_price
            total += line_total
            
            req_item = RequisitionItems(
                requisition_id=requisition.id,
                product_id=product.id if product else None,
                item_description=item_description or product.product_name,
                quantity_requested=quantity,
                estimated_unit_price=unit_price,
                line_total=line_total,
                notes=item.get("notes"),
            )
            db.session.add(req_item)
        
        db.session.commit()
        
        return requisition.to_dict(), 201


class RequisitionResource(Resource):
    """Get, update, or delete a specific requisition"""
    
    @jwt_required()
    @store_required
    def get(self, requisition_id):
        """Get requisition by ID"""
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        return requisition.to_dict(), 200
    
    @jwt_required()
    @store_required
    def patch(self, requisition_id):
        """Update a requisition (only if pending)"""
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        
        if requisition.status != "pending":
            return {"error": "Only pending requisitions can be updated!"}, 400
        
        data = request.get_json()
        
        if "department" in data:
            requisition.department = data["department"]
        if "justification" in data:
            requisition.justification = data["justification"]
        
        # Update items if provided
        if "items" in data:
            RequisitionItems.query.filter_by(requisition_id=requisition.id).delete()
            
            for item in data["items"]:
                product = None
                product_id = item.get("product_id")
                if product_id:
                    product = Products.query.filter_by(id=product_id, deleted_at=None).first()
                    if not product:
                        return {"error": f"Product with id {product_id} not found!"}, 404
                
                item_description = item.get("item_description")
                if not item_description and not product:
                    return {"error": "Each item needs an item_description or product_id!"}, 422
                
                try:
                    quantity = float(item.get("quantity_requested", 1))
                    unit_price = float(item.get("estimated_unit_price", product.buying_price if product else 0))
                except ValueError:
                    return {"error": "Quantity and unit price must be valid numbers!"}, 400
                
                line_total = quantity * unit_price
                
                req_item = RequisitionItems(
                    requisition_id=requisition.id,
                    product_id=product.id if product else None,
                    item_description=item_description or product.product_name,
                    quantity_requested=quantity,
                    estimated_unit_price=unit_price,
                    line_total=line_total,
                    notes=item.get("notes"),
                )
                db.session.add(req_item)
        
        requisition.updated_at = datetime.utcnow()
        db.session.commit()
        
        return requisition.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def delete(self, requisition_id):
        """Soft delete a requisition"""
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        
        requisition.deleted_at = datetime.utcnow()
        db.session.commit()
        return {"message": "Requisition deleted successfully!"}, 200


class RequisitionApprove(Resource):
    """Approve or reject a requisition"""
    
    @jwt_required()
    @admin_required
    def post(self, requisition_id):
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        
        if requisition.status != "pending":
            return {"error": "Only pending requisitions can be approved/rejected!"}, 400
        
        data = request.get_json()
        status = data.get("status", "approved")
        
        if status not in ["approved", "rejected"]:
            return {"error": "Status must be 'approved' or 'rejected'"}, 400
        
        requisition.status = status
        requisition.approved_by_id = int(get_jwt_identity())
        
        if data.get("notes"):
            requisition.justification = (requisition.justification or "") + f"\n[{datetime.utcnow().date()}] {data['notes']}"
        
        db.session.commit()
        return requisition.to_dict(), 200


class RequisitionConvertToPO(Resource):
    """Convert approved requisition to Purchase Order"""
    
    @jwt_required()
    @store_required
    def post(self, requisition_id):
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        
        if requisition.status != "approved":
            return {"error": "Only approved requisitions can be converted to Purchase Orders!"}, 400
        
        if requisition.purchase_order_id:
            return {"error": "Purchase Order already exists for this requisition!"}, 400
        
        data = request.get_json()
        
        # Validate supplier
        supplier_id = data.get("supplier_id")
        if not supplier_id:
            return {"error": "Missing supplier_id!"}, 400
        
        supplier = Suppliers.query.filter_by(id=supplier_id, deleted_at=None).first()
        if not supplier:
            return {"error": "Supplier not found!"}, 404
        
        # Generate PO number
        last_po = PurchaseOrders.query.order_by(PurchaseOrders.id.desc()).first()
        last_num = int(last_po.po_number.split("-")[1]) if last_po and last_po.po_number else 0
        po_number = f"PO-{last_num + 1:04d}"
        
        # Create Purchase Order
        po = PurchaseOrders(
            po_number=po_number,
            po_date=date.today(),
            supplier_id=supplier.id,
            required_date=datetime.strptime(data["required_date"], "%Y-%m-%d").date() if data.get("required_date") else None,
            expected_delivery=datetime.strptime(data["expected_delivery"], "%Y-%m-%d").date() if data.get("expected_delivery") else None,
            status="open",
            notes=f"From Requisition {requisition.requisition_number}",
        )
        
        db.session.add(po)
        db.session.flush()
        
        # Copy items from requisition
        total = 0
        for req_item in requisition.items:
            line_total = float(req_item.line_total or 0)
            total += line_total
            
            po_item = PurchaseOrderItems(
                purchase_order_id=po.id,
                product_id=req_item.product_id,
                item_description=req_item.item_description,
                quantity_ordered=req_item.quantity_requested,
                quantity_received=0,
                unit_price=req_item.estimated_unit_price,
                line_total=line_total,
            )
            db.session.add(po_item)
        
        po.total_amount = total
        requisition.purchase_order_id = po.id
        requisition.status = "converted_to_po"
        
        db.session.commit()
        
        return {
            "message": "Requisition converted to Purchase Order successfully!",
            "requisition": requisition.to_dict(),
            "purchase_order": po.to_dict()
        }, 201


class RequisitionPDF(Resource):
    """Generate PDF for requisition"""
    
    @jwt_required()
    @store_required
    def get(self, requisition_id):
        requisition = Requisitions.query.filter_by(id=requisition_id, deleted_at=None).first()
        if not requisition:
            return {"error": "Requisition not found!"}, 404
        
        pdf_buffer = generate_requisition_pdf(requisition)
        filename = f"requisition_{requisition.requisition_number}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )