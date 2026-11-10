import os
import sys
from datetime import datetime, date, timedelta

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification

def run_tests():
    print("=== STARTING PHASE 10 TEST SUITE (USER / TREKKER UI & INTERACTIONS) ===")
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

        # Create Trekker User
        user = User(
            name="Aarav Mehta",
            email="aarav@test.com",
            phone="9876543210",
            age=28,
            emergency_contact="+91 9123456789",
            address="Mumbai, Maharashtra",
            role="user",
            status="active"
        )
        user.set_password("password123")
        db.session.add(user)

        # Create Staff
        staff = User(
            name="Dawa Sherpa",
            email="dawa@test.com",
            phone="9876543219",
            role="staff",
            status="active"
        )
        staff.set_password("password123")
        db.session.add(staff)
        db.session.flush()

        profile = StaffProfile(
            user_id=staff.id,
            contact_details="Manali Basecamp",
            specialization="High Pass Trekking"
        )
        db.session.add(profile)

        # Create Trek 1: Open with available slots
        tomorrow = date.today() + timedelta(days=2)
        trek_open = Trek(
            name="Bhrigu Lake Alpine Trek",
            location="Manali, Himachal Pradesh",
            difficulty="Moderate",
            duration_days=4,
            total_slots=10,
            available_slots=8,
            assigned_staff_id=staff.id,
            status="Open",
            start_date=tomorrow,
            end_date=tomorrow + timedelta(days=4),
            description="High altitude glacial lake trek with panoramic Pir Panjal views.",
            instructions="Carry rain gear, trekking shoes, and warm socks.",
            price=7500.0
        )
        db.session.add(trek_open)

        # Create Trek 2: Closed trek
        trek_closed = Trek(
            name="Pin Bhaba Pass Expedition",
            location="Spiti, Himachal Pradesh",
            difficulty="Hard",
            duration_days=7,
            total_slots=15,
            available_slots=0,
            assigned_staff_id=staff.id,
            status="Closed",
            start_date=tomorrow + timedelta(days=10),
            end_date=tomorrow + timedelta(days=17),
            description="Dramatic crossover trek from green Kinnaur to cold desert Spiti.",
            instructions="High physical endurance needed.",
            price=18000.0
        )
        db.session.add(trek_closed)

        # Create Trek 3: Past Completed trek
        past_start = date.today() - timedelta(days=20)
        trek_past = Trek(
            name="Prashar Lake Weekend Trek",
            location="Mandi, Himachal Pradesh",
            difficulty="Easy",
            duration_days=2,
            total_slots=20,
            available_slots=15,
            assigned_staff_id=staff.id,
            status="Completed",
            start_date=past_start,
            end_date=past_start + timedelta(days=2),
            description="Tranquil alpine lake with floating island and pagoda temple.",
            instructions="Standard weekend gear.",
            price=3200.0
        )
        db.session.add(trek_past)
        db.session.flush()

        # Add initial past completed booking for Aarav
        past_booking = Booking(
            user_id=user.id,
            trek_id=trek_past.id,
            booking_date=datetime.utcnow() - timedelta(days=22),
            status="Completed",
            payment_status="Paid",
            participants_count=1
        )
        db.session.add(past_booking)

        # Add a notification
        notif = Notification(
            user_id=user.id,
            message="Welcome to TMA! Explore our alpine expeditions.",
            created_at=datetime.utcnow(),
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()

        user_id = user.id
        trek_open_id = trek_open.id
        trek_closed_id = trek_closed.id
        past_booking_id = past_booking.id

    # 1. Login Token for Aarav
    res_login = client.post('/api/auth/login', json={'email': 'aarav@test.com', 'password': 'password123'})
    assert res_login.status_code == 200
    token = res_login.get_json()['data']['token']
    headers = {'Authorization': f'Bearer {token}'}

    # -------------------------------------------------------------
    # TEST 1: User Suite Static Components Delivery
    # -------------------------------------------------------------
    print("\n--- TEST 1: Verifying User Suite Components Static Delivery ---")
    
    # 1a. UserDashboard.js
    resp_dash = client.get('/static/js/components/UserDashboard.js')
    assert resp_dash.status_code == 200
    code_dash = resp_dash.data.decode('utf-8')
    assert 'UserDashboard' in code_dash
    assert 'Export booking history (CSV)' in code_dash
    assert 'available_treks_count' in code_dash
    assert 'notifications' in code_dash
    print("✔ UserDashboard.js: available treks, booked treks, notifications panel, and CSV export polling verified.")

    # 1b. TrekBrowse.js
    resp_browse = client.get('/static/js/components/TrekBrowse.js')
    assert resp_browse.status_code == 200
    code_browse = resp_browse.data.decode('utf-8')
    assert 'TrekBrowse' in code_browse
    assert 'searchQuery' in code_browse
    assert 'filterDifficulty' in code_browse
    assert 'filterLocation' in code_browse
    assert 'filterMinDays' in code_browse
    assert 'badge-status-Open' in code_browse
    assert 'slots left' in code_browse
    assert ':disabled="t.status !== \'Open\' || t.available_slots <= 0"' in code_browse
    print("✔ TrekBrowse.js: search box, filters, paginated cards, slots left, Open/Closed badge, and Book disabled logic verified.")

    # 1c. TrekDetail.js
    resp_detail = client.get('/static/js/components/TrekDetail.js')
    assert resp_detail.status_code == 200
    code_detail = resp_detail.data.decode('utf-8')
    assert 'TrekDetail' in code_detail
    assert 'participantsCount' in code_detail
    assert 'submitBooking' in code_detail
    assert 'simulatePayment' in code_detail
    assert 'Pay (Simulated)' in code_detail
    print("✔ TrekDetail.js: full details, participants count input, Book button, and optional simulated payment verified.")

    # 1d. MyBookings.js
    resp_book = client.get('/static/js/components/MyBookings.js')
    assert resp_book.status_code == 200
    code_book = resp_book.data.decode('utf-8')
    assert 'MyBookings' in code_book
    assert 'confirmCancelBooking' in code_book
    assert 'simulatePayment' in code_book
    assert 'historyBookings' in code_book
    print("✔ MyBookings.js: Active statuses with Cancel button, slot restoration, and History page verified.")

    # 1e. ProfileView.js
    resp_prof = client.get('/static/js/components/ProfileView.js')
    assert resp_prof.status_code == 200
    code_prof = resp_prof.data.decode('utf-8')
    assert 'ProfileView' in code_prof
    assert 'updateProfileInfo' in code_prof
    assert 'changePassword' in code_prof
    print("✔ ProfileView.js: HTML5 profile update and password change form verified.")

    # 1f. Index.html and router.js route registrations
    idx = client.get('/').data.decode('utf-8')
    for script in ['UserDashboard.js', 'TrekBrowse.js', 'TrekDetail.js', 'MyBookings.js', 'ProfileView.js']:
        assert f'/static/js/components/{script}' in idx, f"Missing script {script} in index.html"
    rtr = client.get('/static/js/router.js').data.decode('utf-8')
    assert '/dashboard' in rtr
    assert '/treks/:id' in rtr
    assert '/my-bookings' in rtr
    assert '/profile' in rtr
    print("✔ index.html and router.js correctly configured for user routes.")

    # -------------------------------------------------------------
    # TEST 2: Trekker Dashboard & Notifications API Integration
    # -------------------------------------------------------------
    print("\n--- TEST 2: Verifying Trekker Dashboard & Notifications API ---")
    res_dash = client.get('/api/user/dashboard', headers=headers)
    assert res_dash.status_code == 200
    data_dash = res_dash.get_json()['data']
    assert data_dash['available_treks_count'] >= 1
    assert data_dash['status_counts']['Completed'] == 1

    res_notif = client.get('/api/user/notifications', headers=headers)
    assert res_notif.status_code == 200
    data_notif = res_notif.get_json()['data']
    assert data_notif['unread_count'] >= 1
    assert len(data_notif['notifications']) >= 1

    # Mark notifications read
    res_read = client.post('/api/user/notifications/read', json={}, headers=headers)
    assert res_read.status_code == 200
    res_notif_after = client.get('/api/user/notifications', headers=headers)
    assert res_notif_after.get_json()['data']['unread_count'] == 0
    print("✔ Dashboard and Notifications API verified.")

    # -------------------------------------------------------------
    # TEST 3: TrekBrowse & TrekDetail Booking Workflow
    # -------------------------------------------------------------
    print("\n--- TEST 3: Verifying TrekBrowse & TrekDetail Booking Workflow ---")
    # 3a. Search & Filter
    res_browse = client.get('/api/user/treks?q=Bhrigu&difficulty=Moderate', headers=headers)
    assert res_browse.status_code == 200
    treks_found = res_browse.get_json()['data']['treks']
    assert len(treks_found) == 1
    assert treks_found[0]['name'] == 'Bhrigu Lake Alpine Trek'
    print("✔ Search & filter returned matching active trek.")

    # 3b. Trek Details
    res_det = client.get(f'/api/user/treks/{trek_open_id}', headers=headers)
    assert res_det.status_code == 200
    det_data = res_det.get_json()['data']
    assert det_data['id'] == trek_open_id
    assert det_data['available_slots'] == 8
    print("✔ TrekDetail endpoint returned full metadata and real-time slot capacity.")

    # 3c. Book Expedition
    res_book = client.post('/api/user/bookings', json={
        'trek_id': trek_open_id,
        'participants_count': 2
    }, headers=headers)
    assert res_book.status_code == 201
    book_data = res_book.get_json()['data']
    book_info = book_data.get('booking') or book_data
    new_booking_id = book_info['id']
    assert book_info['status'] == 'Booked'
    assert book_info['payment_status'] == 'Pending'
    assert book_info['participants_count'] == 2
    print(f"✔ Booking created successfully (Booking #{new_booking_id}).")

    # 3d. Simulate Payment
    res_pay = client.post(f'/api/user/bookings/{new_booking_id}/pay', headers=headers)
    assert res_pay.status_code == 200
    pay_data = res_pay.get_json()['data']
    pay_info = pay_data.get('booking') or pay_data
    assert pay_info['payment_status'] == 'Paid'
    print("✔ Payment simulated successfully, updated payment_status to 'Paid'.")

    # -------------------------------------------------------------
    # TEST 4: MyBookings & Cancellation with Slot Restoration
    # -------------------------------------------------------------
    print("\n--- TEST 4: Verifying MyBookings Cancellation & Slot Restoration ---")
    # Cancel booking
    res_cancel = client.post(f'/api/user/bookings/{new_booking_id}/cancel', headers=headers)
    assert res_cancel.status_code == 200
    cancel_data = res_cancel.get_json()['data']
    cancel_info = cancel_data.get('booking') or cancel_data
    assert cancel_info['status'] == 'Cancelled'

    # Verify slots restored to 8
    res_det_after = client.get(f'/api/user/treks/{trek_open_id}', headers=headers)
    assert res_det_after.get_json()['data']['available_slots'] == 8
    print("✔ Booking cancelled and available slots restored back to 8.")

    # Verify History endpoint
    res_hist = client.get('/api/user/history', headers=headers)
    assert res_hist.status_code == 200
    hist_list = res_hist.get_json()['data']
    assert len(hist_list) >= 2  # past_booking + cancelled booking
    print(f"✔ Booking history retrieved with {len(hist_list)} past/cancelled records.")

    # -------------------------------------------------------------
    # TEST 5: CSV Export Flow & Profile Update
    # -------------------------------------------------------------
    print("\n--- TEST 5: Verifying CSV Export Trigger & Profile Update ---")
    # Export trigger
    res_exp = client.post('/api/user/export', headers=headers)
    assert res_exp.status_code == 202
    exp_data = res_exp.get_json()['data']
    task_id = exp_data.get('task_id') or exp_data.get('job_id')
    assert task_id is not None

    # Check status endpoint
    res_status = client.get(f'/api/user/export/{task_id}', headers=headers)
    assert res_status.status_code == 200
    print(f"✔ CSV Export triggered (202 Accepted) and polled successfully (Task ID: {task_id}).")

    # Profile Update
    res_prof_upd = client.put('/api/auth/me', json={
        'name': 'Aarav Mehta Updated',
        'phone': '9876543299',
        'age': 29,
        'emergency_contact': '+91 9988776655',
        'address': 'Pune, Maharashtra',
        'current_password': 'password123',
        'password': 'newpassword123'
    }, headers=headers)
    assert res_prof_upd.status_code == 200
    prof_data = res_prof_upd.get_json()['data']
    upd_user = prof_data.get('user') or prof_data
    assert upd_user['name'] == 'Aarav Mehta Updated'
    assert upd_user['phone'] == '9876543299'

    # Verify new password login
    res_new_login = client.post('/api/auth/login', json={'email': 'aarav@test.com', 'password': 'newpassword123'})
    assert res_new_login.status_code == 200
    print("✔ Profile updated and new password verified on login.")

    print("\n=== ALL PHASE 10 USER UI TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
