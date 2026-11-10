import re
from datetime import datetime, date
from flask import Blueprint, request, g
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification
from auth import api_response, login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

# -------------------------------------------------------------
# Admin Dashboard / Summary Analytics
# -------------------------------------------------------------
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('admin')
def get_dashboard():
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    
    total_treks = Trek.query.filter_by(is_deleted=False).count()
    open_treks = Trek.query.filter_by(is_deleted=False, status='Open').count()
    pending_treks = Trek.query.filter_by(is_deleted=False, status='Pending').count()
    completed_treks = Trek.query.filter_by(is_deleted=False, status='Completed').count()

    all_bookings = Booking.query.all()
    total_bookings = len(all_bookings)
    active_bookings = [b for b in all_bookings if b.status == 'Booked']
    cancelled_bookings = [b for b in all_bookings if b.status == 'Cancelled']
    
    # Calculate revenue from confirmed/paid or active bookings
    total_revenue = sum(
        (b.participants_count * b.trek.price)
        for b in active_bookings if b.trek
    )

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(10).all()

    return api_response(
        True,
        "Admin dashboard statistics retrieved.",
        {
            'stats': {
                'total_users': total_users,
                'total_staff': total_staff,
                'total_treks': total_treks,
                'open_treks': open_treks,
                'pending_treks': pending_treks,
                'completed_treks': completed_treks,
                'total_bookings': total_bookings,
                'active_bookings': len(active_bookings),
                'cancelled_bookings': len(cancelled_bookings),
                'total_revenue': round(total_revenue, 2)
            },
            'recent_bookings': [b.to_dict() for b in recent_bookings]
        },
        200
    )


# -------------------------------------------------------------
# Staff Management
# -------------------------------------------------------------
@admin_bp.route('/staff', methods=['GET'])
@login_required
@role_required('admin')
def list_staff():
    staff_list = User.query.filter_by(role='staff').order_by(User.id.desc()).all()
    return api_response(
        True,
        "Staff list retrieved.",
        [s.to_dict() for s in staff_list],
        200
    )


@admin_bp.route('/staff', methods=['POST'])
@login_required
@role_required('admin')
def create_staff():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    name = (data.get('name') or '').strip()
    password = data.get('password') or ''
    phone = (data.get('phone') or '').strip() or None
    contact_details = (data.get('contact_details') or '').strip() or None
    specialization = (data.get('specialization') or '').strip() or 'General Trek Guide'

    if not email or not EMAIL_REGEX.match(email):
        return api_response(False, "A valid email address is required.", None, 400)
    if not name or len(name) < 2:
        return api_response(False, "Name must be at least 2 characters.", None, 400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters.", None, 400)

    if User.query.filter_by(email=email).first():
        return api_response(False, "A user with this email already exists.", None, 409)

    staff_user = User(
        name=name,
        email=email,
        phone=phone,
        role='staff',
        status='active'
    )
    staff_user.set_password(password)
    db.session.add(staff_user)
    db.session.flush() # Flush to get staff_user.id

    staff_profile = StaffProfile(
        user_id=staff_user.id,
        contact_details=contact_details,
        specialization=specialization,
        status='active',
        joined_on=date.today()
    )
    db.session.add(staff_profile)
    db.session.commit()

    return api_response(True, "Staff created successfully.", staff_user.to_dict(), 201)


@admin_bp.route('/staff/<int:staff_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_staff_detail(staff_id):
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)
    return api_response(True, "Staff details retrieved.", staff.to_dict(), 200)


@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_staff(staff_id):
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        name = data['name'].strip()
        if len(name) < 2:
            return api_response(False, "Name must be at least 2 characters.", None, 400)
        staff.name = name

    if 'phone' in data:
        staff.phone = (data['phone'] or '').strip() or None

    if 'status' in data:
        st = data['status']
        if st not in ['active', 'inactive', 'blacklisted']:
            return api_response(False, "Invalid status value.", None, 400)
        staff.status = st
        if staff.staff_profile:
            staff.staff_profile.status = 'active' if st == 'active' else 'inactive'

    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return api_response(False, "Password must be at least 6 characters.", None, 400)
        staff.set_password(data['password'])

    # Profile fields
    if staff.staff_profile:
        if 'contact_details' in data:
            staff.staff_profile.contact_details = data['contact_details']
        if 'specialization' in data:
            staff.staff_profile.specialization = data['specialization']

    db.session.commit()
    return api_response(True, "Staff member updated successfully.", staff.to_dict(), 200)


@admin_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_or_deactivate_staff(staff_id):
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)

    # Soft delete / toggle status to inactive
    staff.status = 'inactive'
    if staff.staff_profile:
        staff.staff_profile.status = 'inactive'
    db.session.commit()

    return api_response(True, "Staff member deactivated.", staff.to_dict(), 200)


