import os
import sys
import csv
import json
from datetime import datetime, date, timedelta

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile, Trek, Booking, Notification
from config import Config
from tasks import export_bookings_csv, daily_reminders, monthly_report

def setup_test_data(app):
    with app.app_context():
        # Clean existing test data
        Booking.query.delete()
        Notification.query.delete()
        Trek.query.delete()
        StaffProfile.query.delete()
        User.query.filter(User.role != 'admin').delete()
        db.session.commit()

        # Create test trekker user
        user = User(
            name="Alice Trekker",
            email="alice@test.com",
            phone="9876543210",
            role="user",
            status="active"
        )
        user.set_password("password123")
        db.session.add(user)

        # Create another test user (Bob) for permission checks
        bob = User(
            name="Bob Trekker",
            email="bob@test.com",
            phone="9876543211",
            role="user",
            status="active"
        )
        bob.set_password("password123")
        db.session.add(bob)

        # Create test staff
        staff = User(
            name="Guide Dave",
            email="guide.dave@test.com",
            phone="9876543212",
            role="staff",
            status="active"
        )
        staff.set_password("password123")
        db.session.add(staff)
        db.session.flush()

        profile = StaffProfile(
            user_id=staff.id,
            contact_details="basecamp@himalayas.com",
            specialization="High Altitude"
        )
        db.session.add(profile)

        # Create Trek 1: Starting tomorrow (within 2-day reminder window)
        tomorrow = date.today() + timedelta(days=1)
        trek1 = Trek(
            name="Kedarkantha Winter Summit",
            location="Uttarakhand",
            difficulty="Moderate",
            duration_days=5,
            total_slots=20,
            available_slots=18,
            assigned_staff_id=staff.id,
            status="Open",
            start_date=tomorrow,
            end_date=tomorrow + timedelta(days=5),
            description="A scenic winter wonderland peak trek.",
            price=9500.0,
            instructions="Bring thermal innerwear and trekking poles."
        )
        db.session.add(trek1)

        # Create Trek 2: Starting in 15 days (outside 2-day reminder window)
        future = date.today() + timedelta(days=15)
        trek2 = Trek(
            name="Hampta Pass Crossing",
            location="Himachal Pradesh",
            difficulty="Hard",
            duration_days=6,
            total_slots=15,
            available_slots=14,
            assigned_staff_id=staff.id,
            status="Open",
            start_date=future,
            end_date=future + timedelta(days=6),
            description="Dramatic crossover trek from Kullu to Spiti valley.",
            price=12000.0,
            instructions="Crampons provided at basecamp."
        )
        db.session.add(trek2)

        # Create Trek 3: Completed in past
        past_start = date.today() - timedelta(days=30)
        trek3 = Trek(
            name="Triund Weekend Trek",
            location="Dharamshala",
            difficulty="Easy",
            duration_days=2,
            total_slots=25,
            available_slots=20,
            assigned_staff_id=staff.id,
            status="Completed",
            start_date=past_start,
            end_date=past_start + timedelta(days=2),
            description="Popular gentle ridge trek near McLeodGanj.",
            price=3500.0
        )
        db.session.add(trek3)
        db.session.flush()

        # Add bookings for Alice
        b1 = Booking(
            user_id=user.id,
            trek_id=trek1.id,
            booking_date=datetime.utcnow() - timedelta(days=2),
            status="Booked",
            payment_status="Paid",
            participants_count=2
        )
        b2 = Booking(
            user_id=user.id,
            trek_id=trek3.id,
            booking_date=datetime.utcnow() - timedelta(days=32),
            status="Completed",
            payment_status="Paid",
            participants_count=1
        )
        db.session.add_all([b1, b2])

        # Add booking for Bob on Trek 2
        b3 = Booking(
            user_id=bob.id,
            trek_id=trek2.id,
            booking_date=datetime.utcnow() - timedelta(days=1),
            status="Booked",
            payment_status="Paid",
            participants_count=1
        )
        db.session.add(b3)

        db.session.commit()
        return user.id, bob.id, staff.id, trek1.id, trek2.id, trek3.id

