import os
from datetime import datetime, date
from flask import Blueprint, request, g, send_from_directory, current_app
from extensions import db
from models import Trek, Booking, Notification, User
from auth import api_response, login_required, role_required
from cache import invalidate_trek_cache

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# -------------------------------------------------------------
# 1. Trek Exploration & Catalog (Paginated with Filters)
# -------------------------------------------------------------
@user_bp.route('/treks', methods=['GET'])
@login_required
@role_required('user')
def list_treks():
    """
    List treks that are Approved or Open and not deleted.
    Query params:
      - q: search by trek name (substring, case-insensitive)
      - location: filter by location
      - difficulty: 'Easy', 'Moderate', 'Hard'
      - min_days: duration_days >= min_days
      - max_days: duration_days <= max_days
      - status: 'Approved', 'Open' (or specific status requested)
      - page: page number (default 1)
      - per_page: items per page (default 10)
    """
    q = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    min_days = request.args.get('min_days')
    max_days = request.args.get('max_days')
    status_filter = request.args.get('status', '').strip()

    # Pagination parameters
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = min(50, max(1, int(request.args.get('per_page', 10))))
    except (TypeError, ValueError):
        per_page = 10

    # Base query: non-deleted, only Approved or Open
    query = Trek.query.filter(
        Trek.is_deleted == False,
        Trek.status.in_(['Approved', 'Open'])
    )

    if q:
        query = query.filter(Trek.name.ilike(f"%{q}%"))

    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    if difficulty:
        query = query.filter(Trek.difficulty.ilike(difficulty))

    if min_days:
        try:
            query = query.filter(Trek.duration_days >= int(min_days))
        except ValueError:
            pass

    if max_days:
        try:
            query = query.filter(Trek.duration_days <= int(max_days))
        except ValueError:
            pass

    if status_filter:
        if status_filter in ['Approved', 'Open']:
            query = query.filter(Trek.status == status_filter)

    query = query.order_by(Trek.start_date.asc())

    # Paginate query
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    treks = query.offset(offset).limit(per_page).all()

    return api_response(
        True,
        "Available treks retrieved.",
        {
            'treks': [t.to_dict() for t in treks],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        },
        200
    )


