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
    print("RUNNING TMA PART 1 RIGOROUS SPECIFICATION TEST SUITE")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # -------------------------------------------------------------
        # Test 1: Programmatic DB Creation & Admin Seeding
        # -------------------------------------------------------------
        print("\n[Test 1] Verifying Programmatic Database Creation & Admin Seeding...")
        admins = User.query.filter_by(role='admin').all()
        assert len(admins) == 1, f"Expected exactly 1 admin, found {len(admins)}"
        admin = admins[0]
        assert admin.email == 'admin@tma.com', f"Expected admin@tma.com, got {admin.email}"
        assert admin.check_password('admin123') is True, "Admin password verification failed"
        assert admin.role == 'admin'
        assert admin.status == 'active'
        print(f"  PASS: Admin correctly seeded: {admin.email} (Status: {admin.status})")

        # -------------------------------------------------------------
        # Test 2: Health Check Endpoint (/api/health)
        # -------------------------------------------------------------
        print("\n[Test 2] Verifying /api/health Endpoint...")
        health_res = client.get('/api/health')
        assert health_res.status_code == 200, f"Expected 200, got {health_res.status_code}"
        health_data = health_res.get_json()
        assert health_data['success'] is True
        assert health_data['data']['status'] == 'healthy'
        assert health_data['data']['database'] == 'connected'
        print("  PASS: /api/health returned 200 OK with healthy status.")

        # -------------------------------------------------------------
        # Test 3: Frontend Entry Point (GET /)
        # -------------------------------------------------------------
        print("\n[Test 3] Verifying Single Entry Point (GET /)...")
        index_res = client.get('/')
        assert index_res.status_code == 200
        html_content = index_res.get_data(as_text=True)
        assert 'id="app"' in html_content, "Vue mount point missing in index.html"
        assert 'bootstrap' in html_content.lower(), "Bootstrap CDN missing in index.html"
        print("  PASS: GET / returned index.html containing Bootstrap & Vue mount point.")

        # -------------------------------------------------------------
        # Test 4: User Model with Profile Fields & to_dict()
        # -------------------------------------------------------------
        print("\n[Test 4] Verifying User Model & Profile Fields...")
        test_user = User(
            name="Rahul Sharma",
            email="rahul.sharma@example.com",
            phone="9876543210",
            role="user",
            status="active",
            age=26,
            emergency_contact="9876543211",
            address="123 Hill Road, Dehradun"
        )
        test_user.set_password("userPass123")
        db.session.add(test_user)
        db.session.commit()

        assert test_user.id is not None
        assert test_user.check_password("userPass123") is True
        assert test_user.is_active is True
        user_dict = test_user.to_dict()
        assert user_dict['email'] == "rahul.sharma@example.com"
        assert user_dict['age'] == 26
        assert user_dict['phone'] == "9876543210"
        print("  PASS: User model fields, password hashing, and to_dict() validated.")

        # -------------------------------------------------------------
        # Test 5: Staff User & StaffProfile Model
        # -------------------------------------------------------------
        print("\n[Test 5] Verifying Staff User & StaffProfile Table...")
        staff_user = User(
            name="Vikram Singh",
            email="vikram.guide@tma.com",
            phone="9123456789",
            role="staff",
            status="active"
        )
        staff_user.set_password("staffPass123")
        db.session.add(staff_user)
        db.session.commit()

        staff_profile = StaffProfile(
            user_id=staff_user.id,
            contact_details="Base Camp Radio: Channel 4",
            specialization="High Altitude Rescue & First Aid",
            status="active",
            joined_on=date.today()
        )
        db.session.add(staff_profile)
        db.session.commit()

        assert staff_user.staff_profile is not None
        assert staff_user.staff_profile.specialization == "High Altitude Rescue & First Aid"
        staff_dict = staff_user.to_dict()
        assert 'staff_profile' in staff_dict
        assert staff_dict['staff_profile']['specialization'] == "High Altitude Rescue & First Aid"
        print("  PASS: StaffProfile table and relationship to User validated.")

        # -------------------------------------------------------------
        # Test 6: Trek Model (All fields, Status, Soft-delete flag)
        # -------------------------------------------------------------
        print("\n[Test 6] Verifying Trek Model & Slot Management...")
        trek = Trek(
            name="Roopkund Expedition",
            location="Chamoli, Uttarakhand",
            difficulty="Hard",
            duration_days=8,
            total_slots=15,
            available_slots=15,
            assigned_staff_id=staff_user.id,
            status="Open",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 8),
            description="Challenging high altitude trek to the mystery lake.",
            instructions="Carry warm thermal layers and crampons.",
            price=16500.0,
            is_deleted=False
        )
        db.session.add(trek)
        db.session.commit()

        assert trek.id is not None
        assert trek.assigned_staff.name == "Vikram Singh"
        trek_dict = trek.to_dict()
        assert trek_dict['difficulty'] == "Hard"
        assert trek_dict['assigned_staff_name'] == "Vikram Singh"
        assert trek_dict['available_slots'] == 15
        assert trek_dict['is_deleted'] is False
        print("  PASS: Trek model with staff assignment and status validated.")

        # -------------------------------------------------------------
        # Test 7: Booking Model & Duplicate Active Booking Check
        # -------------------------------------------------------------
        print("\n[Test 7] Verifying Booking Model & Duplicate Active Booking Check...")
        assert Booking.has_active_booking(test_user.id, trek.id) is False

        booking = Booking(
            user_id=test_user.id,
            trek_id=trek.id,
            booking_date=datetime.utcnow(),
            status="Booked",
            payment_status="Paid",
            participants_count=2
        )
        db.session.add(booking)
        db.session.commit()

        # Recalculate available slots
        trek.recalculate_available_slots()
        db.session.commit()

        assert trek.available_slots == 13, f"Expected 13 slots, got {trek.available_slots}"
        assert Booking.has_active_booking(test_user.id, trek.id) is True
        print("  PASS: Booking created, available slots updated (15 -> 13), and duplicate check passes.")

        # -------------------------------------------------------------
        # Test 8: Notification Model & to_dict()
        # -------------------------------------------------------------
        print("\n[Test 8] Verifying Notification Model...")
        notification = Notification(
            user_id=test_user.id,
            message="Your booking for Roopkund Expedition is confirmed!",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        assert notification.id is not None
        assert notification.is_read is False
        notif_dict = notification.to_dict()
        assert notif_dict['is_read'] is False
        assert "Roopkund" in notif_dict['message']
        print("  PASS: Notification model created and to_dict() verified.")

        # -------------------------------------------------------------
        # Test 9: Cleanup Test Data
        # -------------------------------------------------------------
        print("\n[Test 9] Cleaning up test data (leaving seeded admin)...")
        db.session.delete(notification)
        db.session.delete(booking)
        db.session.delete(trek)
        db.session.delete(staff_profile)
        db.session.delete(staff_user)
        db.session.delete(test_user)
        db.session.commit()
        print("  PASS: Test artifacts cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 1 SPECIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()
