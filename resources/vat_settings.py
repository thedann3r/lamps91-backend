# resources/vat_settings.py
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, VATSettings
from resources.decorators import admin_required
from datetime import datetime

# Default VAT categories (to be used when initializing)
DEFAULT_VAT_CATEGORIES = [
    {"category_name": "solar panels", "is_exempt": True, "description": "Solar panels - KRA VAT Exempt"},
    {"category_name": "inverters", "is_exempt": True, "description": "Solar inverters - KRA VAT Exempt"},
    {"category_name": "batteries", "is_exempt": True, "description": "Solar batteries - KRA VAT Exempt"},
    {"category_name": "solar cables", "is_exempt": False, "description": "Solar cables - VATable"},
    {"category_name": "mounting structures", "is_exempt": False, "description": "Mounting structures - VATable"},
    {"category_name": "accessories", "is_exempt": False, "description": "Electrical accessories - VATable"},
    {"category_name": "services", "is_exempt": False, "description": "Labour and services - VATable"},
]


class VATSettingsList(Resource):
    """List all VAT settings and create new ones"""
    
    @jwt_required()
    @admin_required
    def get(self):
        """Get all VAT settings"""
        settings = VATSettings.query.filter_by(deleted_at=None).all()
        return [s.to_dict() for s in settings], 200
    
    @jwt_required()
    @admin_required
    def post(self):
        """Add a new VAT category"""
        data = request.get_json()
        
        if not data or not data.get("category_name"):
            return {"error": "Category name is required!"}, 400
        
        # Check if category already exists
        existing = VATSettings.query.filter_by(
            category_name=data["category_name"].strip().lower(),
            deleted_at=None
        ).first()
        
        if existing:
            return {"error": "Category already exists!"}, 400
        
        current_user_id = get_jwt_identity()
        
        vat_setting = VATSettings(
            category_name=data["category_name"].strip().lower(),
            is_exempt=data.get("is_exempt", False),
            vat_rate=float(data.get("vat_rate", 0.16)),
            description=data.get("description"),
            updated_by_id=int(current_user_id),
        )
        
        db.session.add(vat_setting)
        db.session.commit()
        
        return vat_setting.to_dict(), 201


class VATSettingsDetail(Resource):
    """Get, update, or delete a specific VAT setting"""
    
    @jwt_required()
    @admin_required
    def get(self, setting_id):
        """Get a specific VAT setting"""
        setting = VATSettings.query.filter_by(id=setting_id, deleted_at=None).first()
        
        if not setting:
            return {"error": "VAT setting not found!"}, 404
        
        return setting.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def patch(self, setting_id):
        """Update a VAT setting"""
        setting = VATSettings.query.filter_by(id=setting_id, deleted_at=None).first()
        
        if not setting:
            return {"error": "VAT setting not found!"}, 404
        
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        if "category_name" in data:
            # Check if new name conflicts with existing
            new_name = data["category_name"].strip().lower()
            existing = VATSettings.query.filter(
                VATSettings.category_name == new_name,
                VATSettings.id != setting_id,
                VATSettings.deleted_at == None
            ).first()
            if existing:
                return {"error": "Category name already exists!"}, 400
            setting.category_name = new_name
        
        if "is_exempt" in data:
            setting.is_exempt = bool(data["is_exempt"])
        
        if "vat_rate" in data:
            setting.vat_rate = float(data["vat_rate"])
        
        if "description" in data:
            setting.description = data["description"]
        
        setting.updated_by_id = int(current_user_id)
        setting.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return setting.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def delete(self, setting_id):
        """Soft delete a VAT setting"""
        setting = VATSettings.query.filter_by(id=setting_id, deleted_at=None).first()
        
        if not setting:
            return {"error": "VAT setting not found!"}, 404
        
        setting.deleted_at = datetime.utcnow()
        db.session.commit()
        
        return {"message": "VAT setting removed successfully!"}, 200


class VATSettingsReset(Resource):
    """Reset VAT settings to default KRA values"""
    
    @jwt_required()
    @admin_required
    def post(self):
        """Reset all VAT settings to default values"""
        current_user_id = get_jwt_identity()
        
        # Soft delete all existing settings
        VATSettings.query.filter_by(deleted_at=None).update({
            VATSettings.deleted_at: datetime.utcnow()
        })
        
        # Create new default settings
        for cat in DEFAULT_VAT_CATEGORIES:
            vat_setting = VATSettings(
                category_name=cat["category_name"],
                is_exempt=cat["is_exempt"],
                vat_rate=0.16,
                description=cat["description"],
                updated_by_id=int(current_user_id),
            )
            db.session.add(vat_setting)
        
        db.session.commit()
        
        # Return all new settings
        settings = VATSettings.query.filter_by(deleted_at=None).all()
        return {
            "message": "VAT settings reset to default successfully!",
            "settings": [s.to_dict() for s in settings]
        }, 200


class VATSettingsCurrent(Resource):
    """Get current VAT rate and categories (read-only for non-admin users)"""
    
    @jwt_required()
    def get(self):
        """Get current VAT settings for all authenticated users"""
        settings = VATSettings.query.filter_by(deleted_at=None).all()
        
        # Separate exempt and vatable categories
        exempt_categories = [s.category_name for s in settings if s.is_exempt]
        vatable_categories = [s.category_name for s in settings if not s.is_exempt]
        
        # Get current VAT rate (use the most common one)
        vat_rates = [s.vat_rate for s in settings]
        current_vat_rate = max(set(vat_rates), key=vat_rates.count) if vat_rates else 0.16
        
        return {
            "vat_rate": current_vat_rate,
            "vat_rate_percentage": f"{current_vat_rate * 100}%",
            "exempt_categories": exempt_categories,
            "vatable_categories": vatable_categories,
            "all_settings": [s.to_dict() for s in settings]
        }, 200