@user_bp.route('/treks/<int:trek_id>', methods=['GET'])
@login_required
@role_required('user')
def get_trek(trek_id):
    """
    Get single trek details.
    Must be Approved or Open, and not deleted.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted or trek.status not in ['Approved', 'Open']:
        return api_response(False, "Trek not found or not available.", None, 404)

    return api_response(True, "Trek details retrieved.", trek.to_dict(), 200)


# -------------------------------------------------------------
# 2. Bookings & Business Logic
# -------------------------------------------------------------
@user_bp.route('/bookings', methods=['POST'])
@login_required
@role_required('user')
def create_booking():
    """
    Create a booking inside a database transaction enforcing all business rules:
      1. Trek status must be 'Open' (else 400).
      2. No duplicate active booking for the same user and trek (else 409).
      3. available_slots must be >= participants_count, never go negative (else 409 'Fully booked').
      4. Decrement available_slots; create booking with status 'Booked'.
      5. Create a Notification 'Booking confirmed'.
    """
    data = request.get_json(silent=True) or {}
    trek_id = data.get('trek_id')
    participants_count = data.get('participants_count', 1)

    if not trek_id:
        return api_response(False, "trek_id is required.", None, 400)

    try:
        participants_count = int(participants_count)
        if participants_count <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "participants_count must be a positive integer >= 1.", None, 400)

    # 1. Fetch trek & check status
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    # Business Rule 1: Trek status must be 'Open' (else 400)
    if trek.status != 'Open':
        return api_response(
            False,
            f"Cannot book trek with status '{trek.status}'. Trek must be 'Open' for bookings.",
            None,
            400
        )

    # Check trek hasn't already completed or ended
    if trek.end_date < date.today():
        return api_response(False, "This trek has already concluded.", None, 400)

    # Business Rule 2: No duplicate active booking for the same user and trek (else 409)
    if Booking.has_active_booking(g.current_user.id, trek.id):
        return api_response(
            False,
            f"You already have an active booking for '{trek.name}'. Duplicate active bookings are not permitted.",
            None,
            409
        )

    # Business Rule 3: available_slots must be >= participants_count, never go negative (else 409 'Fully booked')
    if trek.available_slots < participants_count:
        return api_response(
            False,
            f"Fully booked: Requested {participants_count} slots, but only {trek.available_slots} slots are available.",
            {'available_slots': trek.available_slots},
            409
        )

    # Business Rule 4: Decrement available_slots & create booking
    trek.available_slots = max(0, trek.available_slots - participants_count)

    booking = Booking(
        user_id=g.current_user.id,
        trek_id=trek.id,
        booking_date=datetime.utcnow(),
        status='Booked',
        payment_status='Pending',
        participants_count=participants_count
    )
    db.session.add(booking)
    db.session.flush()

    # Business Rule 5: Create a Notification 'Booking confirmed'
    notification = Notification(
        user_id=g.current_user.id,
        message=f"Booking confirmed for trek '{trek.name}' ({participants_count} participant(s)). Booking ID #{booking.id}."
    )
    db.session.add(notification)

    # Commit all inside the transaction
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(
        True,
        f"Booking confirmed successfully for '{trek.name}'.",
        booking.to_dict(),
        201
    )


@user_bp.route('/bookings/<int:booking_id>/pay', methods=['POST'])
@login_required
@role_required('user')
def simulate_payment(booking_id):
    """
    Optional payment simulation endpoint: sets payment_status to 'Paid'.
    Only accessible by the booking owner.
    """
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return api_response(False, "Booking not found.", None, 404)

    if booking.user_id != g.current_user.id:
        return api_response(False, "Access forbidden: you do not own this booking.", None, 403)

    if booking.status != 'Booked':
        return api_response(
            False,
            f"Cannot pay for a booking with status '{booking.status}'. Status must be 'Booked'.",
            None,
            400
        )

    booking.payment_status = 'Paid'

    # Create payment confirmation notification
    trek_name = booking.trek.name if booking.trek else 'Trek'
    notif = Notification(
        user_id=g.current_user.id,
        message=f"Payment received for booking #{booking.id} ({trek_name}). Payment Status: Paid."
    )
    db.session.add(notif)
    db.session.commit()

    return api_response(
        True,
        f"Payment of Rs. {booking.total_amount if hasattr(booking, 'total_amount') else ''} simulated successfully. Booking marked as Paid.",
        booking.to_dict(),
        200
    )


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('user')
def cancel_booking(booking_id):
    """
    Cancel an active booking:
      - Only the owner (else 403)
      - Only if status is 'Booked' and the trek is not started/completed (else 400)
      - Restore slots
      - Create a Notification
    """
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return api_response(False, "Booking not found.", None, 404)

    # Ownership check
    if booking.user_id != g.current_user.id:
        return api_response(False, "Access forbidden: you do not own this booking.", None, 403)

    # Status check
    if booking.status != 'Booked':
        return api_response(
            False,
            f"Cannot cancel booking with status '{booking.status}'. Only active 'Booked' bookings can be cancelled.",
            None,
            400
        )

    # Trek started or completed check
    trek = booking.trek
    if trek:
        if trek.is_started or trek.status == 'Completed':
            return api_response(
                False,
                "Cannot cancel booking for a trek that has already started or completed.",
                None,
                400
            )
        if trek.start_date < date.today():
            return api_response(
                False,
                "Cannot cancel booking for a trek whose start date has already passed.",
                None,
                400
            )

        # Restore slots
        trek.available_slots = min(trek.total_slots, trek.available_slots + booking.participants_count)

    booking.status = 'Cancelled'
    booking.cancelled_at = datetime.utcnow()

    # Create notification
    notif = Notification(
        user_id=g.current_user.id,
        message=f"Your booking #{booking.id} for '{trek.name if trek else 'Trek'}' has been cancelled. Slots have been released."
    )
    db.session.add(notif)

    db.session.commit()

    # Invalidate cache hook
    if trek:
        invalidate_trek_cache(trek.id)

    return api_response(
        True,
        "Booking cancelled successfully. Slots restored.",
        booking.to_dict(),
        200
    )


# -------------------------------------------------------------
# 3. User Bookings & Historical Queries
# -------------------------------------------------------------
@user_bp.route('/bookings', methods=['GET'])
@login_required
@role_required('user')
def list_user_bookings():
    """
    Get current user's booking status list.
    """
    bookings = Booking.query.filter_by(
        user_id=g.current_user.id
    ).order_by(Booking.booking_date.desc()).all()

    return api_response(
        True,
        "User bookings retrieved.",
        [b.to_dict() for b in bookings],
        200
    )


@user_bp.route('/history', methods=['GET'])
@login_required
@role_required('user')
def booking_history():
    """
    Get all past / completed / cancelled bookings with trek details.
    """
    history_bookings = Booking.query.filter(
        Booking.user_id == g.current_user.id,
        Booking.status.in_(['Completed', 'Cancelled'])
    ).order_by(Booking.booking_date.desc()).all()

    return api_response(
        True,
        "Booking history retrieved.",
        [b.to_dict() for b in history_bookings],
        200
    )


# -------------------------------------------------------------
# 4. User Dashboard Overview
# -------------------------------------------------------------
@user_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('user')
def user_dashboard():
    """
    User dashboard: available treks count, booked treks, and status breakdown.
    """
    # Count available treks (Approved or Open, not deleted)
    available_treks_count = Trek.query.filter(
        Trek.is_deleted == False,
        Trek.status.in_(['Approved', 'Open'])
    ).count()

    # User's bookings
    user_bookings = Booking.query.filter_by(user_id=g.current_user.id).all()
    active_booked_treks = [b.to_dict() for b in user_bookings if b.status == 'Booked']

    # Breakdown of statuses
    status_counts = {
        'Booked': sum(1 for b in user_bookings if b.status == 'Booked'),
        'Completed': sum(1 for b in user_bookings if b.status == 'Completed'),
        'Cancelled': sum(1 for b in user_bookings if b.status == 'Cancelled')
    }

    return api_response(
        True,
        "User dashboard retrieved.",
        {
            'available_treks_count': available_treks_count,
            'booked_treks': active_booked_treks,
            'status_counts': status_counts,
            'total_bookings': len(user_bookings)
        },
        200
    )


# -------------------------------------------------------------
# 5. Notifications Management
# -------------------------------------------------------------
@user_bp.route('/notifications', methods=['GET'])
@login_required
@role_required('user')
def get_notifications():
    """
    Get notifications for current user with unread count.
    """
    notifications = Notification.query.filter_by(
        user_id=g.current_user.id
    ).order_by(Notification.created_at.desc()).all()

    unread_count = sum(1 for n in notifications if not n.is_read)

    return api_response(
        True,
        "Notifications retrieved.",
        {
            'unread_count': unread_count,
            'notifications': [n.to_dict() for n in notifications]
        },
        200
    )


@user_bp.route('/notifications/read', methods=['POST'])
@login_required
@role_required('user')
def mark_notifications_read():
    """
    Mark notifications as read.
    Accepts optional {"notification_id": int}. If omitted, marks all read.
    """
    data = request.get_json(silent=True) or {}
    notification_id = data.get('notification_id')

    if notification_id:
        notif = db.session.get(Notification, notification_id)
        if not notif or notif.user_id != g.current_user.id:
            return api_response(False, "Notification not found.", None, 404)
        notif.is_read = True
    else:
        # Mark all unread notifications read
        Notification.query.filter_by(user_id=g.current_user.id, is_read=False).update({'is_read': True})

    db.session.commit()
    return api_response(True, "Notification(s) marked as read.", None, 200)


# -------------------------------------------------------------
# 6. CSV Export Trigger (Stub for Part 7) & File Download
# -------------------------------------------------------------
@user_bp.route('/export', methods=['POST'])
@login_required
@role_required('user')
def trigger_export():
    """
    Triggers the CSV export job (stub that returns 202 for now, wired in Part 7).
    """
    timestamp = int(datetime.utcnow().timestamp())
    job_id = f"export_{g.current_user.id}_{timestamp}"
    filename = f"bookings_user_{g.current_user.id}_{timestamp}.csv"

    # In Part 7, this will enqueue a Celery task: export_user_bookings_task.delay(user_id)
    return api_response(
        True,
        "CSV export request accepted and scheduled for processing.",
        {
            'status': 'processing',
            'job_id': job_id,
            'expected_filename': filename
        },
        202
    )


@user_bp.route('/exports/<path:filename>', methods=['GET'])
@login_required
@role_required('user')
def download_export(filename):
    """
    Downloads the generated CSV file for the owner only.
    Validates that the filename belongs to the current user.
    """
    # Security check: filename must belong to the logged-in user
    expected_prefix = f"bookings_user_{g.current_user.id}_"
    if not filename.startswith(expected_prefix) and not f"_{g.current_user.id}_" in filename:
        return api_response(False, "Access forbidden: you do not own this export file.", None, 403)

    exports_dir = current_app.config.get('EXPORTS_DIR', os.path.join(os.path.dirname(__file__), '..', 'exports'))

    if not os.path.exists(os.path.join(exports_dir, filename)):
        return api_response(False, "Export file not found or still processing.", None, 404)

    return send_from_directory(
        exports_dir,
        filename,
        as_attachment=True,
        mimetype='text/csv'
    )
