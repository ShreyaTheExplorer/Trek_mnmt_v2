import re
from datetime import datetime, date
from collections import defaultdict
from flask import Blueprint, request, g
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification
from auth import api_response, login_required, role_required
from cache import invalidate_trek_cache

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PHONE_REGEX = re.compile(r'^\+?[0-9\s\-]{7,20}$')

# -------------------------------------------------------------
# 1. Dashboard Overview
# -------------------------------------------------------------
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('admin')
def get_dashboard():
    """
    Summary metrics: total treks, total users, total staff, total bookings,
    plus counts of treks by status and bookings by status.
    """
    total_treks = Trek.query.filter_by(is_deleted=False).count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    # Breakdown of treks by status
    trek_statuses = ['Pending', 'Approved', 'Open', 'Closed', 'Completed']
    treks_by_status = {status: 0 for status in trek_statuses}
    all_treks = Trek.query.filter_by(is_deleted=False).all()
    for t in all_treks:
        if t.status in treks_by_status:
            treks_by_status[t.status] += 1
        else:
            treks_by_status[t.status] = 1

    # Breakdown of bookings by status
    booking_statuses = ['Booked', 'Cancelled', 'Completed']
    bookings_by_status = {status: 0 for status in booking_statuses}
    all_bookings = Booking.query.all()
    for b in all_bookings:
        if b.status in bookings_by_status:
            bookings_by_status[b.status] += 1
        else:
            bookings_by_status[b.status] = 1

    # Total revenue from active and completed bookings
    revenue = sum(
        (b.participants_count * b.trek.price)
        for b in all_bookings if b.status in ['Booked', 'Completed'] and b.trek
    )

    return api_response(
        True,
        "Admin dashboard metrics retrieved.",
        {
            'total_treks': total_treks,
            'total_users': total_users,
            'total_staff': total_staff,
            'total_bookings': total_bookings,
            'total_revenue': round(revenue, 2),
            'treks_by_status': treks_by_status,
            'bookings_by_status': bookings_by_status
        },
        200
    )


