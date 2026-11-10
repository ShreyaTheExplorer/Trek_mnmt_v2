import os
import sys
from datetime import datetime, date, timedelta

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification

def run_tests():
    print("=== STARTING PHASE 9 TEST SUITE (STAFF UI & EXPEDITION OPERATIONS) ===")
    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Clean previous test records
        Booking.query.delete()
        Notification.query.delete()
        Trek.query.delete()
        StaffProfile.query.delete()
        User.query.filter(User.role != 'admin').delete()
        db.session.commit()

        # Create Staff A (Assigned guide)
        staff_a = User(
            name="Tenzing Guide",
            email="tenzing@test.com",
            phone="9876543210",
            role="staff",
            status="active"
        )
        staff_a.set_password("password123")
        db.session.add(staff_a)
        db.session.flush()

        profile_a = StaffProfile(
            user_id=staff_a.id,
            contact_details="Basecamp 1, Channel 4",
            specialization="Alpine Route Navigation"
        )
        db.session.add(profile_a)

        # Create Staff B (Unassigned guide for 403 isolation testing)
        staff_b = User(
            name="Pasang Guide",
            email="pasang@test.com",
            phone="9876543211",
            role="staff",
            status="active"
        )
        staff_b.set_password("password123")
        db.session.add(staff_b)
        db.session.flush()

        profile_b = StaffProfile(
            user_id=staff_b.id,
            contact_details="Basecamp 2",
            specialization="Glacier Rescue"
        )
        db.session.add(profile_b)

        # Create Trekker User
        trekker = User(
            name="Rahul Sharma",
            email="rahul@test.com",
            phone="9876543212",
            emergency_contact="+91 9999888877",
            role="user",
            status="active"
        )
        trekker.set_password("password123")
        db.session.add(trekker)
        db.session.flush()

        # Create Trek assigned to Staff A
        tomorrow = date.today() + timedelta(days=2)
        trek = Trek(
            name="Chadar Frozen River Trek",
            location="Zanskar, Ladakh",
            difficulty="Hard",
            duration_days=8,
            total_slots=12,
            available_slots=10,
            assigned_staff_id=staff_a.id,
            status="Approved",
            start_date=tomorrow,
            end_date=tomorrow + timedelta(days=8),
            description="Trek over the frozen Zanskar river in winter.",
            instructions="Crampons, thermal sleeping bags required.",
            price=24000.0
        )
        db.session.add(trek)
        db.session.flush()

        # Create Booking for Trekker
        booking = Booking(
            user_id=trekker.id,
            trek_id=trek.id,
            status="Booked",
            payment_status="Paid",
            participants_count=2
        )
        db.session.add(booking)
        db.session.commit()

        staff_a_id = staff_a.id
        staff_b_id = staff_b.id
        trek_id = trek.id
        booking_id = booking.id

    # 1. Login Tokens
    res_a = client.post('/api/auth/login', json={'email': 'tenzing@test.com', 'password': 'password123'})
    assert res_a.status_code == 200
    token_a = res_a.get_json()['data']['token']
    headers_a = {'Authorization': f'Bearer {token_a}'}

    res_b = client.post('/api/auth/login', json={'email': 'pasang@test.com', 'password': 'password123'})
    assert res_b.status_code == 200
    token_b = res_b.get_json()['data']['token']
    headers_b = {'Authorization': f'Bearer {token_b}'}

    # -------------------------------------------------------------
    # TEST 1: Staff Frontend Components Static Delivery
    # -------------------------------------------------------------
    print("\n--- TEST 1: Verifying Staff Frontend Components Delivery ---")
    resp_dash = client.get('/static/js/components/StaffDashboard.js')
    assert resp_dash.status_code == 200
    code_dash = resp_dash.data.decode('utf-8')
    assert 'StaffDashboard' in code_dash
    assert 'goToTrekDetail' in code_dash
    assert 'registered_users_count' in code_dash
    print("✔ StaffDashboard.js delivered with cards, badges, and detail navigation.")

    resp_detail = client.get('/static/js/components/StaffTrekDetail.js')
    assert resp_detail.status_code == 200
    code_detail = resp_detail.data.decode('utf-8')
    assert 'StaffTrekDetail' in code_detail
    assert 'saveSlots' in code_detail
    assert 'integer (>= 0)' in code_detail
    assert 'toggleStatus' in code_detail
    assert 'executeStartTrek' in code_detail
    assert 'executeCompleteTrek' in code_detail
    assert '403' in code_detail
    assert '409' in code_detail
    print("✔ StaffTrekDetail.js delivered with slot validation, confirm dialogs, and friendly error handlers.")

    # Verify index.html and router.js include Staff components
    idx = client.get('/').data.decode('utf-8')
    assert '/static/js/components/StaffDashboard.js' in idx
    assert '/static/js/components/StaffTrekDetail.js' in idx
    rtr = client.get('/static/js/router.js').data.decode('utf-8')
    assert '/staff/treks/:id' in rtr
    print("✔ Single entry point index.html and router.js correctly registered Staff routes.")

    # -------------------------------------------------------------
    # TEST 2: Staff Dashboard Backend Integration
    # -------------------------------------------------------------
    print("\n--- TEST 2: Verifying Staff Dashboard API Responses ---")
    res_dash = client.get('/api/staff/dashboard', headers=headers_a)
    assert res_dash.status_code == 200
    data_dash = res_dash.get_json()['data']
    assert data_dash['summary']['total_assigned_treks'] == 1
    assert data_dash['summary']['total_participants'] == 2  # 2 participants
    assert len(data_dash['treks']) == 1
    print("✔ StaffDashboard API returned assigned trek and registered participants count.")

    # -------------------------------------------------------------
    # TEST 3: StaffTrekDetail Workflow (Slots, Toggle, Manifest, Start, Complete)
    # -------------------------------------------------------------
    print("\n--- TEST 3: StaffTrekDetail Expedition Operations Workflow ---")

    # 3a. Participant manifest retrieval
    res_part = client.get(f'/api/staff/treks/{trek_id}/participants', headers=headers_a)
    assert res_part.status_code == 200
    parts = res_part.get_json()['data']['participants']
    assert len(parts) == 1
    assert parts[0]['name'] == 'Rahul Sharma'
    assert parts[0]['phone'] == '9876543212'
    assert parts[0]['emergency_contact'] == '+91 9999888877'
    assert parts[0]['booking_status'] == 'Booked'
    print("✔ Participant manifest correctly loaded participant info, phone, and emergency contact.")

    # 3b. Slot capacity modification (integer >= 0 and validation below booked slots)
    # Attempting to set total slots below booked count (2) should return 400
    res_slot_err = client.put(f'/api/staff/treks/{trek_id}/slots', json={'total_slots': 1, 'available_slots': 0}, headers=headers_a)
    assert res_slot_err.status_code == 400
    print("✔ Slot update correctly rejected setting total capacity below booked participants (400 Bad Request).")

    # Valid slot update: total=15, available=13
    res_slot_ok = client.put(f'/api/staff/treks/{trek_id}/slots', json={'total_slots': 15, 'available_slots': 13}, headers=headers_a)
    assert res_slot_ok.status_code == 200
    assert res_slot_ok.get_json()['data']['total_slots'] == 15
    assert res_slot_ok.get_json()['data']['available_slots'] == 13
    print("✔ Slot update successfully updated capacity to 15 total / 13 available.")

    # 3c. Toggle Open / Closed status
    # Trek is 'Approved', opening it is valid
    res_open = client.put(f'/api/staff/treks/{trek_id}/status', json={'status': 'Open'}, headers=headers_a)
    assert res_open.status_code == 200
    assert res_open.get_json()['data']['status'] == 'Open'
    print("✔ Trek status toggled from Approved to Open.")

    # Toggle to Closed
    res_close = client.put(f'/api/staff/treks/{trek_id}/status', json={'status': 'Closed'}, headers=headers_a)
    assert res_close.status_code == 200
    assert res_close.get_json()['data']['status'] == 'Closed'
    print("✔ Trek status toggled from Open to Closed.")

    # 3d. Start Trek
    res_start = client.post(f'/api/staff/treks/{trek_id}/start', headers=headers_a)
    assert res_start.status_code == 200
    assert res_start.get_json()['data']['is_started'] is True
    print("✔ Expedition marked as Started (is_started = True).")

    # 3e. Complete Trek
    res_comp = client.post(f'/api/staff/treks/{trek_id}/complete', headers=headers_a)
    assert res_comp.status_code == 200
    assert res_comp.get_json()['data']['status'] == 'Completed'

    with app.app_context():
        # Verify active booking transitioned to Completed
        b = db.session.get(Booking, booking_id)
        assert b.status == 'Completed'
    print("✔ Expedition marked Completed and participant bookings transitioned to Completed.")

    # -------------------------------------------------------------
    # TEST 4: Friendly Error Handling & Strict Staff Isolation (403 Forbidden)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Verifying 403 Forbidden on Unassigned Staff Access ---")
    res_iso = client.get(f'/api/staff/treks/{trek_id}/participants', headers=headers_b)
    assert res_iso.status_code == 403, f"Expected 403 Forbidden, got {res_iso.status_code}"
    err_json = res_iso.get_json()
    assert err_json['success'] is False
    assert "not assigned" in err_json['message'].lower() or "forbidden" in err_json['message'].lower()
    print("✔ Staff B rejected with 403 Forbidden when attempting to access Staff A's trek.")

    print("\n=== ALL PHASE 9 STAFF UI TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
