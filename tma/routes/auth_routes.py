import re
from flask import Blueprint, request, g
from extensions import db
from models import User
from auth import api_response, generate_token, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name = (data.get('name') or data.get('full_name') or '').strip()
    phone = (data.get('phone') or '').strip() or None
    age = data.get('age')
    emergency_contact = (data.get('emergency_contact') or '').strip() or None
    address = (data.get('address') or '').strip() or None

    # Validations
    if not email:
        return api_response(False, "Email is required.", None, 400)
    if not EMAIL_REGEX.match(email):
        return api_response(False, "Invalid email address format.", None, 400)
    if not name or len(name) < 2:
        return api_response(False, "Name must be at least 2 characters.", None, 400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters.", None, 400)

    if age is not None and str(age).strip():
        try:
            age = int(age)
            if age <= 0 or age > 120:
                return api_response(False, "Age must be a valid positive integer.", None, 400)
        except (TypeError, ValueError):
            return api_response(False, "Age must be an integer.", None, 400)
    else:
        age = None

    # Check existing user
    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", None, 409)

    # Create new user (Role is strictly 'user' for self-registration, status 'active')
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
            'user': new_user.to_dict(),
            'token': token
        },
        201
    )


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return api_response(False, "Email and password are required.", None, 400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_response(False, "Invalid email or password.", None, 401)

    if user.status != 'active':
        return api_response(False, f"Your account is {user.status}. Please contact administrator.", None, 403)

    token = generate_token(user)
    return api_response(
        True,
        "Login successful.",
        {
            'user': user.to_dict(),
            'token': token
        },
        200
    )


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return api_response(
        True,
        "Current user profile retrieved.",
        g.current_user.to_dict(),
        200
    )


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or data.get('full_name') or '').strip()

    if name:
        if len(name) < 2:
            return api_response(False, "Name must be at least 2 characters.", None, 400)
        g.current_user.name = name

    if 'phone' in data:
        g.current_user.phone = (data['phone'] or '').strip() or None

    if 'age' in data:
        age_val = data['age']
        if age_val is not None and str(age_val).strip():
            try:
                g.current_user.age = int(age_val)
            except (TypeError, ValueError):
                return api_response(False, "Age must be an integer.", None, 400)
        else:
            g.current_user.age = None

    if 'emergency_contact' in data:
        g.current_user.emergency_contact = (data['emergency_contact'] or '').strip() or None

    if 'address' in data:
        g.current_user.address = (data['address'] or '').strip() or None

    db.session.commit()

    return api_response(
        True,
        "Profile updated successfully.",
        g.current_user.to_dict(),
        200
    )


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''

    if not current_password or not new_password:
        return api_response(False, "Current password and new password are required.", None, 400)

    if not g.current_user.check_password(current_password):
        return api_response(False, "Current password is incorrect.", None, 400)

    if len(new_password) < 6:
        return api_response(False, "New password must be at least 6 characters long.", None, 400)

    g.current_user.set_password(new_password)
    db.session.commit()

    return api_response(True, "Password changed successfully.", None, 200)
