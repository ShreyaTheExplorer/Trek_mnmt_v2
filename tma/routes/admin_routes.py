import re
from datetime import datetime, date
from flask import Blueprint, request, g
from extensions import db
from models import User, Trek, TrekBatch, Booking, Review
from auth import api_response, login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

# -------------------------------------------------------------
# Admin Dashboard / Summary Analytics
# -------------------------------------------------------------
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('admin')
def get_dashboard_stats():
    total_treks = Trek.query.count()
    active_treks = Trek.query.filter_by(is_active=True).count()
    total_batches = TrekBatch.query.count()
    upcoming_batches = TrekBatch.query.filter_by(status='upcoming').count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    
    confirmed_bookings = Booking.query.filter_by(status='confirmed').all()
    total_bookings = len(confirmed_bookings)
    total_revenue = sum(b.total_amount for b in confirmed_bookings)
    total_trekkers = sum(b.num_trekkers for b in confirmed_bookings)

    recent_bookings = Booking.query.order_by(Booking.booked_at.desc()).limit(5).all()

    return api_response(
        True,
        "Admin dashboard statistics retrieved.",
        {
            'stats': {
                'total_treks': total_treks,
                'active_treks': active_treks,
                'total_batches': total_batches,
                'upcoming_batches': upcoming_batches,
                'total_users': total_users,
                'total_staff': total_staff,
                'total_bookings': total_bookings,
                'total_trekkers': total_trekkers,
                'total_revenue': round(total_revenue, 2)
            },
            'recent_bookings': [b.to_dict() for b in recent_bookings]
        },
        200
    )


# -------------------------------------------------------------
# Staff Management Endpoints
# -------------------------------------------------------------
@admin_bp.route('/staff', methods=['GET'])
@login_required
@role_required('admin')
def list_staff():
    staff_members = User.query.filter_by(role='staff').order_by(User.full_name).all()
    return api_response(
        True,
        "Staff list retrieved.",
        [s.to_dict() for s in staff_members],
        200
    )


@admin_bp.route('/staff', methods=['POST'])
@login_required
@role_required('admin')
def create_staff():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    full_name = (data.get('full_name') or '').strip()
    password = data.get('password') or ''

    if not email or not EMAIL_REGEX.match(email):
        return api_response(False, "A valid email address is required.", None, 400)
    if not full_name or len(full_name) < 2:
        return api_response(False, "Full name must be at least 2 characters.", None, 400)
    if not password or len(password) < 6:
        return api_response(False, "Password must be at least 6 characters.", None, 400)

    if User.query.filter_by(email=email).first():
        return api_response(False, "An account with this email already exists.", None, 409)

    staff = User(
        email=email,
        full_name=full_name,
        role='staff',
        is_active=True
    )
    staff.set_password(password)
    db.session.add(staff)
    db.session.commit()

    return api_response(True, "Staff account created successfully.", staff.to_dict(), 201)


@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_staff(staff_id):
    staff = db.session.get(User, staff_id)
    if not staff or staff.role != 'staff':
        return api_response(False, "Staff member not found.", None, 404)

    data = request.get_json(silent=True) or {}
    if 'full_name' in data:
        name = data['full_name'].strip()
        if len(name) < 2:
            return api_response(False, "Full name must be at least 2 characters.", None, 400)
        staff.full_name = name

    if 'is_active' in data:
        staff.is_active = bool(data['is_active'])

    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return api_response(False, "Password must be at least 6 characters.", None, 400)
        staff.set_password(data['password'])

    db.session.commit()
    return api_response(True, "Staff account updated.", staff.to_dict(), 200)


# -------------------------------------------------------------
# Trek Management Endpoints (CRUD)
# -------------------------------------------------------------
@admin_bp.route('/treks', methods=['GET'])
@login_required
@role_required('admin')
def list_treks():
    treks = Trek.query.order_by(Trek.id.desc()).all()
    return api_response(
        True,
        "All treks retrieved.",
        [t.to_dict(include_batches=True) for t in treks],
        200
    )


