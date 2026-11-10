from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import current_app, request, g, jsonify
from extensions import db
from models import User

def api_response(success: bool = True, message: str = "", data=None, status_code: int = 200):
    """
    Standard unified API response shape across the entire application:
    {
        "success": bool,
        "message": str,
        "data": Any
    }
    """
    payload = {
        "success": bool(success),
        "message": str(message),
        "data": data
    }
    return jsonify(payload), status_code


def generate_token(user: User) -> str:
    """
    Generate a signed JWT token with standard claims.
    """
    secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY', 'default-secret')
    expires_in = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)

    now = datetime.utcnow()
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'role': user.role,
        'name': user.name,
        'iat': now,
        'exp': now + timedelta(seconds=expires_in)
    }

    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


def decode_token(token: str) -> dict:
    """
    Decode and verify a signed JWT token.
    """
    secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY', 'default-secret')
    return jwt.decode(token, secret, algorithms=['HS256'])


def login_required(f):
    """
    Decorator to protect endpoints: requires a valid JWT token in Authorization header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return api_response(False, "Missing Authorization header.", None, 401)

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return api_response(False, "Invalid Authorization header format. Expected 'Bearer <token>'.", None, 401)

        token = parts[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return api_response(False, "Token has expired. Please log in again.", None, 401)
        except jwt.InvalidTokenError:
            return api_response(False, "Invalid token. Authentication failed.", None, 401)

        user_id = payload.get('sub')
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return api_response(False, "Invalid token subject claim.", None, 401)

        user = db.session.get(User, user_id)
        if not user:
            return api_response(False, "User account not found.", None, 401)

        if user.status != 'active':
            return api_response(False, f"Account is {user.status}. Access denied.", None, 403)

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    """
    Decorator to restrict access to specific user roles (e.g. 'admin', 'staff', 'user').
    Requires @login_required to be executed first.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or g.current_user is None:
                return api_response(False, "Authentication required.", None, 401)

            if g.current_user.role not in allowed_roles:
                return api_response(
                    False,
                    f"Access forbidden: role '{g.current_user.role}' is not authorized to access this resource.",
                    None,
                    403
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator
