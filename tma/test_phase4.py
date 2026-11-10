import os
import sys
from datetime import date, datetime

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification

def run_tests():
    print("=" * 65)
    print("RUNNING TMA PART 4: STAFF API SPECIFICATION TEST SUITE")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup: Clean any previous test data
        for email in ['staff_a@tma.com', 'staff_b@tma.com', 'trekker_p4@tma.com']:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
        for t_name in ['Staff A Trek', 'Staff B Trek']:
            t = Trek.query.filter_by(name=t_name).first()
            if t:
                db.session.delete(t)
        db.session.commit()

        # 1. Create Staff A
        staff_a = User(name="Guide Arjun", email="staff_a@tma.com", phone="9988776655", role="staff", status="active")
        staff_a.set_password("pass123")
        db.session.add(staff_a)
        db.session.flush()
        db.session.add(StaffProfile(user_id=staff_a.id, specialization="Glacier Crossing"))

        # 2. Create Staff B
        staff_b = User(name="Guide Bhavna", email="staff_b@tma.com", phone="9988776644", role="staff", status="active")
        staff_b.set_password("pass123")
        db.session.add(staff_b)
        db.session.flush()
        db.session.add(StaffProfile(user_id=staff_b.id, specialization="High Pass Navigation"))

        # 3. Create Trek A (Assigned to Staff A)
        trek_a = Trek(
            name="Staff A Trek",
            location="Kullu",
            difficulty="Moderate",
            duration_days=4,
            total_slots=10,
            available_slots=10,
            assigned_staff_id=staff_a.id,
            status="Approved",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 5),
            description="Trek managed by Guide Arjun.",
            price=8000.0
        )
        db.session.add(trek_a)

        # 4. Create Trek B (Assigned to Staff B)
        trek_b = Trek(
            name="Staff B Trek",
            location="Spiti",
            difficulty="Hard",
            duration_days=6,
            total_slots=12,
            available_slots=12,
            assigned_staff_id=staff_b.id,
            status="Approved",
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 16),
            description="Trek managed by Guide Bhavna.",
            price=12000.0
        )
        db.session.add(trek_b)

        # 5. Create Trekker user & booking on Trek A
        trekker = User(
            name="Rohan Mehra",
            email="trekker_p4@tma.com",
            phone="9876543210",
            emergency_contact="9876543219",
            role="user",
            status="active"
        )
        trekker.set_password("pass123")
        db.session.add(trekker)
        db.session.flush()

        booking_a = Booking(
            user_id=trekker.id,
            trek_id=trek_a.id,
            booking_date=datetime.utcnow(),
            status="Booked",
            payment_status="Paid",
            participants_count=2
        )
        db.session.add(booking_a)
        trek_a.recalculate_available_slots()
        db.session.commit()

        # Login tokens
        login_a = client.post('/api/auth/login', json={'email': 'staff_a@tma.com', 'password': 'pass123'})
        assert login_a.status_code == 200
        token_a = login_a.get_json()['data']['token']
        headers_a = {'Authorization': f'Bearer {token_a}'}

        login_b = client.post('/api/auth/login', json={'email': 'staff_b@tma.com', 'password': 'pass123'})
        assert login_b.status_code == 200
        token_b = login_b.get_json()['data']['token']
        headers_b = {'Authorization': f'Bearer {token_b}'}

        # -------------------------------------------------------------
        # Test 1: Staff Dashboard & Assigned Treks
        # -------------------------------------------------------------
        print("\n[Test 1] Testing Staff Dashboard & Assigned Treks...")
        dash_res = client.get('/api/staff/dashboard', headers=headers_a)
        assert dash_res.status_code == 200
        dash_data = dash_res.get_json()['data']
        assert dash_data['summary']['total_assigned_treks'] == 1
        assert dash_data['summary']['total_booked_users'] == 1
        assert dash_data['summary']['total_participants'] == 2
        trek_entry = dash_data['treks'][0]
        assert trek_entry['name'] == 'Staff A Trek'
        assert trek_entry['registered_users_count'] == 1
        print("  PASS: Staff A dashboard shows assigned trek and registered-user count (1 user, 2 participants).")

        # GET /api/staff/treks returns assigned treks only
        treks_res = client.get('/api/staff/treks', headers=headers_a)
        assert treks_res.status_code == 200
        treks_list = treks_res.get_json()['data']
        assert len(treks_list) == 1
        assert treks_list[0]['id'] == trek_a.id
        print("  PASS: GET /api/staff/treks returns assigned treks only.")

        # -------------------------------------------------------------
        # Test 2: Multi-Staff RBAC Isolation (Staff A cannot touch Trek B)
        # -------------------------------------------------------------
        print("\n[Test 2] Verifying Staff A CANNOT access or modify Staff B's Trek...")
        # 2A: Update slots on Trek B
        res_slots_deny = client.put(f'/api/staff/treks/{trek_b.id}/slots', headers=headers_a, json={'total_slots': 15})
        assert res_slots_deny.status_code == 403, f"Expected 403, got {res_slots_deny.status_code}"
        print("  PASS: Staff A blocked from updating slots on Staff B's trek (403 Forbidden).")

        # 2B: Update status on Trek B
        res_status_deny = client.put(f'/api/staff/treks/{trek_b.id}/status', headers=headers_a, json={'status': 'Open'})
        assert res_status_deny.status_code == 403
        print("  PASS: Staff A blocked from toggling status on Staff B's trek (403 Forbidden).")

        # 2C: View participants on Trek B
        res_part_deny = client.get(f'/api/staff/treks/{trek_b.id}/participants', headers=headers_a)
        assert res_part_deny.status_code == 403
        print("  PASS: Staff A blocked from viewing participants on Staff B's trek (403 Forbidden).")

        # 2D: Start Trek B
        res_start_deny = client.post(f'/api/staff/treks/{trek_b.id}/start', headers=headers_a)
        assert res_start_deny.status_code == 403
        print("  PASS: Staff A blocked from starting Staff B's trek (403 Forbidden).")

        # 2E: Complete Trek B
        res_comp_deny = client.post(f'/api/staff/treks/{trek_b.id}/complete', headers=headers_a)
        assert res_comp_deny.status_code == 403
        print("  PASS: Staff A blocked from completing Staff B's trek (403 Forbidden).")

        # -------------------------------------------------------------
        # Test 3: Update Slots (Rules & Available Slots Consistency)
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Slot Updates on Assigned Trek...")
        # Booked participants on Trek A is 2. Trying to set total_slots to 1 MUST fail.
        res_bad_slots = client.put(f'/api/staff/treks/{trek_a.id}/slots', headers=headers_a, json={'total_slots': 1})
        assert res_bad_slots.status_code == 400
        assert 'below currently booked' in res_bad_slots.get_json()['message'].lower()
        print("  PASS: Setting total_slots below booked count rejected with 400 Bad Request.")

        # Set total_slots to 15 -> available_slots must be consistent (15 - 2 = 13)
        res_good_slots = client.put(f'/api/staff/treks/{trek_a.id}/slots', headers=headers_a, json={'total_slots': 15})
        assert res_good_slots.status_code == 200
        updated_trek_a = res_good_slots.get_json()['data']
        assert updated_trek_a['total_slots'] == 15
        assert updated_trek_a['available_slots'] == 13, f"Expected 13, got {updated_trek_a['available_slots']}"
        print(f"  PASS: Total slots updated to 15; available slots kept consistent ({updated_trek_a['available_slots']}).")

        # -------------------------------------------------------------
        # Test 4: Toggle Status (Open / Closed only)
        # -------------------------------------------------------------
        print("\n[Test 4] Testing Status Toggle (Open/Closed only)...")
        # Invalid status value (e.g. 'Completed' or 'Pending' via this endpoint)
        res_bad_st = client.put(f'/api/staff/treks/{trek_a.id}/status', headers=headers_a, json={'status': 'Completed'})
        assert res_bad_st.status_code == 400
        print("  PASS: Staff blocked from setting arbitrary status (only Open/Closed allowed).")

        # Trek A is currently 'Approved'. Opening is allowed.
        res_open = client.put(f'/api/staff/treks/{trek_a.id}/status', headers=headers_a, json={'status': 'Open'})
        assert res_open.status_code == 200
        assert res_open.get_json()['data']['status'] == 'Open'
        print("  PASS: Trek status toggled to 'Open'.")

        # Toggle to 'Closed'
        res_closed = client.put(f'/api/staff/treks/{trek_a.id}/status', headers=headers_a, json={'status': 'Closed'})
        assert res_closed.status_code == 200
        assert res_closed.get_json()['data']['status'] == 'Closed'
        print("  PASS: Trek status toggled to 'Closed'.")

        # Opening from 'Closed' is allowed
        res_reopen = client.put(f'/api/staff/treks/{trek_a.id}/status', headers=headers_a, json={'status': 'Open'})
        assert res_reopen.status_code == 200
        assert res_reopen.get_json()['data']['status'] == 'Open'
        print("  PASS: Trek status reopened from 'Closed' to 'Open'.")

        # -------------------------------------------------------------
        # Test 5: Participants Manifest
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Participants Manifest...")
        part_res = client.get(f'/api/staff/treks/{trek_a.id}/participants', headers=headers_a)
        assert part_res.status_code == 200
        part_data = part_res.get_json()['data']
        assert part_data['total_bookings'] == 1
        p_entry = part_data['participants'][0]
        assert p_entry['name'] == 'Rohan Mehra'
        assert p_entry['phone'] == '9876543210'
        assert p_entry['emergency_contact'] == '9876543219'
        assert p_entry['booking_status'] == 'Booked'
        assert p_entry['participants_count'] == 2
        print(f"  PASS: Participants roster verified with contact & emergency information.")

        # -------------------------------------------------------------
        # Test 6: Start Trek
        # -------------------------------------------------------------
        print("\n[Test 6] Testing POST /api/staff/treks/<id>/start...")
        start_res = client.post(f'/api/staff/treks/{trek_a.id}/start', headers=headers_a)
        assert start_res.status_code == 200
        assert start_res.get_json()['data']['is_started'] is True
        print("  PASS: Trek marked as started (is_started=True).")

        # -------------------------------------------------------------
        # Test 7: Complete Trek (Trek & all 'Booked' bookings set to Completed)
        # -------------------------------------------------------------
        print("\n[Test 7] Testing POST /api/staff/treks/<id>/complete...")
        comp_res = client.post(f'/api/staff/treks/{trek_a.id}/complete', headers=headers_a)
        assert comp_res.status_code == 200
        assert comp_res.get_json()['data']['status'] == 'Completed'

        # Check booking status
        db.session.refresh(booking_a)
        assert booking_a.status == 'Completed', f"Expected booking status='Completed', got {booking_a.status}"
        print("  PASS: Trek set to 'Completed' and all active bookings transitioned to 'Completed'.")

        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Test 8] Cleaning up test data...")
        Notification.query.filter_by(user_id=trekker.id).delete()
        db.session.delete(booking_a)
        db.session.delete(trek_a)
        db.session.delete(trek_b)
        db.session.delete(trekker)
        db.session.delete(staff_a)
        db.session.delete(staff_b)
        db.session.commit()
        print("  PASS: Test data cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 4 STAFF API SPECIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()