# -------------------------------------------------------------
# 2. Trek Management (CRUD)
# -------------------------------------------------------------
@admin_bp.route('/treks', methods=['POST'])
@login_required
@role_required('admin')
def create_trek():
    """
    Create a new trek.
    Validates dates (end >= start), difficulty enum ('Easy'|'Moderate'|'Hard'),
    slots >= 0, and sets available_slots = total_slots on create.
    Admin can set status Pending->Approved->Open etc.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    location = (data.get('location') or '').strip()
    difficulty = (data.get('difficulty') or 'Moderate').strip()
    duration_days = data.get('duration_days', 1)
    total_slots = data.get('total_slots')
    price = data.get('price', 0.0)
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    description = (data.get('description') or '').strip()
    instructions = (data.get('instructions') or '').strip() or None
    assigned_staff_id = data.get('assigned_staff_id')
    status = (data.get('status') or 'Pending').strip()

    # Validations
    if not name or len(name) < 3:
        return api_response(False, "Trek name is required and must be at least 3 characters.", None, 400)
    if not location:
        return api_response(False, "Location is required.", None, 400)
    if difficulty not in ['Easy', 'Moderate', 'Hard']:
        return api_response(False, "Difficulty must be one of: 'Easy', 'Moderate', 'Hard'.", None, 400)
    if status not in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
        return api_response(False, "Status must be: 'Pending', 'Approved', 'Open', 'Closed', 'Completed'.", None, 400)
    if not description or len(description) < 10:
        return api_response(False, "Description is required and must be at least 10 characters.", None, 400)

    try:
        duration_days = int(duration_days)
        if duration_days <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Duration days must be a positive integer.", None, 400)

    try:
        total_slots = int(total_slots)
        if total_slots < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Total slots must be an integer greater than or equal to 0.", None, 400)

    try:
        price = float(price)
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Price must be a non-negative number.", None, 400)

    # Date validations
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return api_response(False, "start_date and end_date must be provided in YYYY-MM-DD format.", None, 400)

    if end_date < start_date:
        return api_response(False, "end_date cannot be earlier than start_date.", None, 400)

    # Validate staff assignment if provided (must be active staff)
    if assigned_staff_id:
        staff_user = db.session.get(User, assigned_staff_id)
        if not staff_user or staff_user.role != 'staff':
            return api_response(False, "Assigned user not found or does not have role 'staff'.", None, 400)
        if staff_user.status != 'active':
            return api_response(False, f"Cannot assign staff with status '{staff_user.status}'. Only active staff can be assigned.", None, 400)
    else:
        assigned_staff_id = None

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty,
        duration_days=duration_days,
        total_slots=total_slots,
        available_slots=total_slots, # Rule: set available_slots = total_slots on create
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

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(True, "Trek created successfully.", trek.to_dict(), 201)


@admin_bp.route('/treks', methods=['GET'])
@login_required
@role_required('admin')
def list_treks():
    """
    List treks with search by name/location and filter by status.
    """
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

    query = Trek.query
    if not include_deleted:
        query = query.filter_by(is_deleted=False)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Trek.name.ilike(search_pattern)) |
            (Trek.location.ilike(search_pattern))
        )

    if status:
        query = query.filter(Trek.status.ilike(status))

    treks = query.order_by(Trek.id.desc()).all()
    return api_response(True, "Treks retrieved.", [t.to_dict() for t in treks], 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_trek(trek_id):
    """
    Get detailed trek information including booking roster.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    data = trek.to_dict()
    data['bookings'] = [b.to_dict() for b in trek.bookings.all()]
    return api_response(True, "Trek details retrieved.", data, 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_trek(trek_id):
    """
    Update trek details.
    Validates dates (end >= start), difficulty enum, slots >= 0,
    and updates available_slots accordingly.
    Admin can set status Pending->Approved->Open etc.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = (data['name'] or '').strip()
        if len(name) < 3:
            return api_response(False, "Trek name must be at least 3 characters.", None, 400)
        trek.name = name

    if 'location' in data:
        loc = (data['location'] or '').strip()
        if not loc:
            return api_response(False, "Location cannot be empty.", None, 400)
        trek.location = loc

    if 'difficulty' in data:
        diff = (data['difficulty'] or '').strip()
        if diff not in ['Easy', 'Moderate', 'Hard']:
            return api_response(False, "Difficulty must be one of: 'Easy', 'Moderate', 'Hard'.", None, 400)
        trek.difficulty = diff

    if 'status' in data:
        st = (data['status'] or '').strip()
        if st not in ['Pending', 'Approved', 'Open', 'Closed', 'Completed']:
            return api_response(False, "Status must be: 'Pending', 'Approved', 'Open', 'Closed', 'Completed'.", None, 400)
        trek.status = st

    if 'duration_days' in data:
        try:
            d = int(data['duration_days'])
            if d <= 0:
                raise ValueError
            trek.duration_days = d
        except (TypeError, ValueError):
            return api_response(False, "Duration days must be a positive integer.", None, 400)

    # Date validations
    new_start = trek.start_date
    new_end = trek.end_date
    if 'start_date' in data:
        try:
            new_start = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "start_date must be in YYYY-MM-DD format.", None, 400)
    if 'end_date' in data:
        try:
            new_end = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "end_date must be in YYYY-MM-DD format.", None, 400)

    if new_end < new_start:
        return api_response(False, "end_date cannot be earlier than start_date.", None, 400)

    trek.start_date = new_start
    trek.end_date = new_end

    # Slot updates: slots >= 0, and total_slots cannot be less than active booked slots
    if 'total_slots' in data:
        try:
            slots = int(data['total_slots'])
            if slots < 0:
                raise ValueError
            active_booked = sum(b.participants_count for b in trek.bookings.filter_by(status='Booked').all())
            if slots < active_booked:
                return api_response(
                    False,
                    f"Total slots cannot be less than already booked participants ({active_booked}).",
                    None,
                    400
                )
            trek.total_slots = slots
            trek.recalculate_available_slots()
        except (TypeError, ValueError):
            return api_response(False, "Total slots must be an integer >= 0.", None, 400)

    if 'price' in data:
        try:
            p = float(data['price'])
            if p < 0:
                raise ValueError
            trek.price = p
        except (TypeError, ValueError):
            return api_response(False, "Price must be a non-negative number.", None, 400)

    if 'description' in data:
        desc = (data['description'] or '').strip()
        if len(desc) < 10:
            return api_response(False, "Description must be at least 10 characters.", None, 400)
        trek.description = desc

    if 'instructions' in data:
        trek.instructions = (data['instructions'] or '').strip() or None

    if 'assigned_staff_id' in data:
        s_id = data['assigned_staff_id']
        if s_id:
            staff_user = db.session.get(User, s_id)
            if not staff_user or staff_user.role != 'staff':
                return api_response(False, "Assigned user is not staff.", None, 400)
            if staff_user.status != 'active':
                return api_response(False, f"Cannot assign staff with status '{staff_user.status}'. Only active staff can be assigned.", None, 400)
            trek.assigned_staff_id = staff_user.id
        else:
            trek.assigned_staff_id = None

    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(True, "Trek updated successfully.", trek.to_dict(), 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_trek(trek_id):
    """
    Soft delete a trek.
    If active bookings exist:
      - By default blocks deletion with a 400 error.
      - If cancel_bookings=true is passed, cancels active bookings automatically and soft-deletes.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    cancel_bookings = request.args.get('cancel_bookings', 'false').lower() == 'true'
    active_bookings = trek.bookings.filter_by(status='Booked').all()

    if active_bookings:
        if not cancel_bookings:
            return api_response(
                False,
                f"Cannot delete trek with {len(active_bookings)} active booking(s). Pass 'cancel_bookings=true' to cancel them automatically.",
                {'active_bookings_count': len(active_bookings)},
                400
            )
        # Cancel all active bookings
        now = datetime.utcnow()
        for b in active_bookings:
            b.status = 'Cancelled'
            b.cancelled_at = now
            # Send notification to trekker
            notif = Notification(
                user_id=b.user_id,
                message=f"Your booking for trek '{trek.name}' has been cancelled because the trek was cancelled by administration."
            )
            db.session.add(notif)

    trek.is_deleted = True
    trek.status = 'Closed'
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(True, "Trek soft deleted successfully.", trek.to_dict(), 200)


# -------------------------------------------------------------
# 3. Staff Management & Assignment
# -------------------------------------------------------------
@admin_bp.route('/staff', methods=['POST'])
@login_required
@role_required('admin')
def create_staff():
    """
    Create a new staff member (creates User with role='staff' plus a StaffProfile).
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    phone = (data.get('phone') or '').strip()
    contact_details = (data.get('contact_details') or '').strip() or None
    specialization = (data.get('specialization') or '').strip() or 'General Guide'

    if not name or len(name) < 2:
        return api_response(False, "Name must be at least 2 characters.", None, 400)
    if not email or not EMAIL_REGEX.match(email):
        return api_response(False, "A valid email address is required.", None, 400)
    if not phone or not PHONE_REGEX.match(phone):
        return api_response(False, "A valid phone number is required.", None, 400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters.", None, 400)

    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", None, 409)

    staff_user = User(
        name=name,
        email=email,
        phone=phone,
        role='staff',
        status='active'
    )
    staff_user.set_password(password)
    db.session.add(staff_user)
    db.session.flush()

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


@admin_bp.route('/staff', methods=['GET'])
@login_required
@role_required('admin')
def list_staff():
    """
    List staff members with search by name, email, phone, or specialization.
    """
    search = request.args.get('search', '').strip()
    query = User.query.filter_by(role='staff')

    if search:
        search_pattern = f"%{search}%"
        query = query.outerjoin(StaffProfile).filter(
            (User.name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.phone.ilike(search_pattern)) |
            (StaffProfile.specialization.ilike(search_pattern))
        )

    staff_list = query.order_by(User.id.desc()).all()
    return api_response(True, "Staff list retrieved.", [s.to_dict() for s in staff_list], 200)


@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_staff(staff_id):
    """
    Update staff user fields and StaffProfile.
    """
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = (data['name'] or '').strip()
        if len(name) < 2:
            return api_response(False, "Name must be at least 2 characters.", None, 400)
        staff.name = name

    if 'phone' in data:
        phone = (data['phone'] or '').strip()
        if phone:
            if not PHONE_REGEX.match(phone):
                return api_response(False, "Invalid phone number format.", None, 400)
            staff.phone = phone
        else:
            staff.phone = None

    if 'age' in data:
        staff.age = int(data['age']) if data['age'] else None
    if 'emergency_contact' in data:
        staff.emergency_contact = (data['emergency_contact'] or '').strip() or None
    if 'address' in data:
        staff.address = (data['address'] or '').strip() or None

    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return api_response(False, "Password must be at least 6 characters.", None, 400)
        staff.set_password(data['password'])

    # Profile updates
    profile = staff.staff_profile
    if not profile:
        profile = StaffProfile(user_id=staff.id)
        db.session.add(profile)

    if 'contact_details' in data:
        profile.contact_details = data['contact_details']
    if 'specialization' in data:
        profile.specialization = data['specialization']

    db.session.commit()
    return api_response(True, "Staff member updated.", staff.to_dict(), 200)


@admin_bp.route('/staff/<int:staff_id>/status', methods=['PATCH'])
@login_required
@role_required('admin')
def update_staff_status(staff_id):
    """
    Update staff status: active / inactive / blacklisted.
    """
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)

    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ['active', 'inactive', 'blacklisted']:
        return api_response(False, "Status must be 'active', 'inactive', or 'blacklisted'.", None, 400)

    staff.status = status
    if staff.staff_profile:
        staff.staff_profile.status = 'active' if status == 'active' else 'inactive'

    db.session.commit()
    return api_response(True, f"Staff status updated to '{status}'.", staff.to_dict(), 200)


@admin_bp.route('/treks/<int:trek_id>/assign', methods=['POST'])
@login_required
@role_required('admin')
def assign_staff_to_trek(trek_id):
    """
    Assign staff to a trek: POST /treks/<id>/assign {staff_id}.
    Rule: Only ACTIVE staff can be assigned.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    data = request.get_json(silent=True) or {}
    staff_id = data.get('staff_id')

    if staff_id is None:
        # Unassign staff
        trek.assigned_staff_id = None
        db.session.commit()
        invalidate_trek_cache(trek.id)
        return api_response(True, "Staff unassigned from trek successfully.", trek.to_dict(), 200)

    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "User not found or is not a staff member.", None, 400)

    if staff.status != 'active':
        return api_response(
            False,
            f"Cannot assign staff with status '{staff.status}'. Only active staff can be assigned.",
            None,
            400
        )

    trek.assigned_staff_id = staff.id
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(
        True,
        f"Staff '{staff.name}' successfully assigned to trek '{trek.name}'.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# 4. User / Trekker Management
# -------------------------------------------------------------
@admin_bp.route('/users', methods=['GET'])
@login_required
@role_required('admin')
def list_users():
    """
    Get users (search by name/email, filter by status).
    """
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = User.query.filter_by(role='user')

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )

    if status:
        query = query.filter(User.status.ilike(status))

    users = query.order_by(User.id.desc()).all()
    return api_response(True, "Users retrieved.", [u.to_dict() for u in users], 200)


@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@login_required
@role_required('admin')
def update_user_status(user_id):
    """
    Update user status: active / inactive / blacklisted.
    Rule: Admin cannot modify themselves.
    """
    if user_id == g.current_user.id:
        return api_response(False, "Admin cannot modify their own account status.", None, 400)

    user = db.session.get(User, user_id)
    if not user:
        return api_response(False, "User not found.", None, 404)

    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ['active', 'inactive', 'blacklisted']:
        return api_response(False, "Status must be 'active', 'inactive', or 'blacklisted'.", None, 400)

    user.status = status
    db.session.commit()

    return api_response(True, f"User status updated to '{status}'.", user.to_dict(), 200)


# -------------------------------------------------------------
# 5. Bookings Overview (Historical & Filterable)
# -------------------------------------------------------------
@admin_bp.route('/bookings', methods=['GET'])
@login_required
@role_required('admin')
def list_all_bookings():
    """
    All bookings with user and trek info, filterable by trek, user, and status.
    Includes historical data including completed and cancelled.
    """
    trek_id = request.args.get('trek_id')
    user_id = request.args.get('user_id')
    status = request.args.get('status')

    query = Booking.query

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

    if status:
        query = query.filter(Booking.status.ilike(status))

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return api_response(True, "Bookings retrieved.", [b.to_dict() for b in bookings], 200)


