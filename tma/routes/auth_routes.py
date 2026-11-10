import re
from flask import Blueprint, request, g
from extensions import db
from models import User
from auth import api_response, generate_token, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-]{7,20}$')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User self-registration endpoint.
    Only creates users with role='user'. Admin and staff cannot self-register.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    phone = (data.get('phone') or '').strip()
    age = data.get('age')
    emergency_contact = (data.get('emergency_contact') or '').strip() or None
    address = (data.get('address') or '').strip() or None

    # Validate name
    if not name or len(name) < 2:
        return api_response(False, "Name is required and must be at least 2 characters.", None, 400)

    # Validate email
    if not email:
        return api_response(False, "Email is required.", None, 400)
    if not EMAIL_REGEX.match(email):
        return api_response(False, "Invalid email address format.", None, 400)

    # Validate phone
    if not phone:
        return api_response(False, "Phone number is required.", None, 400)
    if not PHONE_REGEX.match(phone):
        return api_response(False, "Invalid phone number format (must contain 7 to 20 digits).", None, 400)

    # Validate password length
    if not password or len(password) < 6:
        return api_response(False, "Password is required and must be at least 6 characters.", None, 400)

    # Validate optional age
    if age is not None and str(age).strip():
        try:
            age = int(age)
            if age <= 0 or age > 120:
                return api_response(False, "Age must be a valid positive integer between 1 and 120.", None, 400)
        except (TypeError, ValueError):
            return api_response(False, "Age must be an integer.", None, 400)
    else:
        age = None

    # Check for duplicate email
    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", None, 409)

    # Strictly force role to 'user' and status to 'active'
    new_user = User(
        name=name,
        email=email,
        phone=phone,
        role='user',
        status='active',
        age=age,
        emergency_contact=emergency_contact,
        address=address
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user)
    return api_response(
        True,
        "Registration successful.",
        {
            'token': token,
            'role': new_user.role,
            'name': new_user.name,
            'user': new_user.to_dict()
        },
        201
    )


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint for all three roles: admin, staff, and user.
    Refuses blacklisted or inactive accounts with a clear message.
    Returns token, role, name, and user profile.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return api_response(False, "Email and password are required.", None, 400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_response(False, "Invalid email or password.", None, 401)

    # Refuse blacklisted or inactive accounts with clear messages
    if user.status == 'blacklisted':
        return api_response(False, "Your account has been blacklisted. Access denied.", None, 403)
    if user.status == 'inactive':
        return api_response(False, "Your account is inactive. Please contact administrator.", None, 403)
    if user.status != 'active':
        return api_response(False, f"Your account status is '{user.status}'. Access denied.", None, 403)

    token = generate_token(user)
    return api_response(
        True,
        "Login successful.",
        {
            'token': token,
            'role': user.role,
            'name': user.name,
            'user': user.to_dict()
        },
        200
    )


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Get current logged-in user profile.
    """
    return api_response(
        True,
        "User profile retrieved successfully.",
        g.current_user.to_dict(),
        200
    )


@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_profile():
    """
    Update profile for the current user:
    name, phone, age, emergency_contact, address, and optional password change.
    """
    data = request.get_json(silent=True) or {}
    user = g.current_user

    if 'name' in data:
        name = (data['name'] or '').strip()
        if len(name) < 2:
            return api_response(False, "Name must be at least 2 characters.", None, 400)
        user.name = name

    if 'phone' in data:
        phone = (data['phone'] or '').strip()
        if phone:
            if not PHONE_REGEX.match(phone):
                return api_response(False, "Invalid phone number format.", None, 400)
            user.phone = phone
        else:
            user.phone = None

    if 'age' in data:
        age_val = data['age']
        if age_val is not None and str(age_val).strip():
            try:
                age_int = int(age_val)
                if age_int <= 0 or age_int > 120:
                    return api_response(False, "Age must be between 1 and 120.", None, 400)
                user.age = age_int
            except (TypeError, ValueError):
                return api_response(False, "Age must be an integer.", None, 400)
        else:
            user.age = None

    if 'emergency_contact' in data:
        user.emergency_contact = (data['emergency_contact'] or '').strip() or None

    if 'address' in data:
        user.address = (data['address'] or '').strip() or None

    # Optional password change
    new_password = data.get('new_password') or data.get('password')
    if new_password:
        current_password = data.get('current_password')
        if not current_password:
            return api_response(False, "Current password is required to set a new password.", None, 400)
        if not user.check_password(current_password):
            return api_response(False, "Current password is incorrect.", None, 400)
        if len(new_password) < 6:
            return api_response(False, "New password must be at least 6 characters.", None, 400)
        user.set_password(new_password)

    db.session.commit()

    return api_response(
        True,
        "Profile updated successfully.",
        user.to_dict(),
        200
    )
