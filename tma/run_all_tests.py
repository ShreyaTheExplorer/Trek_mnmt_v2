"""
Master Test Runner for Trekking Management Application (TMA)
Executes all 10 Phase test suites sequentially and provides an executive summary report.
"""

import os
import sys
import time
import subprocess

TEST_SUITES = [
    ("Phase 1: Database Models & Seeding", "tma/test_phase1.py"),
    ("Phase 2: Authentication & RBAC", "tma/test_phase2.py"),
    ("Phase 3: Admin API Endpoints", "tma/test_phase3.py"),
    ("Phase 4: Staff API Endpoints", "tma/test_phase4.py"),
    ("Phase 5: Trekker / User API", "tma/test_phase5.py"),
    ("Phase 6: Redis Caching & Invalidation", "tma/test_phase6.py"),
    ("Phase 7: Celery Jobs & Batch Processing", "tma/test_phase7.py"),
    ("Phase 8: Frontend Foundation & Admin UI", "tma/test_phase8.py"),
    ("Phase 9: Staff UI & Expedition Operations", "tma/test_phase9.py"),
    ("Phase 10: Trekker / User UI", "tma/test_phase10.py"),
]

def main():
    python_exec = sys.executable
    print("=" * 75)
    print("TREKKING MANAGEMENT APPLICATION (TMA) - MASTER SPECIFICATION TEST RUNNER")
    print("=" * 75)
    print(f"Python Environment: {python_exec}")
    print(f"Total Test Suites: {len(TEST_SUITES)}\n")

    results = []
    total_start = time.time()

    for idx, (title, script_path) in enumerate(TEST_SUITES, 1):
        full_path = os.path.abspath(script_path)
        if not os.path.exists(full_path):
            # Try path relative to current dir
            alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.basename(script_path)))
            if os.path.exists(alt_path):
                full_path = alt_path

        print(f"[{idx}/{len(TEST_SUITES)}] Running {title}...")
        start_time = time.time()
        res = subprocess.run([python_exec, full_path], capture_output=True, text=True)
        duration = time.time() - start_time

        success = (res.returncode == 0)
        results.append({
            'index': idx,
            'title': title,
            'script': os.path.basename(script_path),
            'success': success,
            'duration': duration,
            'stdout': res.stdout,
            'stderr': res.stderr
        })

        if success:
            print(f"  ✔ PASSED ({duration:.2f}s)\n")
        else:
            print(f"  ✖ FAILED ({duration:.2f}s)")
            print(f"--- Output Preview ---")
            print(res.stdout[-400:] if res.stdout else '')
            print(res.stderr[-400:] if res.stderr else '')
            print("----------------------\n")

    total_duration = time.time() - total_start

    print("=" * 75)
    print("EXECUTIVE TEST SUITE SUMMARY")
    print("=" * 75)
    passed_count = sum(1 for r in results if r['success'])
    failed_count = len(results) - passed_count

    print(f"{'#':<3} {'Test Suite Title':<45} {'Duration':<12} {'Status'}")
    print("-" * 75)
    for r in results:
        status_str = "PASS ✔" if r['success'] else "FAIL ✖"
        print(f"{r['index']:<3} {r['title']:<45} {r['duration']:>6.2f}s     {status_str}")

    print("-" * 75)
    print(f"Total Suites: {len(results)} | Passed: {passed_count} | Failed: {failed_count} | Total Time: {total_duration:.2f}s")
    print("=" * 75)

    if failed_count == 0:
        print("\n🎉 ALL SPECIFICATIONS & REGRESSION TESTS PASSED WITH 100% SUCCESS!\n")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed_count} TEST SUITE(S) FAILED.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()