# -------------------------------------------------------------
# 6. Unified Search Endpoint
# -------------------------------------------------------------
@admin_bp.route('/search', methods=['GET'])
@login_required
@role_required('admin')
def unified_search():
    """
    Unified search endpoint: GET /search?q=&type=users|staff|treks
    """
    q = request.args.get('q', '').strip()
    search_type = request.args.get('type', '').strip().lower()

    if not q:
        return api_response(False, "Query parameter 'q' is required.", None, 400)

    pattern = f"%{q}%"
    results = {}

    if not search_type or search_type == 'users':
        users = User.query.filter(
            User.role == 'user',
            (User.name.ilike(pattern)) | (User.email.ilike(pattern)) | (User.phone.ilike(pattern))
        ).limit(20).all()
        results['users'] = [u.to_dict() for u in users]

    if not search_type or search_type == 'staff':
        staff = User.query.outerjoin(StaffProfile).filter(
            User.role == 'staff',
            (User.name.ilike(pattern)) | (User.email.ilike(pattern)) | (StaffProfile.specialization.ilike(pattern))
        ).limit(20).all()
        results['staff'] = [s.to_dict() for s in staff]

    if not search_type or search_type == 'treks':
        treks = Trek.query.filter(
            Trek.is_deleted == False,
            (Trek.name.ilike(pattern)) | (Trek.location.ilike(pattern)) | (Trek.description.ilike(pattern))
        ).limit(20).all()
        results['treks'] = [t.to_dict() for t in treks]

    return api_response(True, f"Search results for '{q}'.", results, 200)


