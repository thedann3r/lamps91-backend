from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import Users

def role_required(allowed_roles):
    """
    Decorator to restrict access to specific user roles.
    Usage: @role_required(['admin', 'finance_officer'])
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Get current user ID from JWT
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            
            if not user:
                return {"error": "User not found!"}, 404
            
            if user.role not in allowed_roles:
                return {"error": f"Access denied! Required roles: {', '.join(allowed_roles)}"}, 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Shorthand for admin-only access"""
    return role_required(['admin'])(fn)


def finance_required(fn):
    """Shorthand for finance and admin access"""
    return role_required(['admin', 'finance_officer'])(fn)


def store_required(fn):
    """Shorthand for store manager and admin access"""
    return role_required(['admin', 'store_manager'])(fn)


def engineer_required(fn):
    """Shorthand for engineer and admin access"""
    return role_required(['admin', 'engineer'])(fn)


def sales_required(fn):
    """Shorthand for sales and admin access"""
    return role_required(['admin', 'sales_officer'])(fn)