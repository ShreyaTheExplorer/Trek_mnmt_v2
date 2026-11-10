from datetime import datetime
from flask import Blueprint, request, g
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification
from auth import api_response, login_required, role_required
from cache import invalidate_trek_cache

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')

# -------------------------------------------------------------
# Reusable Helper: Enforce Staff Trek Assignment
# -------------------------------------------------------------
def get_staff_trek_or_403(trek_id: int):
    """
    Enforce on EVERY route that the trek's assigned_staff_id equals
    the current staff user's id; otherwise return 403 Forbidden.
    Returns (trek, None) on success, or (None, error_response) on failure.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return None, api_response(False, "Trek not found.", None, 404)

    if trek.assigned_staff_id != g.current_user.id:
        return None, api_response(
            False,
            "Access forbidden: you are not assigned to this trek.",
            None,
            403
        )

    return trek, None


# -------------------------------------------------------------
# 1. Staff Dashboard
# -------------------------------------------------------------
@staff_bp.route('/dashboard', methods=['GET'])
@login_required
@role_required('staff')
def staff_dashboard():
    """
    Treks assigned to this staff member and registered-user count
    per trek (count of Booked bookings).
    """
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=g.current_user.id,
        is_deleted=False
    ).order_by(Trek.start_date.asc()).all()

    treks_summary = []
    total_booked_users = 0
    total_participants = 0

    for trek in assigned_treks:
        active_bookings = trek.bookings.filter_by(status='Booked').all()
        registered_users_count = len(active_bookings)
        participants_count = sum(b.participants_count for b in active_bookings)

        total_booked_users += registered_users_count
        total_participants += participants_count

        trek_info = trek.to_dict()
        trek_info['registered_users_count'] = registered_users_count
        trek_info['total_participants'] = participants_count
        treks_summary.append(trek_info)

    return api_response(
        True,
        "Staff dashboard retrieved.",
        {
            'staff': {
                'id': g.current_user.id,
                'name': g.current_user.name,
                'email': g.current_user.email
            },
            'summary': {
                'total_assigned_treks': len(assigned_treks),
                'open_treks': sum(1 for t in assigned_treks if t.status == 'Open'),
                'completed_treks': sum(1 for t in assigned_treks if t.status == 'Completed'),
                'total_booked_users': total_booked_users,
                'total_participants': total_participants
            },
            'treks': treks_summary
        },
        200
    )


# -------------------------------------------------------------
# 2. Assigned Treks Listing
# -------------------------------------------------------------
@staff_bp.route('/treks', methods=['GET'])
@login_required
@role_required('staff')
def list_assigned_treks():
    """
    List assigned treks only for the current staff member.
    """
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=g.current_user.id,
        is_deleted=False
    ).order_by(Trek.start_date.asc()).all()

    return api_response(
        True,
        "Assigned treks retrieved.",
        [t.to_dict() for t in assigned_treks],
        200
    )


# -------------------------------------------------------------
# 3. Update Slots for Assigned Trek
# -------------------------------------------------------------
@staff_bp.route('/treks/<int:trek_id>/slots', methods=['PUT'])
@login_required
@role_required('staff')
def update_trek_slots(trek_id):
    """
    Update total/available slots.
    Cannot set total below the number of booked users; keep available consistent.
    """
    trek, err = get_staff_trek_or_403(trek_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    total_slots = data.get('total_slots')

    try:
        total_slots = int(total_slots)
        if total_slots < 0:
            raise ValueError
    except (TypeError, ValueError):
        return api_response(False, "total_slots must be an integer >= 0.", None, 400)

    # Active booked participants count
    active_bookings = trek.bookings.filter_by(status='Booked').all()
    booked_participants = sum(b.participants_count for b in active_bookings)

    if total_slots < booked_participants:
        return api_response(
            False,
            f"Cannot set total slots ({total_slots}) below currently booked participants ({booked_participants}).",
            None,
            400
        )

    trek.total_slots = total_slots
    # Keep available consistent
    trek.available_slots = total_slots - booked_participants
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(
        True,
        f"Slots updated successfully for '{trek.name}'. Available slots: {trek.available_slots}.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# 4. Toggle Status (Open / Closed only)
# -------------------------------------------------------------
@staff_bp.route('/treks/<int:trek_id>/status', methods=['PUT'])
@login_required
@role_required('staff')
def toggle_trek_status(trek_id):
    """
    Toggle Open/Closed only.
    Opening is allowed only if the trek is Approved or Closed.
    """
    trek, err = get_staff_trek_or_403(trek_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').strip()

    if new_status not in ['Open', 'Closed']:
        return api_response(
            False,
            "Staff can only toggle status between 'Open' and 'Closed'.",
            None,
            400
        )

    # Rule: Opening is allowed only if the trek is Approved or Closed
    if new_status == 'Open':
        if trek.status not in ['Approved', 'Closed']:
            return api_response(
                False,
                f"Cannot open trek from status '{trek.status}'. Opening is allowed only if the trek is Approved or Closed.",
                None,
                400
            )

    trek.status = new_status
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(
        True,
        f"Trek status toggled to '{new_status}'.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# 5. Participants Roster
# -------------------------------------------------------------
@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@login_required
@role_required('staff')
def get_trek_participants(trek_id):
    """
    List of registered users (name, phone, emergency contact, booking status).
    """
    trek, err = get_staff_trek_or_403(trek_id)
    if err:
        return err

    bookings = trek.bookings.order_by(Booking.booking_date.asc()).all()
    participants = []
    for b in bookings:
        participants.append({
            'booking_id': b.id,
            'user_id': b.user_id,
            'name': b.user.name if b.user else 'Unknown',
            'phone': b.user.phone if b.user else None,
            'emergency_contact': b.user.emergency_contact if b.user else None,
            'booking_status': b.status,
            'participants_count': b.participants_count,
            'payment_status': b.payment_status,
            'booking_date': b.booking_date.isoformat() if b.booking_date else None
        })

    return api_response(
        True,
        f"Participants roster retrieved for trek '{trek.name}'.",
        {
            'trek_id': trek.id,
            'trek_name': trek.name,
            'total_bookings': len(bookings),
            'participants': participants
        },
        200
    )


# -------------------------------------------------------------
# 6. Start Trek
# -------------------------------------------------------------
@staff_bp.route('/treks/<int:trek_id>/start', methods=['POST'])
@login_required
@role_required('staff')
def start_trek(trek_id):
    """
    Marks the trek as started (sets is_started = True).
    """
    trek, err = get_staff_trek_or_403(trek_id)
    if err:
        return err

    trek.is_started = True
    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    # Send notification to booked participants
    active_bookings = trek.bookings.filter_by(status='Booked').all()
    for b in active_bookings:
        notif = Notification(
            user_id=b.user_id,
            message=f"Trek '{trek.name}' has officially started! Enjoy the journey."
        )
        db.session.add(notif)
    db.session.commit()

    return api_response(
        True,
        f"Trek '{trek.name}' has been marked as started.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# 7. Complete Trek
# -------------------------------------------------------------
@staff_bp.route('/treks/<int:trek_id>/complete', methods=['POST'])
@login_required
@role_required('staff')
def complete_trek(trek_id):
    """
    Sets the trek to Completed and all 'Booked' bookings to 'Completed'.
    """
    trek, err = get_staff_trek_or_403(trek_id)
    if err:
        return err

    # Set trek to Completed
    trek.status = 'Completed'

    # Set all 'Booked' bookings to 'Completed'
    booked_bookings = trek.bookings.filter_by(status='Booked').all()
    for b in booked_bookings:
        b.status = 'Completed'
        # Send completion notification
        notif = Notification(
            user_id=b.user_id,
            message=f"Congratulations! Trek '{trek.name}' is successfully completed."
        )
        db.session.add(notif)

    db.session.commit()

    # Invalidate cache hook
    invalidate_trek_cache(trek.id)

    return api_response(
        True,
        f"Trek '{trek.name}' and all active bookings set to 'Completed'.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# 8. Staff Profile Management
# -------------------------------------------------------------
@staff_bp.route('/profile', methods=['GET'])
@login_required
@role_required('staff')
def get_profile():
    """
    Get profile of the logged-in staff member.
    """
    user = g.current_user
    profile = user.staff_profile
    return api_response(
        True,
        "Staff profile retrieved.",
        {
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        },
        200
    )


@staff_bp.route('/profile', methods=['PUT'])
@login_required
@role_required('staff')
def update_profile():
    """
    Update staff's own contact details and specialization.
    """
    user = g.current_user
    profile = user.staff_profile
    if not profile:
        profile = StaffProfile(user_id=user.id)
        db.session.add(profile)

    data = request.get_json(silent=True) or {}
    if 'contact_details' in data:
        profile.contact_details = data['contact_details']
    if 'specialization' in data:
        profile.specialization = data['specialization']

    if 'name' in data and len((data['name'] or '').strip()) >= 2:
        user.name = data['name'].strip()
    if 'phone' in data:
        user.phone = (data['phone'] or '').strip() or None

    db.session.commit()

    return api_response(
        True,
        "Staff profile updated successfully.",
        {
            'user': user.to_dict(),
            'profile': profile.to_dict()
        },
        200
    )