# -------------------------------------------------------------
# 7. Chart-Ready Analytics Stats
# -------------------------------------------------------------
@admin_bp.route('/stats', methods=['GET'])
@login_required
@role_required('admin')
def get_stats():
    """
    Analytics stats: popular treks (top by booking count),
    bookings per month, and users participated.
    Returns chart-ready arrays for easy Chart.js integration.
    """
    all_bookings = Booking.query.all()

    # 1. Popular treks (top by active/completed bookings)
    trek_counts = defaultdict(lambda: {'trek_name': '', 'bookings': 0, 'participants': 0})
    for b in all_bookings:
        if b.trek and not b.trek.is_deleted and b.status in ['Booked', 'Completed']:
            t_id = b.trek_id
            trek_counts[t_id]['trek_name'] = b.trek.name
            trek_counts[t_id]['bookings'] += 1
            trek_counts[t_id]['participants'] += b.participants_count

    popular_treks = sorted(trek_counts.values(), key=lambda x: x['bookings'], reverse=True)[:10]

    # 2. Bookings per month (YYYY-MM)
    monthly_data = defaultdict(lambda: {'count': 0, 'participants': 0, 'revenue': 0.0})
    for b in all_bookings:
        if b.booking_date:
            month_key = b.booking_date.strftime('%Y-%m')
            monthly_data[month_key]['count'] += 1
            monthly_data[month_key]['participants'] += b.participants_count
            if b.status in ['Booked', 'Completed'] and b.trek:
                monthly_data[month_key]['revenue'] += (b.participants_count * b.trek.price)

    bookings_per_month = [
        {
            'month': m,
            'count': data['count'],
            'participants': data['participants'],
            'revenue': round(data['revenue'], 2)
        }
        for m, data in sorted(monthly_data.items())
    ]

    # 3. Users participated by booking status breakdown
    status_counts = defaultdict(int)
    for b in all_bookings:
        status_counts[b.status] += b.participants_count

    users_participated = [
        {'status': st, 'total_participants': status_counts[st]}
        for st in ['Booked', 'Completed', 'Cancelled']
    ]

    return api_response(
        True,
        "Chart-ready analytics retrieved.",
        {
            'popular_treks': popular_treks,
            'bookings_per_month': bookings_per_month,
            'users_participated': users_participated
        },
        200
    )
