# resources/company_settings.py
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CompanySettings
from resources.decorators import admin_required
from datetime import datetime


class CompanySettingsResource(Resource):
    """Get or update company settings"""
    
    @jwt_required()
    def get(self):
        """Get current company settings (all authenticated users)"""
        settings = CompanySettings.query.first()
        
        if not settings:
            # Create default settings if none exist
            settings = CompanySettings(
                company_name="LAMPS91 Energies Ltd",
                phone="0118401463",
                whatsapp_number="254118401463",
                email="info@lamps91.co.ke",
                kra_pin="A123456789Z",
            )
            db.session.add(settings)
            db.session.commit()
        
        return settings.to_dict(), 200
    
    @jwt_required()
    @admin_required
    def patch(self):
        """Update company settings (admin only)"""
        settings = CompanySettings.query.first()
        
        if not settings:
            return {"error": "Company settings not found!"}, 404
        
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        fields = [
            "company_name", "tagline", "email", "phone", "whatsapp_number",
            "physical_address", "postal_address", "kra_pin", "website", "logo_url",
            "primary_color", "secondary_color", "text_color",
            "bank_name", "bank_account_name", "bank_account_number", "bank_branch",
            "mpesa_paybill", "mpesa_account",
            "quotation_validity_days", "invoice_due_days", "default_terms"
        ]
        
        for field in fields:
            if field in data:
                setattr(settings, field, data[field])
        
        settings.updated_by_id = int(current_user_id)
        settings.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return settings.to_dict(), 200


class CompanySettingsReset(Resource):
    """Reset company settings to default"""
    
    @jwt_required()
    @admin_required
    def post(self):
        settings = CompanySettings.query.first()
        
        if settings:
            db.session.delete(settings)
        
        settings = CompanySettings(
            company_name="LAMPS91 Energies Ltd",
            phone="0118401463",
            whatsapp_number="254118401463",
            email="info@lamps91.co.ke",
            kra_pin="A123456789Z",
        )
        db.session.add(settings)
        db.session.commit()
        
        return {"message": "Company settings reset!", "settings": settings.to_dict()}, 200