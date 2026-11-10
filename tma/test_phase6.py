import os
import sys
import time

# Ensure tma directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from models import User, Trek, Booking, Notification
import cache

def run_tests():
    print("=" * 65)
    print("RUNNING TMA PART 6: REDIS CACHING & INVALIDATION TEST SUITE")
    print("=" * 65)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Setup: Ensure clean cache and seed a test trek & users
        cache.invalidate_trek_cache()

        # Login as Admin
        admin_login = client.post('/api/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
        assert admin_login.status_code == 200
        admin_token = admin_login.get_json()['data']['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # Register & Login Trekker User
        u = User.query.filter_by(email='cache_trekker@tma.com').first()
        if u:
            db.session.delete(u)
        db.session.commit()

        user_reg = client.post('/api/auth/register', json={
            'name': 'Cache Trekker',
            'email': 'cache_trekker@tma.com',
            'password': 'password123',
            'phone': '9876543210'
        })
        assert user_reg.status_code == 201
        user_token = user_reg.get_json()['data']['token']
        user_headers = {'Authorization': f'Bearer {user_token}'}

        # Create a test trek
        t_exist = Trek.query.filter_by(name='Kashmir Great Lakes Trek').first()
        if t_exist:
            db.session.delete(t_exist)
            db.session.commit()

        trek = Trek(
            name="Kashmir Great Lakes Trek",
            location="Sonamarg, J&K",
            difficulty="Moderate",
            duration_days=7,
            total_slots=16,
            available_slots=16,
            status="Open",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 8),
            description="Seven turquoise high altitude alpine lakes.",
            price=15000.0
        )
        db.session.add(trek)
        db.session.commit()
        trek_id = trek.id

        # -------------------------------------------------------------
        # 1. Test cache.py Helper Functions Directly
        # -------------------------------------------------------------
        print("\n[Test 1] Testing cache.py Helper Functions (get_json, set_json, delete_pattern)...")
        cache.set_json("test:key:1", {"foo": "bar", "val": 42}, ttl=60)
        cached_val = cache.get_json("test:key:1")
        assert cached_val is not None
        assert cached_val["foo"] == "bar"
        assert cached_val["val"] == 42
        print("  PASS: set_json() and get_json() stored and retrieved object correctly.")

        # Test pattern deletion
        cache.set_json("test:pattern:a", 1)
        cache.set_json("test:pattern:b", 2)
        deleted = cache.delete_pattern("test:pattern:*")
        assert deleted >= 2
        assert cache.get_json("test:pattern:a") is None
        assert cache.get_json("test:pattern:b") is None
        print("  PASS: delete_pattern() successfully purged matching wildcard keys.")

        # -------------------------------------------------------------
        # 2. User Trek Catalog Caching & X-Cache Header
        # -------------------------------------------------------------
        print("\n[Test 2] Testing User Trek Catalog Caching (GET /api/user/treks)...")
        # Ensure fresh cache
        cache.invalidate_trek_cache()

        # Request 1: Must be Cache MISS
        t0 = time.perf_counter()
        res1 = client.get('/api/user/treks?q=Kashmir', headers=user_headers)
        t_miss = (time.perf_counter() - t0) * 1000
        assert res1.status_code == 200
        assert res1.headers.get('X-Cache') == 'MISS', f"Expected X-Cache: MISS, got {res1.headers.get('X-Cache')}"
        print(f"  PASS: 1st Request returned X-Cache: MISS (Latency: {t_miss:.2f} ms).")

        # Request 2: Must be Cache HIT
        t0 = time.perf_counter()
        res2 = client.get('/api/user/treks?q=Kashmir', headers=user_headers)
        t_hit = (time.perf_counter() - t0) * 1000
        assert res2.status_code == 200
        assert res2.headers.get('X-Cache') == 'HIT', f"Expected X-Cache: HIT, got {res2.headers.get('X-Cache')}"
        print(f"  PASS: 2nd Request returned X-Cache: HIT (Latency: {t_hit:.2f} ms).")
        print(f"        Performance speedup: {t_miss / max(0.001, t_hit):.1f}x faster!")

        # -------------------------------------------------------------
        # 3. Single Trek Details Caching
        # -------------------------------------------------------------
        print("\n[Test 3] Testing Single Trek Details Caching (GET /api/user/treks/<id>)...")
        cache.delete_pattern(f"trek:detail:{trek_id}")

        # Request 1: MISS
        res_d1 = client.get(f'/api/user/treks/{trek_id}', headers=user_headers)
        assert res_d1.status_code == 200
        assert res_d1.headers.get('X-Cache') == 'MISS'
        print("  PASS: 1st Details Request returned X-Cache: MISS.")

        # Request 2: HIT
        res_d2 = client.get(f'/api/user/treks/{trek_id}', headers=user_headers)
        assert res_d2.status_code == 200
        assert res_d2.headers.get('X-Cache') == 'HIT'
        print("  PASS: 2nd Details Request returned X-Cache: HIT.")

        # -------------------------------------------------------------
        # 4. Admin Dashboard Counts Caching
        # -------------------------------------------------------------
        print("\n[Test 4] Testing Admin Dashboard Caching (GET /api/admin/dashboard)...")
        cache.delete_pattern("admin:dashboard*")

        # Request 1: MISS
        dash1 = client.get('/api/admin/dashboard', headers=admin_headers)
        assert dash1.status_code == 200
        assert dash1.headers.get('X-Cache') == 'MISS'
        print("  PASS: 1st Admin Dashboard Request returned X-Cache: MISS.")

        # Request 2: HIT
        dash2 = client.get('/api/admin/dashboard', headers=admin_headers)
        assert dash2.status_code == 200
        assert dash2.headers.get('X-Cache') == 'HIT'
        print("  PASS: 2nd Admin Dashboard Request returned X-Cache: HIT.")

        # -------------------------------------------------------------
        # 5. Admin Stats Caching
        # -------------------------------------------------------------
        print("\n[Test 5] Testing Admin Stats Caching (GET /api/admin/stats)...")
        cache.delete_pattern("admin:stats*")

        # Request 1: MISS
        stats1 = client.get('/api/admin/stats', headers=admin_headers)
        assert stats1.status_code == 200
        assert stats1.headers.get('X-Cache') == 'MISS'
        print("  PASS: 1st Admin Stats Request returned X-Cache: MISS.")

        # Request 2: HIT
        stats2 = client.get('/api/admin/stats', headers=admin_headers)
        assert stats2.status_code == 200
        assert stats2.headers.get('X-Cache') == 'HIT'
        print("  PASS: 2nd Admin Stats Request returned X-Cache: HIT.")

        # -------------------------------------------------------------
        # 6. Cache Invalidation Verification
        # -------------------------------------------------------------
        print("\n[Test 6] Verifying Cache Invalidation on Mutation...")
        # Verify cache is currently HIT for trek catalog and admin dashboard
        assert client.get('/api/user/treks?q=Kashmir', headers=user_headers).headers.get('X-Cache') == 'HIT'
        assert client.get('/api/admin/dashboard', headers=admin_headers).headers.get('X-Cache') == 'HIT'

        # Action: User books a slot on the trek (which triggers invalidate_trek_cache)
        book_res = client.post('/api/user/bookings', headers=user_headers, json={
            'trek_id': trek_id,
            'participants_count': 2
        })
        assert book_res.status_code == 201

        # Check: Next catalog query MUST now be a MISS because slots changed!
        res_after_book = client.get('/api/user/treks?q=Kashmir', headers=user_headers)
        assert res_after_book.headers.get('X-Cache') == 'MISS', f"Expected X-Cache: MISS after booking mutation, got {res_after_book.headers.get('X-Cache')}"
        assert res_after_book.get_json()['data']['treks'][0]['available_slots'] == 14
        print("  PASS: Catalog cache invalidated upon booking creation. Returned X-Cache: MISS with updated slots (14).")

        # Check: Admin dashboard cache was also invalidated!
        dash_after_book = client.get('/api/admin/dashboard', headers=admin_headers)
        assert dash_after_book.headers.get('X-Cache') == 'MISS'
        print("  PASS: Admin dashboard cache invalidated upon booking. Returned X-Cache: MISS with updated booking counts.")

        # -------------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------------
        print("\n[Test 7] Cleaning up test artifacts...")
        Notification.query.filter_by(user_id=user_reg.get_json()['data']['user']['id']).delete()
        Booking.query.filter_by(trek_id=trek_id).delete()
        db.session.delete(trek)
        db.session.delete(db.session.get(User, user_reg.get_json()['data']['user']['id']))
        db.session.commit()
        cache.invalidate_trek_cache()
        print("  PASS: Test artifacts and cache cleaned up successfully.")

    print("\n" + "=" * 65)
    print("ALL PART 6 REDIS CACHING TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    from datetime import date
    run_tests()