@admin_bp.route('/treks', methods=['POST'])
@login_required
@role_required('admin')
def create_trek():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    location = (data.get('location') or '').strip()
    difficulty = (data.get('difficulty') or 'Moderate').strip()
    duration_days = data.get('duration_days')
    base_price = data.get('base_price')
    max_altitude = data.get('max_altitude')

    if not name or len(name) < 3:
        return api_response(False, "Trek name must be at least 3 characters.", None, 400)
    if not description or len(description) < 10:
        return api_response(False, "Description must be at least 10 characters.", None, 400)
    if not location:
        return api_response(False, "Location is required.", None, 400)
    if difficulty not in ['Easy', 'Moderate', 'Challenging', 'Difficult']:
        return api_response(False, "Difficulty must be Easy, Moderate, Challenging, or Difficult.", None, 400)

    try:
        duration_days = int(duration_days)
        if duration_days <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Duration days must be a positive integer.", None, 400)

    try:
        base_price = float(base_price)
        if base_price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Base price must be a non-negative number.", None, 400)

    if max_altitude is not None and str(max_altitude).strip():
        try:
            max_altitude = int(max_altitude)
        except (TypeError, ValueError):
            return api_response(False, "Max altitude must be an integer.", None, 400)
    else:
        max_altitude = None

    if Trek.query.filter(Trek.name.ilike(name)).first():
        return api_response(False, "A trek with this name already exists.", None, 409)

    trek = Trek(
        name=name,
        description=description,
        location=location,
        difficulty=difficulty,
        duration_days=duration_days,
        base_price=base_price,
        max_altitude=max_altitude,
        is_active=True
    )
    db.session.add(trek)
    db.session.commit()

    return api_response(True, "Trek created successfully.", trek.to_dict(), 201)


