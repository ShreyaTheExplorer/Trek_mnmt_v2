import os
import sys
from datetime import date, datetime

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, Trek, Booking, Notification

def run_tests():
    print("=" * 65)
    print("RUNNING TMA PART 5: TREKKER / USER API SPECIFICATION TESTS")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Clean up any leftover test data
        for email in ['trekker_alice@tma.com', 'trekker_bob@tma.com']:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
        for t_name in ['Open Valley Trek', 'Closed Mountain Trek', 'Approved Peak Trek']:
            t = Trek.query.filter_by(name=t_name).first()
            if t:
                db.session.delete(t)
        db.session.commit()

        # 1. Register & Login Alice (User)
        reg_alice = client.post('/api/auth/register', json={
            'name': 'Alice Sharma',
            'email': 'trekker_alice@tma.com',
            'password': 'password123',
            'phone': '9876543210'
        })
        assert reg_alice.status_code == 201
        token_alice = reg_alice.get_json()['data']['token']
        headers_alice = {'Authorization': f'Bearer {token_alice}'}

        # 2. Register & Login Bob (User)
        reg_bob = client.post('/api/auth/register', json={
            'name': 'Bob Patel',
            'email': 'trekker_bob@tma.com',
            'password': 'password123',
            'phone': '9876543211'
        })
        assert reg_bob.status_code == 201
        token_bob = reg_bob.get_json()['data']['token']
        headers_bob = {'Authorization': f'Bearer {token_bob}'}

        # 3. Create Treks in DB
        # Trek 1: Open for booking with 5 slots
        trek_open = Trek(
            name="Open Valley Trek",
            location="Manali",
            difficulty="Moderate",
            duration_days=4,
            total_slots=5,
            available_slots=5,
            status="Open",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 5),
            description="Lush green meadow trek open for reservations.",
            price=7500.0
        )
        db.session.add(trek_open)

        # Trek 2: Closed trek (not open for booking)
        trek_closed = Trek(
            name="Closed Mountain Trek",
            location="Leh",
            difficulty="Hard",
            duration_days=7,
            total_slots=10,
            available_slots=10,
            status="Closed",
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 17),
            description="High pass trek currently closed.",
            price=14000.0
        )
        db.session.add(trek_closed)

        # Trek 3: Approved trek (Approved but not yet Open for booking)
        trek_approved = Trek(
            name="Approved Peak Trek",
            location="Garhwal",
            difficulty="Easy",
            duration_days=3,
            total_slots=15,
            available_slots=15,
            status="Approved",
            start_date=date(2026, 12, 15),
            end_date=date(2026, 12, 18),
            description="Gentle hillside exploration.",
            price=5000.0
        )
        db.session.add(trek_approved)
        db.session.commit()

        # -------------------------------------------------------------
        # Test 1: GET /api/user/treks with Query Filters & Pagination
        # -------------------------------------------------------------
        print("\n[Test 1] Testing GET /api/user/treks with Pagination & Filters...")
        res_list = client.get('/api/user/treks?q=Valley&difficulty=Moderate&min_days=3&page=1&per_page=5', headers=headers_alice)
        assert res_list.status_code == 200, f"Expected 200, got {res_list.status_code}"
        list_data = res_list.get_json()['data']
        assert 'treks' in list_data
        assert 'pagination' in list_data
        assert len(list_data['treks']) >= 1
        assert list_data['treks'][0]['name'] == 'Open Valley Trek'
        assert list_data['pagination']['page'] == 1
        print("  PASS: Treks listed with search, difficulty filter, duration filter, and pagination.")

        # GET single trek
        res_single = client.get(f'/api/user/treks/{trek_open.id}', headers=headers_alice)
        assert res_single.status_code == 200
        assert res_single.get_json()['data']['available_slots'] == 5
        print("  PASS: Single trek details retrieved.")

        # -------------------------------------------------------------
        # Test 2: Closed Trek Booking Prevention (Rule 1)
        # -------------------------------------------------------------
        print("\n[Test 2] Testing Closed Trek Booking Prevention (Rule 1)...")
        # Attempt to book trek_closed (status 'Closed')
        res_closed_book = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_closed.id,
            'participants_count': 1
        })
        assert res_closed_book.status_code == 400, f"Expected 400, got {res_closed_book.status_code}"
        assert 'must be \'open\'' in res_closed_book.get_json()['message'].lower()
        print("  PASS: Booking closed trek rejected with 400 Bad Request.")

        # Attempt to book trek_approved (status 'Approved', not yet 'Open')
        res_app_book = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_approved.id,
            'participants_count': 1
        })
        assert res_app_book.status_code == 400
        print("  PASS: Booking Approved (non-Open) trek rejected with 400 Bad Request.")

        # -------------------------------------------------------------
        # Test 3: Overbooking Prevention (Rule 3)
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Overbooking Prevention (Rule 3)...")
        # trek_open has available_slots = 5. Trying to book 6 slots MUST fail with 409
        res_overbook = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_open.id,
            'participants_count': 6
        })
        assert res_overbook.status_code == 409, f"Expected 409, got {res_overbook.status_code}"
        assert 'fully booked' in res_overbook.get_json()['message'].lower()
        print("  PASS: Overbooking rejected with 409 Fully booked.")

        # -------------------------------------------------------------
        # Test 4: Successful Booking & Slot Decrement (Rules 4 & 5)
        # -------------------------------------------------------------
        print("\n[Test 4] Testing Successful Booking & Slot Decrement...")
        res_book = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_open.id,
            'participants_count': 2
        })
        assert res_book.status_code == 201, f"Expected 201, got {res_book.status_code}: {res_book.get_data(as_text=True)}"
        booking_data = res_book.get_json()['data']
        booking_id = booking_data['id']
        assert booking_data['status'] == 'Booked'
        assert booking_data['participants_count'] == 2

        # Verify slots decremented in DB: 5 - 2 = 3
        db.session.refresh(trek_open)
        assert trek_open.available_slots == 3, f"Expected 3 available slots, got {trek_open.available_slots}"
        print(f"  PASS: Booking created. Available slots decremented (5 -> {trek_open.available_slots}).")

        # Verify Notification generated
        notif_res = client.get('/api/user/notifications', headers=headers_alice)
        assert notif_res.status_code == 200
        notifs = notif_res.get_json()['data']['notifications']
        assert len(notifs) >= 1
        assert 'Booking confirmed' in notifs[0]['message']
        print("  PASS: Booking confirmation notification created.")

        # -------------------------------------------------------------
        # Test 5: Duplicate Active Booking Prevention (Rule 2)
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Duplicate Active Booking Prevention (Rule 2)...")
        # Alice already has an active booking on trek_open. Trying to book again MUST fail with 409
        res_dup = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_open.id,
            'participants_count': 1
        })
        assert res_dup.status_code == 409, f"Expected 409, got {res_dup.status_code}"
        assert 'already have an active booking' in res_dup.get_json()['message'].lower()
        print("  PASS: Duplicate booking rejected with 409 Conflict.")

        # -------------------------------------------------------------
        # Test 6: Payment Simulation Endpoint (/api/user/bookings/<id>/pay)
        # -------------------------------------------------------------
        print("\n[Test 6] Testing Payment Simulation Endpoint...")
        # Bob cannot pay for Alice's booking
        res_pay_deny = client.post(f'/api/user/bookings/{booking_id}/pay', headers=headers_bob)
        assert res_pay_deny.status_code == 403

        # Alice pays for her booking
        res_pay = client.post(f'/api/user/bookings/{booking_id}/pay', headers=headers_alice)
        assert res_pay.status_code == 200
        assert res_pay.get_json()['data']['payment_status'] == 'Paid'
        print("  PASS: Payment simulation sets payment_status='Paid'.")

        # -------------------------------------------------------------
        # Test 7: Cancel Booking & Restore Slots
        # -------------------------------------------------------------
        print("\n[Test 7] Testing Cancel Booking & Slot Restoration...")
        # Bob cannot cancel Alice's booking
        res_cancel_deny = client.post(f'/api/user/bookings/{booking_id}/cancel', headers=headers_bob)
        assert res_cancel_deny.status_code == 403

        # Alice cancels her booking
        res_cancel = client.post(f'/api/user/bookings/{booking_id}/cancel', headers=headers_alice)
        assert res_cancel.status_code == 200
        cancelled_data = res_cancel.get_json()['data']
        assert cancelled_data['status'] == 'Cancelled'

        # Verify slots restored: 3 + 2 = 5
        db.session.refresh(trek_open)
        assert trek_open.available_slots == 5, f"Expected 5 restored slots, got {trek_open.available_slots}"
        print(f"  PASS: Booking cancelled. Available slots restored to {trek_open.available_slots}.")

        # Alice can now book again since previous booking is cancelled
        res_rebook = client.post('/api/user/bookings', headers=headers_alice, json={
            'trek_id': trek_open.id,
            'participants_count': 1
        })
        assert res_rebook.status_code == 201
        new_booking_id = res_rebook.get_json()['data']['id']
        print("  PASS: New booking allowed after cancellation.")

        # -------------------------------------------------------------
        # Test 8: User Bookings, History & Dashboard
        # -------------------------------------------------------------
        print("\n[Test 8] Testing GET /bookings, GET /history, and GET /dashboard...")
        # Active bookings list
        b_list = client.get('/api/user/bookings', headers=headers_alice)
        assert b_list.status_code == 200
        assert len(b_list.get_json()['data']) >= 1

        # History list (must include the cancelled booking)
        hist_res = client.get('/api/user/history', headers=headers_alice)
        assert hist_res.status_code == 200
        hist_bookings = hist_res.get_json()['data']
        assert any(b['id'] == booking_id and b['status'] == 'Cancelled' for b in hist_bookings)
        print("  PASS: GET /api/user/history returns historical cancelled/completed bookings.")

        # User Dashboard
        dash_res = client.get('/api/user/dashboard', headers=headers_alice)
        assert dash_res.status_code == 200
        dash_data = dash_res.get_json()['data']
        assert dash_data['available_treks_count'] >= 2 # trek_open and trek_approved
        assert len(dash_data['booked_treks']) >= 1
        assert dash_data['status_counts']['Booked'] >= 1
        assert dash_data['status_counts']['Cancelled'] >= 1
        print("  PASS: GET /api/user/dashboard returns available treks, active bookings, and status counts.")

        # -------------------------------------------------------------
        # Test 9: Notifications & Mark Read
        # -------------------------------------------------------------
        print("\n[Test 9] Testing Notifications & POST /notifications/read...")
        notif_get = client.get('/api/user/notifications', headers=headers_alice)
        assert notif_get.status_code == 200
        notif_list = notif_get.get_json()['data']['notifications']
        assert len(notif_list) >= 1
        first_notif_id = notif_list[0]['id']

        # Mark single read
        read_single = client.post('/api/user/notifications/read', headers=headers_alice, json={
            'notification_id': first_notif_id
        })
        assert read_single.status_code == 200

        # Mark all read
        read_all = client.post('/api/user/notifications/read', headers=headers_alice, json={})
        assert read_all.status_code == 200

        notif_after = client.get('/api/user/notifications', headers=headers_alice)
        assert notif_after.get_json()['data']['unread_count'] == 0
        print("  PASS: Notifications retrieved and marked read.")

        # -------------------------------------------------------------
        # Test 10: CSV Export Trigger (Stub returning 202)
        # -------------------------------------------------------------
        print("\n[Test 10] Testing POST /api/user/export (202 Accepted)...")
        export_res = client.post('/api/user/export', headers=headers_alice)
        assert export_res.status_code == 202, f"Expected 202 Accepted, got {export_res.status_code}"
        exp_data = export_res.get_json()['data']
        assert exp_data['status'] == 'processing'
        assert 'job_id' in exp_data
        print(f"  PASS: CSV export triggered successfully (202 Accepted: {exp_data['job_id']}).")

        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Test 11] Cleaning up test records...")
        Notification.query.filter(Notification.user_id.in_([reg_alice.get_json()['data']['user']['id'], reg_bob.get_json()['data']['user']['id']])).delete()
        Booking.query.filter_by(trek_id=trek_open.id).delete()
        db.session.delete(trek_open)
        db.session.delete(trek_closed)
        db.session.delete(trek_approved)
        db.session.delete(db.session.get(User, reg_alice.get_json()['data']['user']['id']))
        db.session.delete(db.session.get(User, reg_bob.get_json()['data']['user']['id']))
        db.session.commit()
        print("  PASS: Test artifacts cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 5 TREKKER / USER API TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()