# -------------------------------------------------------------
# Trek Management (CRUD)
# -------------------------------------------------------------
@admin_bp.route('/treks', methods=['GET'])
@login_required
@role_required('admin')
def list_treks():
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    query = Trek.query
    if not include_deleted:
        query = query.filter_by(is_deleted=False)
    
    treks = query.order_by(Trek.id.desc()).all()
    return api_response(True, "Treks retrieved.", [t.to_dict() for t in treks], 200)


@admin_bp.route('/treks', methods=['POST'])
@login_required
@role_required('admin')
def create_trek():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    location = (data.get('location') or '').strip()
    difficulty = (data.get('difficulty') or 'Moderate').strip()
    duration_days = data.get('duration_days')
    total_slots = data.get('total_slots')
    price = data.get('price')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    description = (data.get('description') or '').strip()
    instructions = (data.get('instructions') or '').strip() or None
    assigned_staff_id = data.get('assigned_staff_id')
    status = data.get('status') or 'Pending'

    # Validations
    if not name or len(name) < 3:
        return api_response(False, "Trek name must be at least 3 characters.", None, 400)
    if not location:
        return api_response(False, "Location is required.", None, 400)
    if difficulty not in ['Easy', 'Moderate', 'Hard']:
        return api_response(False, "Difficulty must be 'Easy', 'Moderate', or 'Hard'.", None, 400)
    if status not in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
        return api_response(False, "Invalid trek status.", None, 400)
    if not description or len(description) < 10:
        return api_response(False, "Description must be at least 10 characters.", None, 400)

    try:
        duration_days = int(duration_days)
        if duration_days <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Duration days must be a positive integer.", None, 400)

    try:
        total_slots = int(total_slots)
        if total_slots <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Total slots must be a positive integer.", None, 400)

    try:
        price = float(price)
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Price must be a non-negative number.", None, 400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return api_response(False, "Dates must be provided in YYYY-MM-DD format.", None, 400)

    if end_date < start_date:
        return api_response(False, "End date cannot be earlier than start date.", None, 400)

    # Validate staff assignment
    if assigned_staff_id:
        staff_user = db.session.get(User, assigned_staff_id)
        if not staff_user or staff_user.role != 'staff':
            return api_response(False, "Assigned staff member not found or is not staff.", None, 400)
    else:
        assigned_staff_id = None

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty,
        duration_days=duration_days,
        total_slots=total_slots,
        available_slots=total_slots, # Initially all slots are available
        assigned_staff_id=assigned_staff_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        description=description,
        instructions=instructions,
        price=price,
        is_deleted=False
    )
    db.session.add(trek)
    db.session.commit()

    return api_response(True, "Trek created successfully.", trek.to_dict(), 201)