@admin_bp.route('/treks/<int:trek_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)
    return api_response(True, "Trek details retrieved.", trek.to_dict(include_batches=True), 200)


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
        existing = Trek.query.filter(Trek.name.ilike(name), Trek.id != trek.id).first()
        if existing:
            return api_response(False, "Another trek already has this name.", None, 409)
        trek.name = name

    if 'description' in data:
        desc = data['description'].strip()
        if len(desc) < 10:
            return api_response(False, "Description must be at least 10 characters.", None, 400)
        trek.description = desc

    if 'location' in data:
        loc = data['location'].strip()
        if not loc:
            return api_response(False, "Location cannot be empty.", None, 400)
        trek.location = loc

    if 'difficulty' in data:
        diff = data['difficulty'].strip()
        if diff not in ['Easy', 'Moderate', 'Challenging', 'Difficult']:
            return api_response(False, "Invalid difficulty value.", None, 400)
        trek.difficulty = diff

    if 'duration_days' in data:
        try:
            d = int(data['duration_days'])
            if d <= 0:
                raise ValueError
            trek.duration_days = d
        except (TypeError, ValueError):
            return api_response(False, "Duration days must be a positive integer.", None, 400)

    if 'base_price' in data:
        try:
            p = float(data['base_price'])
            if p < 0:
                raise ValueError
            trek.base_price = p
        except (TypeError, ValueError):
            return api_response(False, "Base price must be a non-negative number.", None, 400)

    if 'max_altitude' in data:
        alt = data['max_altitude']
        if alt is not None and str(alt).strip():
            try:
                trek.max_altitude = int(alt)
            except (TypeError, ValueError):
                return api_response(False, "Max altitude must be an integer.", None, 400)
        else:
            trek.max_altitude = None

    if 'is_active' in data:
        trek.is_active = bool(data['is_active'])

    db.session.commit()
    return api_response(True, "Trek updated successfully.", trek.to_dict(include_batches=True), 200)


@admin_bp.route('/treks/<int:trek_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_trek(trek_id):
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return api_response(False, "Trek not found.", None, 404)

    # Check if there are active bookings
    active_bookings = Booking.query.join(TrekBatch).filter(
        TrekBatch.trek_id == trek_id,
        Booking.status == 'confirmed'
    ).count()

    if active_bookings > 0:
        # Soft delete by deactivating
        trek.is_active = False
        db.session.commit()
        return api_response(
            True,
            "Trek has active bookings, so it was deactivated instead of permanently deleted.",
            trek.to_dict(),
            200
        )

    db.session.delete(trek)
    db.session.commit()
    return api_response(True, "Trek deleted successfully.", None, 200)


# -------------------------------------------------------------
# Batch Management Endpoints
# -------------------------------------------------------------
@admin_bp.route('/batches', methods=['GET'])
@login_required
@role_required('admin')
def list_batches():
    trek_id = request.args.get('trek_id')
    query = TrekBatch.query

    if trek_id:
        try:
            query = query.filter_by(trek_id=int(trek_id))
        except ValueError:
            return api_response(False, "Invalid trek_id.", None, 400)

    batches = query.order_by(TrekBatch.start_date.desc()).all()
    return api_response(True, "Batches retrieved.", [b.to_dict() for b in batches], 200)


@admin_bp.route('/batches', methods=['POST'])
@login_required
@role_required('admin')
def create_batch():
    data = request.get_json(silent=True) or {}
    trek_id = data.get('trek_id')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    capacity = data.get('capacity')
    price = data.get('price')
    staff_id = data.get('staff_id')

    # Validate trek
    trek = db.session.get(Trek, trek_id) if trek_id else None
    if not trek:
        return api_response(False, "Valid trek_id is required.", None, 400)

    # Parse and validate dates
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return api_response(False, "Dates must be in YYYY-MM-DD format.", None, 400)

    if end_date < start_date:
        return api_response(False, "End date cannot be earlier than start date.", None, 400)

    # Validate capacity & price
    try:
        capacity = int(capacity)
        if capacity <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Capacity must be a positive integer.", None, 400)

    try:
        price = float(price) if price is not None else float(trek.base_price)
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "Price must be a non-negative number.", None, 400)

    # Validate optional staff
    if staff_id:
        staff = db.session.get(User, staff_id)
        if not staff or staff.role != 'staff':
            return api_response(False, "Assigned staff member not found or is not staff.", None, 400)
    else:
        staff_id = None

    batch = TrekBatch(
        trek_id=trek.id,
        start_date=start_date,
        end_date=end_date,
        capacity=capacity,
        price=price,
        status='upcoming',
        staff_id=staff_id
    )
    db.session.add(batch)
    db.session.commit()

    return api_response(True, "Batch created successfully.", batch.to_dict(), 201)


@admin_bp.route('/batches/<int:batch_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_batch(batch_id):
    batch = db.session.get(TrekBatch, batch_id)
    if not batch:
        return api_response(False, "Batch not found.", None, 404)

    data = request.get_json(silent=True) or {}

    if 'start_date' in data:
        try:
            batch.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "Start date must be in YYYY-MM-DD format.", None, 400)

    if 'end_date' in data:
        try:
            batch.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return api_response(False, "End date must be in YYYY-MM-DD format.", None, 400)

    if batch.end_date < batch.start_date:
        return api_response(False, "End date cannot be earlier than start date.", None, 400)

    if 'capacity' in data:
        try:
            cap = int(data['capacity'])
            if cap < batch.booked_count:
                return api_response(
                    False,
                    f"Capacity cannot be less than already booked slots ({batch.booked_count}).",
                    None,
                    400
                )
            batch.capacity = cap
        except (TypeError, ValueError):
            return api_response(False, "Capacity must be a positive integer.", None, 400)

    if 'price' in data:
        try:
            p = float(data['price'])
            if p < 0:
                raise ValueError
            batch.price = p
        except (TypeError, ValueError):
            return api_response(False, "Price must be a non-negative number.", None, 400)

    if 'status' in data:
        st = data['status']
        if st not in ['upcoming', 'in_progress', 'completed', 'cancelled']:
            return api_response(False, "Invalid status value.", None, 400)
        batch.status = st

    if 'staff_id' in data:
        s_id = data['staff_id']
        if s_id:
            staff = db.session.get(User, s_id)
            if not staff or staff.role != 'staff':
                return api_response(False, "Staff member not found.", None, 400)
            batch.staff_id = staff.id
        else:
            batch.staff_id = None

    db.session.commit()
    return api_response(True, "Batch updated successfully.", batch.to_dict(), 200)


@admin_bp.route('/batches/<int:batch_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_batch(batch_id):
    batch = db.session.get(TrekBatch, batch_id)
    if not batch:
        return api_response(False, "Batch not found.", None, 404)

    if batch.booked_count > 0:
        batch.status = 'cancelled'
        db.session.commit()
        return api_response(
            True,
            "Batch has bookings, so its status was updated to cancelled instead of deleted.",
            batch.to_dict(),
            200
        )

    db.session.delete(batch)
    db.session.commit()
    return api_response(True, "Batch deleted successfully.", None, 200)


# -------------------------------------------------------------
# All Bookings Overview
# -------------------------------------------------------------
@admin_bp.route('/bookings', methods=['GET'])
@login_required
@role_required('admin')
def list_all_bookings():
    status = request.args.get('status')
    batch_id = request.args.get('batch_id')

    query = Booking.query
    if status:
        query = query.filter_by(status=status)
    if batch_id:
        try:
            query = query.filter_by(batch_id=int(batch_id))
        except ValueError:
            return api_response(False, "Invalid batch_id.", None, 400)

    bookings = query.order_by(Booking.booked_at.desc()).all()
    return api_response(True, "Bookings retrieved.", [b.to_dict() for b in bookings], 200)
