import os
import sys
from datetime import date, datetime, timedelta

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification

def run_tests():
    print("=" * 65)
    print("RUNNING TMA PART 3: ADMIN API SPECIFICATION TEST SUITE")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup: Login as seeded Admin
        admin_login = client.post('/api/auth/login', json={
            'email': 'admin@tma.com',
            'password': 'admin123'
        })
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.get_data(as_text=True)}"
        admin_token = admin_login.get_json()['data']['token']
        headers = {'Authorization': f'Bearer {admin_token}'}

        # -------------------------------------------------------------
        # 1. Staff Management (POST, GET, PUT, PATCH status)
        # -------------------------------------------------------------
        print("\n[Test 1] Testing Admin Staff Endpoints...")
        # Create Staff
        staff_res = client.post('/api/admin/staff', headers=headers, json={
            'name': 'Karan Negi',
            'email': 'karan.guide@tma.com',
            'password': 'guidePassword123',
            'phone': '9876543222',
            'contact_details': 'Radio Frequency: 144.5 MHz',
            'specialization': 'High Altitude Wilderness Expert'
        })
        assert staff_res.status_code == 201, f"Expected 201, got {staff_res.status_code}: {staff_res.get_data(as_text=True)}"
        staff_data = staff_res.get_json()['data']
        staff_id = staff_data['id']
        assert staff_data['role'] == 'staff'
        assert staff_data['staff_profile']['specialization'] == 'High Altitude Wilderness Expert'
        print(f"  PASS: Staff '{staff_data['name']}' created with StaffProfile.")

        # List Staff with search
        staff_search = client.get('/api/admin/staff?search=Negi', headers=headers)
        assert staff_search.status_code == 200
        assert len(staff_search.get_json()['data']) >= 1
        print("  PASS: Staff listing with search query successful.")

        # Update Staff
        staff_update = client.put(f'/api/admin/staff/{staff_id}', headers=headers, json={
            'name': 'Karan Singh Negi',
            'specialization': 'Mountaineering & Rescue Specialist'
        })
        assert staff_update.status_code == 200
        assert staff_update.get_json()['data']['name'] == 'Karan Singh Negi'
        print("  PASS: Staff information updated.")

        # PATCH Staff status (to inactive, then back to active)
        status_patch = client.patch(f'/api/admin/staff/{staff_id}/status', headers=headers, json={
            'status': 'inactive'
        })
        assert status_patch.status_code == 200
        assert status_patch.get_json()['data']['status'] == 'inactive'
        print("  PASS: Staff status patched to 'inactive'.")

        # -------------------------------------------------------------
        # 2. Trek Management (POST, GET, PUT, Staff Assignment)
        # -------------------------------------------------------------
        print("\n[Test 2] Testing Admin Trek Creation & Validations...")
        # Invalid dates: end < start
        bad_dates = client.post('/api/admin/treks', headers=headers, json={
            'name': 'Invalid Date Trek',
            'location': 'Himachal',
            'difficulty': 'Moderate',
            'duration_days': 5,
            'total_slots': 20,
            'price': 12000.0,
            'start_date': '2026-10-15',
            'end_date': '2026-10-10', # Invalid
            'description': 'A beautiful autumn trek in Himachal Pradesh.'
        })
        assert bad_dates.status_code == 400
        print("  PASS: Rejection of invalid end_date < start_date (400 Bad Request).")

        # Invalid difficulty enum
        bad_diff = client.post('/api/admin/treks', headers=headers, json={
            'name': 'Invalid Diff Trek',
            'location': 'Himachal',
            'difficulty': 'Extreme', # Not in Easy/Moderate/Hard
            'duration_days': 5,
            'total_slots': 20,
            'price': 12000.0,
            'start_date': '2026-10-10',
            'end_date': '2026-10-15',
            'description': 'A beautiful autumn trek in Himachal Pradesh.'
        })
        assert bad_diff.status_code == 400
        print("  PASS: Rejection of invalid difficulty enum (400 Bad Request).")

        # Create valid trek: sets available_slots = total_slots
        trek_res = client.post('/api/admin/treks', headers=headers, json={
            'name': 'Kedarkantha Summit Expedition',
            'location': 'Uttarakhand',
            'difficulty': 'Moderate',
            'duration_days': 6,
            'total_slots': 18,
            'price': 9500.0,
            'start_date': '2026-12-10',
            'end_date': '2026-12-15',
            'description': 'Magnificent summit climb through pine forests and snow.',
            'instructions': 'Carry warm winter fleece and sturdy trekking boots.',
            'status': 'Pending'
        })
        assert trek_res.status_code == 201
        trek_data = trek_res.get_json()['data']
        trek_id = trek_data['id']
        assert trek_data['total_slots'] == 18
        assert trek_data['available_slots'] == 18, f"Expected available_slots=18, got {trek_data['available_slots']}"
        assert trek_data['status'] == 'Pending'
        print(f"  PASS: Trek created. available_slots initialized to total_slots ({trek_data['available_slots']}).")

        # Admin transitions status: Pending -> Approved -> Open
        status_update = client.put(f'/api/admin/treks/{trek_id}', headers=headers, json={
            'status': 'Open'
        })
        assert status_update.status_code == 200
        assert status_update.get_json()['data']['status'] == 'Open'
        print("  PASS: Admin transitioned trek status from 'Pending' to 'Open'.")

        # -------------------------------------------------------------
        # 3. Staff Assignment Rule (Only ACTIVE staff can be assigned)
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Staff Assignment Rule (Only active staff)...")
        # Try assigning inactive staff Karan (status is currently 'inactive')
        bad_assign = client.post(f'/api/admin/treks/{trek_id}/assign', headers=headers, json={
            'staff_id': staff_id
        })
        assert bad_assign.status_code == 400, f"Expected 400 for assigning inactive staff, got {bad_assign.status_code}"
        assert 'active' in bad_assign.get_json()['message'].lower()
        print("  PASS: Attempt to assign inactive staff rejected with 400 Bad Request.")

        # Reactivate staff
        client.patch(f'/api/admin/staff/{staff_id}/status', headers=headers, json={'status': 'active'})

        # Now assign active staff
        good_assign = client.post(f'/api/admin/treks/{trek_id}/assign', headers=headers, json={
            'staff_id': staff_id
        })
        assert good_assign.status_code == 200
        assert good_assign.get_json()['data']['assigned_staff_id'] == staff_id
        print(f"  PASS: Active staff successfully assigned to trek.")

        # -------------------------------------------------------------
        # 4. User Management (GET, PATCH status, Admin protection)
        # -------------------------------------------------------------
        print("\n[Test 4] Testing User Management & Admin Self-Modification Protection...")
        # Create a test trekker
        reg_res = client.post('/api/auth/register', json={
            'name': 'Ankit Verma',
            'email': 'ankit.test@tma.com',
            'password': 'password123',
            'phone': '9876543111'
        })
        assert reg_res.status_code == 201
        user_id = reg_res.get_json()['data']['user']['id']

        # List users with filter
        users_res = client.get('/api/admin/users?search=Ankit&status=active', headers=headers)
        assert users_res.status_code == 200
        assert len(users_res.get_json()['data']) >= 1
        print("  PASS: User listing with search & status filter successful.")

        # Admin cannot modify themselves
        admin_self_patch = client.patch(f'/api/admin/users/{admin_login.get_json()["data"]["user"]["id"]}/status', headers=headers, json={
            'status': 'inactive'
        })
        assert admin_self_patch.status_code == 400
        assert 'cannot modify their own' in admin_self_patch.get_json()['message'].lower()
        print("  PASS: Admin prevented from modifying their own account status (400 Bad Request).")

        # Deactivate user, blacklist user, then reactivate
        user_patch = client.patch(f'/api/admin/users/{user_id}/status', headers=headers, json={
            'status': 'blacklisted'
        })
        assert user_patch.status_code == 200
        assert user_patch.get_json()['data']['status'] == 'blacklisted'
        print("  PASS: Trekker user status patched to 'blacklisted'.")

        # Reactivate user for booking test
        client.patch(f'/api/admin/users/{user_id}/status', headers=headers, json={'status': 'active'})

        # -------------------------------------------------------------
        # 5. Bookings Overview & Historical Data
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Bookings Overview & Filtering...")
        # Create a booking
        test_booking = Booking(
            user_id=user_id,
            trek_id=trek_id,
            booking_date=datetime.utcnow(),
            status='Booked',
            payment_status='Paid',
            participants_count=3
        )
        db.session.add(test_booking)
        trek = db.session.get(Trek, trek_id)
        trek.recalculate_available_slots()
        db.session.commit()

        # Query all bookings
        all_b_res = client.get('/api/admin/bookings', headers=headers)
        assert all_b_res.status_code == 200
        bookings_list = all_b_res.get_json()['data']
        assert len(bookings_list) >= 1
        b_entry = next(b for b in bookings_list if b['id'] == test_booking.id)
        assert b_entry['user_name'] == 'Ankit Verma'
        assert b_entry['trek_name'] == 'Kedarkantha Summit Expedition'
        assert b_entry['participants_count'] == 3
        print("  PASS: GET /api/admin/bookings returned full user and trek metadata.")

        # -------------------------------------------------------------
        # 6. Trek Soft-Delete Protection with Active Bookings
        # -------------------------------------------------------------
        print("\n[Test 6] Testing Trek Soft-Delete Protection...")
        # Without cancel_bookings=true, delete MUST fail with 400
        del_fail = client.delete(f'/api/admin/treks/{trek_id}', headers=headers)
        assert del_fail.status_code == 400, f"Expected 400, got {del_fail.status_code}"
        assert 'active booking' in del_fail.get_json()['message'].lower()
        print("  PASS: Trek deletion blocked while active bookings exist (400 Bad Request).")

        # With cancel_bookings=true, delete succeeds and cancels bookings
        del_success = client.delete(f'/api/admin/treks/{trek_id}?cancel_bookings=true', headers=headers)
        assert del_success.status_code == 200
        del_trek_data = del_success.get_json()['data']
        assert del_trek_data['is_deleted'] is True
        assert del_trek_data['status'] == 'Closed'
        # Verify booking was cancelled
        db.session.refresh(test_booking)
        assert test_booking.status == 'Cancelled'
        print("  PASS: Trek soft deleted and active bookings automatically cancelled.")

        # -------------------------------------------------------------
        # 7. Unified Search Endpoint (/api/admin/search)
        # -------------------------------------------------------------
        print("\n[Test 7] Testing Unified Search Endpoint (/api/admin/search)...")
        search_res = client.get('/api/admin/search?q=Negi', headers=headers)
        assert search_res.status_code == 200
        search_data = search_res.get_json()['data']
        assert 'staff' in search_data
        assert any(s['name'] == 'Karan Singh Negi' for s in search_data['staff'])
        print("  PASS: Unified search returned matched staff records.")

        # -------------------------------------------------------------
        # 8. Dashboard & Chart-Ready Stats Endpoints
        # -------------------------------------------------------------
        print("\n[Test 8] Testing Dashboard & Chart Analytics Stats...")
        dash_res = client.get('/api/admin/dashboard', headers=headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.get_json()['data']
        assert 'total_treks' in dash_data
        assert 'treks_by_status' in dash_data
        assert 'bookings_by_status' in dash_data
        assert isinstance(dash_data['treks_by_status'], dict)
        assert isinstance(dash_data['bookings_by_status'], dict)
        print("  PASS: GET /api/admin/dashboard returned complete metric breakdowns.")

        stats_res = client.get('/api/admin/stats', headers=headers)
        assert stats_res.status_code == 200
        stats_data = stats_res.get_json()['data']
        assert 'popular_treks' in stats_data
        assert 'bookings_per_month' in stats_data
        assert 'users_participated' in stats_data
        assert isinstance(stats_data['popular_treks'], list)
        assert isinstance(stats_data['bookings_per_month'], list)
        print("  PASS: GET /api/admin/stats returned chart-ready arrays.")

        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Test 9] Cleaning up test records...")
        db.session.delete(test_booking)
        db.session.delete(trek)
        db.session.delete(db.session.get(User, staff_id))
        db.session.delete(db.session.get(User, user_id))
        db.session.commit()
        print("  PASS: Test records cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 3 ADMIN API SPECIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()