def run_tests():
    app = create_app()
    client = app.test_client()

    print("=== STARTING PHASE 7 TEST SUITE (CELERY JOBS & BATCH PROCESSING) ===")

    user_id, bob_id, staff_id, trek1_id, trek2_id, trek3_id = setup_test_data(app)

    # 1. Obtain Auth Tokens
    admin_login = client.post('/api/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    assert admin_login.status_code == 200
    admin_token = admin_login.get_json()['data']['token']

    alice_login = client.post('/api/auth/login', json={'email': 'alice@test.com', 'password': 'password123'})
    assert alice_login.status_code == 200
    alice_token = alice_login.get_json()['data']['token']

    bob_login = client.post('/api/auth/login', json={'email': 'bob@test.com', 'password': 'password123'})
    assert bob_login.status_code == 200
    bob_token = bob_login.get_json()['data']['token']

    print("✔ Authentication tokens acquired successfully.")

    with app.app_context():
        # -----------------------------------------------------------------
        # TEST 1: User CSV Export Direct Task Function
        # -----------------------------------------------------------------
        print("\n--- TEST 1: export_bookings_csv() direct task execution ---")
        export_res = export_bookings_csv(user_id)
        assert export_res['status'] == 'SUCCESS'
        filename = export_res['filename']
        assert filename.startswith(f"bookings_user_{user_id}_")
        assert filename.endswith(".csv")

        # Check file exists in exports/
        csv_path = os.path.join(Config.EXPORTS_DIR, filename)
        assert os.path.exists(csv_path), f"File {csv_path} does not exist!"

        # Verify CSV contents and exact 7 required columns
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_header = [
                'User ID',
                'Trek Name',
                'Location',
                'Booking Status',
                'Booking Date',
                'Trek Start Date',
                'Trek End Date'
            ]
            assert header == expected_header, f"Header mismatch: {header} vs {expected_header}"
            rows = list(reader)
            assert len(rows) == 2, f"Expected 2 bookings for Alice, got {len(rows)}"

        # Verify Notification generated for user
        notif = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).first()
        assert notif is not None
        assert "Your export is ready" in notif.message
        assert export_res['download_url'] in notif.message
        print(f"✔ CSV Export generated {filename} with 7 valid columns and notification created.")

        # -----------------------------------------------------------------
        # TEST 2: User Export Endpoints (POST /export, GET /export/<task_id>, GET /exports/<filename>)
        # -----------------------------------------------------------------
        print("\n--- TEST 2: User Export API Endpoints ---")
        alice_headers = {'Authorization': f'Bearer {alice_token}'}
        bob_headers = {'Authorization': f'Bearer {bob_token}'}

        # 2a. POST /api/user/export triggers job (202 Accepted)
        post_exp = client.post('/api/user/export', headers=alice_headers)
        assert post_exp.status_code == 202
        post_data = post_exp.get_json()['data']
        task_id = post_data['task_id']
        assert task_id is not None
        print(f"✔ POST /api/user/export returned 202 Accepted with task_id: {task_id}")

        # 2b. GET /api/user/export/<task_id> returns task status
        get_status = client.get(f'/api/user/export/{task_id}', headers=alice_headers)
        assert get_status.status_code == 200
        status_data = get_status.get_json()['data']
        assert status_data['task_id'] == task_id
        print(f"✔ GET /api/user/export/<task_id> status: {status_data.get('status')}")

        # 2c. GET /api/user/exports/<filename> for Alice (Owner)
        get_file = client.get(f'/api/user/exports/{filename}', headers=alice_headers)
        assert get_file.status_code == 200
        assert get_file.mimetype == 'text/csv'
        assert b"Kedarkantha Winter Summit" in get_file.data
        print("✔ GET /api/user/exports/<filename> successfully downloaded by owner (Alice).")

        # 2d. Bob attempting to download Alice's export must return 403 Forbidden
        bob_attempt = client.get(f'/api/user/exports/{filename}', headers=bob_headers)
        assert bob_attempt.status_code == 403
        print("✔ Bob forbidden (403) from downloading Alice's export file.")

        # -----------------------------------------------------------------
        # TEST 3: Scheduled Job 1: daily_reminders()
        # -----------------------------------------------------------------
        print("\n--- TEST 3: daily_reminders() execution ---")
        reminder_res = daily_reminders(days_ahead=2)
        assert reminder_res['status'] == 'completed'
        # Trek 1 starts tomorrow (1 day ahead <= 2 days ahead window) -> should send 1 reminder
        # Trek 2 starts in 15 days (> 2 days) -> should not send reminder
        assert reminder_res['reminders_sent'] == 1, f"Expected 1 reminder, got {reminder_res['reminders_sent']}"

        # Verify notification for Alice in DB
        rem_notif = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.message.like('%Trek Reminder: \'Kedarkantha Winter Summit\'%')
        ).first()
        assert rem_notif is not None, "Reminder notification was not created in DB!"
        assert "Bring thermal innerwear" in rem_notif.message
        print(f"✔ daily_reminders sent 1 reminder for upcoming trek within 2 days; in-app notification recorded.")

        # -----------------------------------------------------------------
        # TEST 4: Scheduled Job 2: monthly_report()
        # -----------------------------------------------------------------
        print("\n--- TEST 4: monthly_report() execution ---")
        report_res = monthly_report()
        assert report_res['status'] == 'completed'
        report_filename = report_res['report_filename']
        assert report_filename.endswith('.html')

        report_path = os.path.join(Config.EXPORTS_DIR, report_filename)
        assert os.path.exists(report_path), f"Report {report_path} was not created!"

        with open(report_path, mode='r', encoding='utf-8') as f:
            html = f.read()
            assert "<!DOCTYPE html>" in html
            assert "TMA Monthly Activity Report" in html
            assert "Treks Conducted" in html
            assert "Unique Trekkers" in html
            assert "Kedarkantha Winter Summit" in html
            assert "style=" in html  # Verify inline-CSS styling

        # Verify Admin Notification was created
        admin = User.query.filter_by(role='admin').first()
        admin_notif = Notification.query.filter(
            Notification.user_id == admin.id,
            Notification.message.like('%Monthly Activity Report%')
        ).first()
        assert admin_notif is not None
        print(f"✔ monthly_report created styled HTML report {report_filename} in exports/ and notified admin.")

        # -----------------------------------------------------------------
        # TEST 5: Admin Manual Job Trigger Endpoint (POST /api/admin/jobs/<name>/run)
        # -----------------------------------------------------------------
        print("\n--- TEST 5: Admin Manual Job Trigger Endpoint ---")
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 5a. Invalid job name -> 400
        inv_job = client.post('/api/admin/jobs/invalid_job/run', headers=admin_headers)
        assert inv_job.status_code == 400
        print("✔ Invalid job trigger correctly returned 400 Bad Request.")

        # 5b. Regular user attempting to run admin job -> 403 Forbidden
        user_run = client.post('/api/admin/jobs/daily_reminders/run', headers=alice_headers)
        assert user_run.status_code == 403
        print("✔ Regular user forbidden (403) from running admin batch jobs.")

        # 5c. Admin triggers daily_reminders -> 200 or 202
        run_reminders = client.post('/api/admin/jobs/daily_reminders/run', headers=admin_headers)
        assert run_reminders.status_code in [200, 202]
        print(f"✔ Admin manually triggered daily_reminders (Status {run_reminders.status_code}).")

        # 5d. Admin triggers monthly_report -> 200 or 202
        run_report = client.post('/api/admin/jobs/monthly_report/run', headers=admin_headers)
        assert run_report.status_code in [200, 202]
        print(f"✔ Admin manually triggered monthly_report (Status {run_report.status_code}).")

    print("\n=== ALL PHASE 7 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
