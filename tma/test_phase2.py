import os
import sys

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, StaffProfile

def run_tests():
    print("=" * 65)
    print("RUNNING TMA PART 2: AUTHENTICATION & RBAC TEST SUITE")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup: clean up previous test users if any
        for email in ['trekker_test@tma.com', 'staff_test@tma.com', 'blacklisted@tma.com', 'inactive@tma.com']:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
        db.session.commit()

        # -------------------------------------------------------------
        # 1. Registration Validations
        # -------------------------------------------------------------
        print("\n[Test 1] Testing Registration Validations (/api/auth/register)...")

        # Name too short
        res = client.post('/api/auth/register', json={
            'name': 'A',
            'email': 'trekker_test@tma.com',
            'password': 'password123',
            'phone': '9876543210'
        })
        assert res.status_code == 400, f"Expected 400 for short name, got {res.status_code}"

        # Invalid email format
        res = client.post('/api/auth/register', json={
            'name': 'Valid Name',
            'email': 'not-an-email',
            'password': 'password123',
            'phone': '9876543210'
        })
        assert res.status_code == 400, f"Expected 400 for invalid email, got {res.status_code}"

        # Missing / invalid phone
        res = client.post('/api/auth/register', json={
            'name': 'Valid Name',
            'email': 'trekker_test@tma.com',
            'password': 'password123',
            'phone': '123' # too short
        })
        assert res.status_code == 400, f"Expected 400 for short phone, got {res.status_code}"

        # Password length < 6
        res = client.post('/api/auth/register', json={
            'name': 'Valid Name',
            'email': 'trekker_test@tma.com',
            'password': '123',
            'phone': '9876543210'
        })
        assert res.status_code == 400, f"Expected 400 for short password, got {res.status_code}"
        print("  PASS: All input validation checks returned 400 Bad Request.")

        # -------------------------------------------------------------
        # 2. Successful Registration & Role Forcing
        # -------------------------------------------------------------
        print("\n[Test 2] Testing Successful Registration & Role Forcing...")
        res = client.post('/api/auth/register', json={
            'name': 'Pooja Verma',
            'email': 'trekker_test@tma.com',
            'password': 'password123',
            'phone': '9876543210',
            'role': 'admin', # Attempt to escalate privilege
            'age': 25,
            'emergency_contact': '9876543211',
            'address': 'Kolkata, WB'
        })
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.get_data(as_text=True)}"
        data = res.get_json()
        assert data['success'] is True
        assert data['data']['role'] == 'user', f"Role must be forced to 'user', got {data['data']['role']}"
        assert data['data']['name'] == 'Pooja Verma'
        assert 'token' in data['data']
        user_token = data['data']['token']
        print(f"  PASS: User registered. Role strictly forced to 'user'. Token generated.")

        # Duplicate email check
        res_dup = client.post('/api/auth/register', json={
            'name': 'Pooja Verma',
            'email': 'trekker_test@tma.com',
            'password': 'password123',
            'phone': '9876543210'
        })
        assert res_dup.status_code == 409, f"Expected 409 Conflict, got {res_dup.status_code}"
        print("  PASS: Duplicate registration rejected with 409 Conflict.")

        # -------------------------------------------------------------
        # 3. Login for All Three Roles (Admin, Staff, User)
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Login for All Three Roles...")

        # 3A. Admin Login
        res_admin = client.post('/api/auth/login', json={
            'email': 'admin@tma.com',
            'password': 'admin123'
        })
        assert res_admin.status_code == 200
        admin_data = res_admin.get_json()['data']
        assert admin_data['role'] == 'admin'
        assert admin_data['name'] == 'System Administrator'
        admin_token = admin_data['token']
        print("  PASS: Admin login successful. Role='admin', valid JWT token.")

        # 3B. User Login
        res_user = client.post('/api/auth/login', json={
            'email': 'trekker_test@tma.com',
            'password': 'password123'
        })
        assert res_user.status_code == 200
        user_login_data = res_user.get_json()['data']
        assert user_login_data['role'] == 'user'
        assert user_login_data['name'] == 'Pooja Verma'
        print("  PASS: Trekker user login successful. Role='user'.")

        # 3C. Staff Login (create staff account directly in DB or via admin)
        staff_user = User(
            name="Ramesh Thapa",
            email="staff_test@tma.com",
            phone="9123456789",
            role="staff",
            status="active"
        )
        staff_user.set_password("staff123")
        db.session.add(staff_user)
        db.session.commit()

        res_staff = client.post('/api/auth/login', json={
            'email': 'staff_test@tma.com',
            'password': 'staff123'
        })
        assert res_staff.status_code == 200
        staff_data = res_staff.get_json()['data']
        assert staff_data['role'] == 'staff'
        assert staff_data['name'] == 'Ramesh Thapa'
        staff_token = staff_data['token']
        print("  PASS: Staff login successful. Role='staff'.")

        # -------------------------------------------------------------
        # 4. Refuse Inactive & Blacklisted Accounts
        # -------------------------------------------------------------
        print("\n[Test 4] Testing Rejection of Inactive & Blacklisted Accounts...")

        # Inactive user
        inactive_user = User(
            name="Inactive User",
            email="inactive@tma.com",
            phone="9876543299",
            role="user",
            status="inactive"
        )
        inactive_user.set_password("pass123")
        db.session.add(inactive_user)

        # Blacklisted user
        blacklisted_user = User(
            name="Blacklisted User",
            email="blacklisted@tma.com",
            phone="9876543288",
            role="user",
            status="blacklisted"
        )
        blacklisted_user.set_password("pass123")
        db.session.add(blacklisted_user)
        db.session.commit()

        # Try logging in as inactive
        res_inact = client.post('/api/auth/login', json={
            'email': 'inactive@tma.com',
            'password': 'pass123'
        })
        assert res_inact.status_code == 403, f"Expected 403 for inactive login, got {res_inact.status_code}"
        assert 'inactive' in res_inact.get_json()['message'].lower()

        # Try logging in as blacklisted
        res_black = client.post('/api/auth/login', json={
            'email': 'blacklisted@tma.com',
            'password': 'pass123'
        })
        assert res_black.status_code == 403, f"Expected 403 for blacklisted login, got {res_black.status_code}"
        assert 'blacklisted' in res_black.get_json()['message'].lower()
        print("  PASS: Inactive and blacklisted accounts rejected on login with 403 and descriptive messages.")

        # -------------------------------------------------------------
        # 5. GET /api/auth/me & Protected Decorator
        # -------------------------------------------------------------
        print("\n[Test 5] Testing GET /api/auth/me...")
        # Without token
        res_no_tok = client.get('/api/auth/me')
        assert res_no_tok.status_code == 401

        # With user token
        res_me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {user_token}'})
        assert res_me.status_code == 200
        me_data = res_me.get_json()['data']
        assert me_data['email'] == 'trekker_test@tma.com'
        assert me_data['name'] == 'Pooja Verma'
        assert me_data['age'] == 25
        print(f"  PASS: /api/auth/me returned authenticated profile for {me_data['name']}.")

        # -------------------------------------------------------------
        # 6. PUT /api/auth/me (Profile update & optional password change)
        # -------------------------------------------------------------
        print("\n[Test 6] Testing PUT /api/auth/me (Profile Update & Password Change)...")
        res_update = client.put('/api/auth/me', headers={'Authorization': f'Bearer {user_token}'}, json={
            'name': 'Pooja V. Sharma',
            'phone': '9876500000',
            'age': 26,
            'current_password': 'password123',
            'new_password': 'newpassword456'
        })
        assert res_update.status_code == 200, f"Expected 200, got {res_update.status_code}"
        updated_data = res_update.get_json()['data']
        assert updated_data['name'] == 'Pooja V. Sharma'
        assert updated_data['phone'] == '9876500000'
        assert updated_data['age'] == 26
        print("  PASS: Profile fields updated and password changed.")

        # Verify old password no longer works
        res_old_login = client.post('/api/auth/login', json={
            'email': 'trekker_test@tma.com',
            'password': 'password123'
        })
        assert res_old_login.status_code == 401

        # Verify new password works
        res_new_login = client.post('/api/auth/login', json={
            'email': 'trekker_test@tma.com',
            'password': 'newpassword456'
        })
        assert res_new_login.status_code == 200
        new_token = res_new_login.get_json()['data']['token']
        print("  PASS: New password verified via /api/auth/login.")

        # -------------------------------------------------------------
        # 7. Role-Based Access Control (RBAC) Verification
        # -------------------------------------------------------------
        print("\n[Test 7] Verifying Role-Based Access Control (RBAC)...")

        # 7A. User token accessing Admin Dashboard -> MUST BE 403 Forbidden
        res_rbac_user = client.get('/api/admin/dashboard', headers={
            'Authorization': f'Bearer {new_token}'
        })
        assert res_rbac_user.status_code == 403, f"Expected 403 Forbidden for User accessing Admin, got {res_rbac_user.status_code}"
        print(f"  PASS: Trekker user token correctly denied access to admin route (403 Forbidden: {res_rbac_user.get_json()['message']})")

        # 7B. Staff token accessing Admin Dashboard -> MUST BE 403 Forbidden
        res_rbac_staff = client.get('/api/admin/dashboard', headers={
            'Authorization': f'Bearer {staff_token}'
        })
        assert res_rbac_staff.status_code == 403, f"Expected 403 Forbidden for Staff accessing Admin, got {res_rbac_staff.status_code}"
        print(f"  PASS: Staff token correctly denied access to admin route (403 Forbidden)")

        # 7C. Admin token accessing Admin Dashboard -> MUST BE 200 OK
        res_rbac_admin = client.get('/api/admin/dashboard', headers={
            'Authorization': f'Bearer {admin_token}'
        })
        assert res_rbac_admin.status_code == 200, f"Expected 200 OK for Admin accessing Admin, got {res_rbac_admin.status_code}"
        print(f"  PASS: Admin token granted access to admin dashboard (200 OK)")

        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Test 8] Cleaning up test accounts...")
        for u in [staff_user, inactive_user, blacklisted_user, User.query.filter_by(email='trekker_test@tma.com').first()]:
            if u:
                db.session.delete(u)
        db.session.commit()
        print("  PASS: Test accounts cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 2 AUTHENTICATION & RBAC TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()