@admin_bp.route('/treks/<int:trek_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)
    data = trek.to_dict()
    data['bookings'] = [b.to_dict() for b in trek.bookings.all()]
    return api_response(True, "Trek retrieved.", data, 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = data['name'].strip()
        if len(name) < 3:
            return api_response(False, "Trek name must be at least 3 characters.", None, 400)
        trek.name = name

    if 'location' in data:
        loc = data['location'].strip()
        if not loc:
            return api_response(False, "Location cannot be empty.", None, 400)
        trek.location = loc

    if 'difficulty' in data:
        diff = data['difficulty'].strip()
        if diff not in ['Easy', 'Moderate', 'Hard']:
            return api_response(False, "Difficulty must be 'Easy', 'Moderate', or 'Hard'.", None, 400)
        trek.difficulty = diff

    if 'duration_days' in data:
        try:
            d = int(data['duration_days'])
            if d <= 0:
                raise ValueError
            trek.duration_days = d
        except (TypeError, ValueError):
            return api_response(False, "Duration days must be a positive integer.", None, 400)

    if 'total_slots' in data:
        try:
            slots = int(data['total_slots'])
            active_booked = sum(b.participants_count for b in trek.bookings.filter_by(status='Booked').all())
            if slots < active_booked:
                return api_response(
                    False,
                    f"Total slots cannot be less than currently booked slots ({active_booked}).",
                    None,
                    400
                )
            trek.total_slots = slots
            trek.recalculate_available_slots()
        except (TypeError, ValueError):
            return api_response(False, "Total slots must be a positive integer.", None, 400)

    if 'price' in data:
        try:
            p = float(data['price'])
            if p < 0:
                raise ValueError
            trek.price = p
        except (TypeError, ValueError):
            return api_response(False, "Price must be a non-negative number.", None, 400)

    if 'start_date' in data:
        try:
            trek.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "Invalid start date format (YYYY-MM-DD).", None, 400)

    if 'end_date' in data:
        try:
            trek.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "Invalid end date format (YYYY-MM-DD).", None, 400)

    if trek.end_date < trek.start_date:
        return api_response(False, "End date cannot be earlier than start date.", None, 400)

    if 'description' in data:
        desc = data['description'].strip()
        if len(desc) < 10:
            return api_response(False, "Description must be at least 10 characters.", None, 400)
        trek.description = desc

    if 'instructions' in data:
        trek.instructions = (data['instructions'] or '').strip() or None

    if 'status' in data:
        st = data['status']
        if st not in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
            return api_response(False, "Invalid status value.", None, 400)
        trek.status = st

    if 'assigned_staff_id' in data:
        staff_id = data['assigned_staff_id']
        if staff_id:
            staff_user = db.session.get(User, staff_id)
            if not staff_user or staff_user.role != 'staff':
                return api_response(False, "Assigned staff member not found or is not staff.", None, 400)
            trek.assigned_staff_id = staff_user.id
        else:
            trek.assigned_staff_id = None

    if 'is_deleted' in data:
        trek.is_deleted = bool(data['is_deleted'])

    db.session.commit()
    return api_response(True, "Trek updated successfully.", trek.to_dict(), 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    active_bookings = trek.bookings.filter_by(status='Booked').count()
    if active_bookings > 0:
        # Soft delete by marking is_deleted = True and status = Closed
        trek.is_deleted = True
        trek.status = 'Closed'
        db.session.commit()
        return api_response(
            True,
            "Trek has active bookings, so it was soft-deleted (marked is_deleted=True and Closed).",
            trek.to_dict(),
            200
        )

    # If no bookings exist, perform soft delete as per schema flag
    trek.is_deleted = True
    db.session.commit()
    return api_response(True, "Trek soft deleted successfully.", None, 200)


# -------------------------------------------------------------
# Bookings Management (Admin View & Status Updates)
# -------------------------------------------------------------
@admin_bp.route('/bookings', methods=['GET'])
@login_required
@role_required('admin')
def list_bookings():
    status = request.args.get('status')
    trek_id = request.args.get('trek_id')
    user_id = request.args.get('user_id')

    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    if trek_id:
        try:
            query = query.filter_by(trek_id=int(trek_id))
        except ValueError:
            return api_response(False, "Invalid trek_id.", None, 400)
    if user_id:
        try:
            query = query.filter_by(user_id=int(user_id))
        except ValueError:
            return api_response(False, "Invalid user_id.", None, 400)

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return api_response(True, "Bookings retrieved.", [b.to_dict() for b in bookings], 200)


@admin_bp.route('/bookings/<int:booking_id>/status', methods=['PUT'])
@login_required
@role_required('admin')
def update_booking_status(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return api_response(False, "Booking not found.", None, 404)

    data = request.get_json(silent=True) or {}
    status = data.get('status')
    payment_status = data.get('payment_status')

    if status:
        if status not in ['Booked', 'Cancelled', 'Completed']:
            return api_response(False, "Invalid status ('Booked', 'Cancelled', 'Completed').", None, 400)
        old_status = booking.status
        booking.status = status
        if status == 'Cancelled' and old_status != 'Cancelled':
            booking.cancelled_at = datetime.utcnow()
        # Recalculate trek slots
        if booking.trek:
            booking.trek.recalculate_available_slots()

    if payment_status:
        if payment_status not in ['Pending', 'Paid', 'NA']:
            return api_response(False, "Invalid payment status ('Pending', 'Paid', 'NA').", None, 400)
        booking.payment_status = payment_status

    db.session.commit()
    return api_response(True, "Booking status updated.", booking.to_dict(), 200)


# -------------------------------------------------------------
# User / Trekker Account Management
# -------------------------------------------------------------
@admin_bp.route('/users', methods=['GET'])
@login_required
@role_required('admin')
def list_users():
    users = User.query.filter_by(role='user').order_by(User.id.desc()).all()
    return api_response(True, "Users retrieved.", [u.to_dict() for u in users], 200)


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@login_required
@role_required('admin')
def update_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return api_response(False, "User not found.", None, 404)

    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ['active', 'inactive', 'blacklisted']:
        return api_response(False, "Invalid status ('active', 'inactive', 'blacklisted').", None, 400)

    user.status = status
    db.session.commit()
    return api_response(True, f"User status updated to {status}.", user.to_dict(), 200)
