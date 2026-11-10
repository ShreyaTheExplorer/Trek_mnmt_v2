from datetime import datetime, date
from flask import Blueprint, request, g
from extensions import db
from models import Trek, Booking, Notification, User
from auth import api_response, login_required

user_bp = Blueprint('user', __name__, url_prefix='/api')

# -------------------------------------------------------------
# Public Trek Exploration Endpoints
# -------------------------------------------------------------
@user_bp.route('/treks', methods=['GET'])
def list_public_treks():
    """
    Public endpoint for exploring treks.
    Only shows non-deleted treks with status 'Open' or 'Approved'.
    Supports filtering by search query, difficulty, max_price, and location.
    """
    search = request.args.get('search', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()
    max_price = request.args.get('max_price')
    sort_by = request.args.get('sort_by', 'date_asc')

    query = Trek.query.filter(
        Trek.is_deleted == False,
        Trek.status.in_(['Open', 'Approved'])
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Trek.name.ilike(search_filter)) |
            (Trek.location.ilike(search_filter)) |
            (Trek.description.ilike(search_filter))
        )

    if difficulty:
        query = query.filter(Trek.difficulty.ilike(difficulty))

    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    if max_price:
        try:
            query = query.filter(Trek.price <= float(max_price))
        except ValueError:
            pass

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Trek.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Trek.price.desc())
    elif sort_by == 'date_desc':
        query = query.order_by(Trek.start_date.desc())
    else: # date_asc default
        query = query.order_by(Trek.start_date.asc())

    treks = query.all()
    return api_response(True, "Available treks retrieved.", [t.to_dict() for t in treks], 200)


@user_bp.route('/treks/<int:trek_id>', methods=['GET'])
def get_public_trek_detail(trek_id):
    """
    Public endpoint: Get details of a single trek.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    return api_response(True, "Trek details retrieved.", trek.to_dict(), 200)


# -------------------------------------------------------------
# Trekker Booking Operations (Protected)
# -------------------------------------------------------------
@user_bp.route('/bookings', methods=['POST'])
@login_required
def create_booking():
    """
    Book a trek for the authenticated user.
    Enforces slot availability, checks for duplicate active bookings,
    recalculates available slots, and creates a confirmation notification.
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
        return api_response(False, "participants_count must be a positive integer.", None, 400)

    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found or has been removed.", None, 404)

    if trek.status not in ['Open', 'Approved']:
        return api_response(False, f"Trek is currently '{trek.status}' and not open for booking.", None, 400)

    if trek.start_date < date.today():
        return api_response(False, "This trek has already started or ended. Booking is closed.", None, 400)

    # Prevent duplicate active bookings for the same user and trek
    if Booking.has_active_booking(g.current_user.id, trek.id):
        return api_response(
            False,
            f"You already have an active booking for '{trek.name}'. Duplicate bookings are not allowed.",
            None,
            400
        )

    # Check available slot capacity
    if participants_count > trek.available_slots:
        return api_response(
            False,
            f"Insufficient slots available. Requested: {participants_count}, Available: {trek.available_slots}.",
            None,
            400
        )

    # Create new booking
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

    # Recalculate and update trek slots
    trek.recalculate_available_slots()

    # Create confirmation notification for the trekker
    notification = Notification(
        user_id=g.current_user.id,
        message=f"Booking confirmed for '{trek.name}' ({participants_count} participant(s)). Booking ID #{booking.id}.",
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()

    return api_response(
        True,
        "Trek booked successfully.",
        booking.to_dict(),
        201
    )


@user_bp.route('/user/bookings', methods=['GET'])
@login_required
def get_user_bookings():
    """
    List all bookings for the currently authenticated trekker.
    """
    bookings = Booking.query.filter_by(user_id=g.current_user.id).order_by(Booking.booking_date.desc()).all()
    return api_response(
        True,
        "Bookings retrieved.",
        [b.to_dict() for b in bookings],
        200
    )


@user_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@login_required
def get_booking_detail(booking_id):
    """
    Get detailed information for a specific booking.
    Restricted to the booking owner, staff, or admin.
    """
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return api_response(False, "Booking not found.", None, 404)

    if g.current_user.role not in ['admin', 'staff'] and booking.user_id != g.current_user.id:
        return api_response(False, "Access forbidden: you do not own this booking.", None, 403)

    return api_response(True, "Booking details retrieved.", booking.to_dict(), 200)


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """
    Cancel an active booking.
    Frees up the booked slots and sends a cancellation notification.
    """
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return api_response(False, "Booking not found.", None, 404)

    # Permission check
    if g.current_user.role not in ['admin'] and booking.user_id != g.current_user.id:
        return api_response(False, "Access forbidden: you cannot cancel this booking.", None, 403)

    if booking.status != 'Booked':
        return api_response(False, f"Cannot cancel booking with status '{booking.status}'.", None, 400)

    trek = booking.trek
    if trek and trek.start_date < date.today():
        return api_response(False, "Cannot cancel booking for a trek that has already commenced.", None, 400)

    # Update status to Cancelled
    booking.status = 'Cancelled'
    booking.cancelled_at = datetime.utcnow()

    # Recalculate available slots for the trek
    if trek:
        trek.recalculate_available_slots()

    # Create cancellation notification
    notification = Notification(
        user_id=booking.user_id,
        message=f"Your booking for '{trek.name if trek else 'Trek'}' (ID #{booking.id}) has been cancelled.",
        created_at=datetime.utcnow(),
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()

    return api_response(
        True,
        "Booking cancelled successfully. Slots have been released.",
        booking.to_dict(),
        200
    )


# -------------------------------------------------------------
# User Notification Endpoints
# -------------------------------------------------------------
@user_bp.route('/user/notifications', methods=['GET'])
@login_required
def get_user_notifications():
    """
    List all notifications for the authenticated user.
    """
    notifications = Notification.query.filter_by(user_id=g.current_user.id).order_by(Notification.created_at.desc()).all()
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


@user_bp.route('/user/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """
    Mark a specific notification as read.
    """
    notif = db.session.get(Notification, notification_id)
    if not notif or notif.user_id != g.current_user.id:
        return api_response(False, "Notification not found.", None, 404)

    notif.is_read = True
    db.session.commit()
    return api_response(True, "Notification marked as read.", notif.to_dict(), 200)


@user_bp.route('/user/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """
    Mark all unread notifications for the current user as read.
    """
    Notification.query.filter_by(user_id=g.current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return api_response(True, "All notifications marked as read.", None, 200)
