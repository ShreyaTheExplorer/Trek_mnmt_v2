from flask import Blueprint, request, g
from extensions import db
from models import User, StaffProfile, Trek, Booking
from auth import api_response, login_required, role_required

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')

# -------------------------------------------------------------
# Staff Assigned Treks
# -------------------------------------------------------------
@staff_bp.route('/treks', methods=['GET'])
@login_required
@role_required('staff', 'admin')
def get_assigned_treks():
    """
    List treks assigned to the current staff member.
    Admins can view all assigned treks or filter by staff.
    """
    if g.current_user.role == 'admin':
        treks = Trek.query.filter_by(is_deleted=False).order_by(Trek.start_date.asc()).all()
    else:
        treks = Trek.query.filter_by(
            assigned_staff_id=g.current_user.id,
            is_deleted=False
        ).order_by(Trek.start_date.asc()).all()

    return api_response(
        True,
        "Assigned treks retrieved.",
        [t.to_dict() for t in treks],
        200
    )


@staff_bp.route('/treks/<int:trek_id>', methods=['GET'])
@login_required
@role_required('staff', 'admin')
def get_assigned_trek_detail(trek_id):
    """
    Get detailed information for an assigned trek.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    # Permission check: staff can only view their own assigned trek
    if g.current_user.role == 'staff' and trek.assigned_staff_id != g.current_user.id:
        return api_response(False, "Access forbidden: you are not assigned to this trek.", None, 403)

    data = trek.to_dict()
    # Include booked participants count
    active_bookings = trek.bookings.filter_by(status='Booked').all()
    data['total_booked_participants'] = sum(b.participants_count for b in active_bookings)
    return api_response(True, "Trek details retrieved.", data, 200)


@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@login_required
@role_required('staff', 'admin')
def get_trek_participants(trek_id):
    """
    Get the participant roster / manifest for an assigned trek.
    Includes trekker contact and emergency details for safety.
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    if g.current_user.role == 'staff' and trek.assigned_staff_id != g.current_user.id:
        return api_response(False, "Access forbidden: you are not assigned to this trek.", None, 403)

    bookings = trek.bookings.filter_by(status='Booked').order_by(Booking.booking_date.asc()).all()
    participants = []
    for b in bookings:
        participants.append({
            'booking_id': b.id,
            'user_id': b.user_id,
            'name': b.user.name if b.user else 'Unknown',
            'email': b.user.email if b.user else 'Unknown',
            'phone': b.user.phone if b.user else None,
            'age': b.user.age if b.user else None,
            'emergency_contact': b.user.emergency_contact if b.user else None,
            'address': b.user.address if b.user else None,
            'participants_count': b.participants_count,
            'payment_status': b.payment_status,
            'booking_date': b.booking_date.isoformat() if b.booking_date else None
        })

    return api_response(
        True,
        f"Participant manifest retrieved for trek '{trek.name}'.",
        {
            'trek_id': trek.id,
            'trek_name': trek.name,
            'total_participants': sum(p['participants_count'] for p in participants),
            'participants': participants
        },
        200
    )


@staff_bp.route('/treks/<int:trek_id>/status', methods=['PUT'])
@login_required
@role_required('staff', 'admin')
def update_trek_status(trek_id):
    """
    Update trek operational status ('Approved', 'Open', 'Closed', 'Completed').
    """
    trek = db.session.get(Trek, trek_id)
    if not trek or trek.is_deleted:
        return api_response(False, "Trek not found.", None, 404)

    if g.current_user.role == 'staff' and trek.assigned_staff_id != g.current_user.id:
        return api_response(False, "Access forbidden: you are not assigned to this trek.", None, 403)

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ['Approved', 'Open', 'Closed', 'Completed']:
        return api_response(
            False,
            "Invalid status. Allowed values: 'Approved', 'Open', 'Closed', 'Completed'.",
            None,
            400
        )

    trek.status = new_status
    db.session.commit()

    return api_response(
        True,
        f"Trek status updated to '{new_status}'.",
        trek.to_dict(),
        200
    )


# -------------------------------------------------------------
# Staff Profile Management
# -------------------------------------------------------------
@staff_bp.route('/profile', methods=['GET'])
@login_required
@role_required('staff', 'admin')
def get_staff_profile():
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
@role_required('staff', 'admin')
def update_staff_profile():
    """
    Update logged-in staff member's profile details.
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

    # Update basic user fields if sent
    if 'name' in data and len(data['name'].strip()) >= 2:
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
