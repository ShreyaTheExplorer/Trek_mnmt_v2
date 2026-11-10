import os
import sys

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app

def run_tests():
    print("=== STARTING PHASE 8 TEST SUITE (FRONTEND FOUNDATION & ADMIN UI) ===")
    app = create_app()
    client = app.test_client()

    # -------------------------------------------------------------
    # TEST 1: Single Entry Point (GET /)
    # -------------------------------------------------------------
    print("\n--- TEST 1: Verifying Single Entry Point (GET /) ---")
    res = client.get('/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.data.decode('utf-8')

    # Verify Vue mount point
    assert '<div id="app"></div>' in html, "Missing #app mount point!"

    # Verify CDN script inclusions
    cdn_dependencies = [
        'bootstrap@5.3.3/dist/css/bootstrap.min.css',
        'bootstrap-icons@1.11.3',
        'bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
        'vue@3.4.38/dist/vue.global.prod.js',
        'vue-router@4.3.0/dist/vue-router.global.prod.js',
        'chart.js@4.4.3/dist/chart.umd.min.js'
    ]
    for dep in cdn_dependencies:
        assert dep in html, f"Missing CDN dependency in index.html: {dep}"
    print("✔ Single entry point index.html loaded with all 6 required CDN libraries.")

    # -------------------------------------------------------------
    # TEST 2: Static Files Accessibility via HTTP
    # -------------------------------------------------------------
    print("\n--- TEST 2: Verifying Static Files Accessibility ---")
    static_files = [
        '/static/css/custom.css',
        '/static/js/api.js',
        '/static/js/router.js',
        '/static/js/app.js',
        '/static/js/components/Toast.js',
        '/static/js/components/Navbar.js',
        '/static/js/components/LoginPage.js',
        '/static/js/components/RegisterPage.js',
        '/static/js/components/Placeholders.js',
        '/static/js/components/AdminDashboard.js',
        '/static/js/components/AdminTreks.js',
        '/static/js/components/AdminStaff.js',
        '/static/js/components/AdminUsers.js',
        '/static/js/components/AdminBookings.js',
        '/static/js/components/AdminSearch.js',
        '/static/js/components/AdminView.js'
    ]

    for path in static_files:
        resp = client.get(path)
        assert resp.status_code == 200, f"Failed to serve static file: {path} (Status {resp.status_code})"
        assert len(resp.data) > 0, f"Static file {path} is empty!"
        assert path in html, f"Static script reference {path} missing from index.html"
    print(f"✔ All {len(static_files)} frontend static files served successfully with HTTP 200.")

    # -------------------------------------------------------------
    # TEST 3: Component Structure & Code Verification
    # -------------------------------------------------------------
    print("\n--- TEST 3: Verifying Component Definitions & API Integrations ---")
    
    # 3a. api.js
    api_js = client.get('/static/js/api.js').data.decode('utf-8')
    assert 'localStorage.getItem(\'tma_token\')' in api_js
    assert 'Bearer' in api_js
    assert 'setAuth' in api_js
    assert 'clearAuth' in api_js
    print("✔ api.js: Bearer token management, 401 handling, and session state verified.")

    # 3b. router.js
    router_js = client.get('/static/js/router.js').data.decode('utf-8')
    assert 'beforeEach' in router_js
    assert 'requiresAuth' in router_js
    assert '/admin' in router_js
    assert '/login' in router_js
    assert '/register' in router_js
    print("✔ router.js: Role-based navigation guards and redirection verified.")

    # 3c. AdminDashboard.js
    dash_js = client.get('/static/js/components/AdminDashboard.js').data.decode('utf-8')
    assert 'new Chart(' in dash_js
    assert 'popularTreksChart' in dash_js
    assert 'monthlyTrendsChart' in dash_js
    assert '/admin/dashboard' in dash_js
    assert '/admin/stats' in dash_js
    print("✔ AdminDashboard.js: Stat cards and Chart.js integration verified.")

    # 3d. AdminTreks.js
    treks_js = client.get('/static/js/components/AdminTreks.js').data.decode('utf-8')
    assert 'openCreateModal' in treks_js
    assert 'openEditModal' in treks_js
    assert 'openAssignModal' in treks_js
    assert 'updateTrekStatus' in treks_js
    assert 'confirmDelete' in treks_js
    print("✔ AdminTreks.js: Search, create/edit modal, delete, staff assignment, and status controls verified.")

    # 3e. AdminStaff.js
    staff_js = client.get('/static/js/components/AdminStaff.js').data.decode('utf-8')
    assert 'createStaff' in staff_js
    assert 'setStaffStatus' in staff_js
    assert 'openAddModal' in staff_js
    print("✔ AdminStaff.js: Staff listing, onboarding modal, and status controls verified.")

    # 3f. AdminUsers.js
    users_js = client.get('/static/js/components/AdminUsers.js').data.decode('utf-8')
    assert 'setUserStatus' in users_js
    assert 'fetchUsers' in users_js
    print("✔ AdminUsers.js: User directory and deactivate/blacklist controls verified.")

    # 3g. AdminBookings.js
    bookings_js = client.get('/static/js/components/AdminBookings.js').data.decode('utf-8')
    assert 'fetchBookings' in bookings_js
    assert 'filterStatus' in bookings_js
    print("✔ AdminBookings.js: Global booking ledger with filters and history verified.")

    # 3h. AdminSearch.js
    search_js = client.get('/static/js/components/AdminSearch.js').data.decode('utf-8')
    assert 'performSearch' in search_js
    assert '/admin/search' in search_js
    print("✔ AdminSearch.js: Global administrative search verified.")

    # 3i. HTML5 Validations in RegisterPage.js
    reg_js = client.get('/static/js/components/RegisterPage.js').data.decode('utf-8')
    assert 'required' in reg_js
    assert 'minlength="6"' in reg_js
    assert 'pattern="' in reg_js
    print("✔ RegisterPage.js: HTML5 validations (required, minlength, phone pattern) verified.")

    print("\n=== ALL PHASE 8 FRONTEND TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()

