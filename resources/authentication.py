from flask import request
from flask_restful import Resource
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, Users
from datetime import datetime
import re

bcrypt = Bcrypt()

# ==================== VALIDATION FUNCTIONS ====================

def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password):
    """
    Validate password strength:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long!"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least 1 uppercase letter!"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least 1 lowercase letter!"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least 1 number!"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least 1 special character (e.g., !@#$%^&*)!"
    
    return True, "Password is strong!"


def validate_phone(phone):
    """Validate Kenyan phone number format"""
    # Remove any spaces or special characters
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it matches Kenyan format: 0712345678 or +254712345678
    pattern = r'^(\+254|0)[17]\d{8}$'
    return re.match(pattern, cleaned) is not None


class Register(Resource):
    def post(self):
        data = request.get_json()
        
        # Validate required fields
        required = ["name", "email", "phone", "password"]
        if not all(field in data for field in required):
            return {"error": "Missing required fields!"}, 400

        # Validate required fields
        required = ["name", "email", "phone", "password"]
        if not all(field in data for field in required):
            return {"error": "Missing required fields: name, email, phone, password!"}, 400
        
        # Validate email format
        if not validate_email(data["email"]):
            return {"error": "Invalid email format! Example: user@domain.com"}, 400
        
        # Validate phone format (Kenyan)
        if not validate_phone(data["phone"]):
            return {"error": "Invalid phone number! Use format: 0712345678 or +254712345678"}, 400
        
        # Validate password strength
        is_valid, message = validate_password_strength(data["password"])
        if not is_valid:
            return {"error": message}, 400
        
        # Check if user exists
        if Users.query.filter_by(email=data["email"]).first():
            return {"error": "Email already registered!"}, 400
        
        if Users.query.filter_by(phone=data["phone"]).first():
            return {"error": "Phone already registered!"}, 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
        
        # Create user
        user = Users(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            password=hashed_password,
            role=data.get("role", "sales_officer")
        )
        
        db.session.add(user)
        db.session.commit()
        
        return {"message": "User created successfully!", "user": user.to_dict()}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        
        if not data.get("email") or not data.get("password"):
            return {"error": "Email and password required!"}, 400

         # Validate email format
        if not validate_email(data["email"]):
            return {"error": "Invalid email format!"}, 400
        
        user = Users.query.filter_by(email=data["email"], deleted_at=None).first()
        
        if not user:
            return {"error": "Invalid credentials!"}, 401
        
        if not bcrypt.check_password_hash(user.password, data["password"]):
            return {"error": "Invalid credentials!"}, 401
        
        if not user.is_active:
            return {"error": "Account deactivated!"}, 401
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }, 200


class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=user_id)
        return {"access_token": new_access_token}, 200


class Logout(Resource):
    @jwt_required()
    def post(self):
        # With JWT, logout is handled on client side (remove token)
        return {"message": "Logged out successfully!"}, 200