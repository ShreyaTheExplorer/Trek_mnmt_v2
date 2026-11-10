# Trekking Management Application (TMA) - MAD-2 Project

A comprehensive, production-grade Trekking Management Application built in strict adherence to the **Modern Application Development 2 (MAD-2)** university course constraints, architectural principles, and rubric specifications.

---

## 1. Architectural & Technology Stack Compliance

TMA adheres strictly to the mandated library restrictions, zero-build frontend architecture, and uniform JSON API conventions:

- **Backend:**
  - **Framework:** Flask 3.1.2 REST API.
  - **ORM & Database:** Flask-SQLAlchemy 3.1.1 on SQLite (`tma.db`). Schema is initialized programmatically using `db.create_all()`—never via manual SQLite commands.
  - **Security & Authentication:** Werkzeug (`generate_password_hash`, `check_password_hash`) and PyJWT 2.10.1 (signed cryptographic bearer tokens containing `sub`, `role`, `email`, and `exp`).
  - **Caching:** `redis-py` 5.2.1 wrapper (`cache.py`) supporting graceful in-memory fallback if Redis is offline.
  - **Background & Scheduled Tasks:** Celery 5.4.0 with Redis broker and result backend.
  - **Zero Unauthorized Dependencies:** Only standard library modules (`smtplib`, `csv`, `json`, `urllib`, `datetime`, `os`, `sys`) are used. `requirements.txt` contains strictly allowed packages.
- **Frontend:**
  - **Architecture:** Zero-build Vue 3 Single Page Application (SPA). No Node.js, npm, Vite, Webpack, or CLI build tools.
  - **Single Entry Point:** `templates/index.html` is the **only** Jinja2 template in the application.
  - **CDN Dependencies:**
    - Vue.js 3 (`vue.global.prod.js`)
    - Vue Router 4 (`vue-router.global.prod.js`) with client-side RBAC guards
    - Bootstrap 5.3 & Bootstrap Icons 1.11 via CDN
    - Chart.js 4.4 via CDN for analytics visualization
- **API Standards:**
  - Every API endpoint uniformly returns JSON:
    ```json
    {
      "success": true,
      "message": "Human-readable status description",
      "data": { ... }
    }
    ```
  - Standard HTTP status codes: `200 OK`, `201 Created`, `202 Accepted`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`.

---

## 2. Prerequisites

1. **Python 3.10+** (Developed and verified on Python 3.13).
2. **Redis Server 6.0+** running locally on default port `6379`.
   - Windows users can run Redis via native Windows port or WSL2 (`redis-server`).

---

## 3. Installation & Setup

### Step 1: Clone or Open Project
```powershell
cd "c:\Users\VICTUS\OneDrive\Desktop\trekking proj\tma"
```

### Step 2: Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv ..\.venv

# Activate virtual environment (Windows PowerShell)
..\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Seed the Demo Database
Run the programmatic seed script to initialize `tma.db` with 1 Admin, 2 Staff Guides, 5 Trekkers (including 1 blacklisted account), 8 Mountain Expeditions across varied statuses, and 6 active/historical bookings:
```powershell
python seed_demo.py
```

---

## 4. Running the Application Infrastructure

Open 4 separate terminal windows to run the complete asynchronous stack:

### Terminal 1: Redis Server
```powershell
redis-server
```
*(Note: If Redis is offline, the Flask API will automatically degrade gracefully to a thread-safe in-memory cache).*

### Terminal 2: Celery Worker
On Windows, Celery worker requires the `-P solo` or `threads` execution pool:
```powershell
cd tma
..\.venv\Scripts\activate
celery -A celery_app.celery worker -l info -P solo
```

### Terminal 3: Celery Beat (Periodic Scheduler)
Celery Beat automatically schedules daily reminder emails and monthly executive reports:
```powershell
cd tma
..\.venv\Scripts\activate
celery -A celery_app.celery beat -l info
```

### Terminal 4: Flask API Application
```powershell
cd tma
..\.venv\Scripts\activate
python app.py
```
The application will be accessible in your web browser at: **`http://127.0.0.1:5000`**

---

## 5. Master Test Runner (100% Pass Rate)

To verify the entire specification across all 10 development phases end-to-end:
```powershell
cd tma
python run_all_tests.py
```

### Individual Test Suites:
```powershell
python test_phase1.py   # Models, schemas, programmatic SQLite, seeding
python test_phase2.py   # Auth, JWT tokens, RBAC, input validations, profile updates
python test_phase3.py   # Admin API: CRUD, assign staff, user toggles, unified search, stats
python test_phase4.py   # Staff API: assigned treks, slot controls, status toggle, start/complete
python test_phase5.py   # Trekker API: catalog filters, booking rules, overbooking, cancel, payments
python test_phase6.py   # Redis caching, TTL verification, invalidation triggers, X-Cache headers
python test_phase7.py   # Celery async jobs: CSV export, daily reminders, monthly HTML reports
python test_phase8.py   # Frontend foundation: Vue 3, Vue Router guards, Bootstrap 5, Admin UI
python test_phase9.py   # Staff UI: StaffDashboard, StaffTrekDetail, manifest roster, friendly errors
python test_phase10.py  # Trekker UI: UserDashboard, TrekBrowse, TrekDetail, MyBookings, Profile
```

---

## 6. Demonstration Credentials

All accounts are pre-populated by `seed_demo.py`:

| Role | Name | Email | Password | Assigned Expeditions / Role Details |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | System Administrator | `admin@tma.com` | `admin123` | System Super Administrator. Single programmatic admin account. |
| **Staff 1** | Karan Negi | `karan.staff@tma.com` | `staff123` | Senior Alpine Guide (Kedarkantha, Valley of Flowers, Kashmir Great Lakes). |
| **Staff 2** | Maya Sharma | `maya.staff@tma.com` | `staff123` | High Altitude Glacier Lead (Hampta Pass, Chadar Expedition, Triund Ridge). |
| **Trekker 1** | Aarav Mehta | `aarav@example.com` | `user123` | Active reservation for Kedarkantha Winter Summit (`Booked`). |
| **Trekker 2** | Sneha Patel | `sneha@example.com` | `user123` | Active reservation for Hampta Pass Crossing (`Booked`). |
| **Trekker 3** | Vikram Singh | `vikram@example.com` | `user123` | Historical completed reservation for Triund Ridge (`Completed`). |
| **Trekker 4** | Ananya Roy | `ananya@example.com` | `user123` | Historical cancelled reservation (`Cancelled`). |
| **Blacklisted**| Rohit Verma | `rohit@example.com` | `user123` | Blacklisted account to demonstrate `403 Forbidden` login rejection. |

---

## 7. How to Trigger Background Jobs for Demo

### 1. Asynchronous User Bookings CSV Export (`export_bookings_csv`)
- **Via Frontend:**
  1. Log in as any trekker (`aarav@example.com` / `user123`).
  2. On the User Dashboard (`/dashboard`), click the **"Export booking history (CSV)"** button.
  3. The UI will show *"Export started..."*, poll the status endpoint, and display a download button when the CSV is generated in `exports/`.
- **Via cURL:**
  ```bash
  # Step 1: Request Export (returns 202 Accepted with task_id)
  curl -X POST http://127.0.0.1:5000/api/user/export \
    -H "Authorization: Bearer <USER_TOKEN>"

  # Step 2: Check Status
  curl http://127.0.0.1:5000/api/user/export/<task_id> \
    -H "Authorization: Bearer <USER_TOKEN>"

  # Step 3: Download CSV
  curl -O http://127.0.0.1:5000/api/user/exports/<filename> \
    -H "Authorization: Bearer <USER_TOKEN>"
  ```

### 2. Scheduled Daily Reminders (`daily_reminders`)
- **Automatic:** Fires daily at `08:00 UTC` via Celery Beat crontab.
- **Immediate Admin Trigger:**
  ```bash
  curl -X POST http://127.0.0.1:5000/api/admin/jobs/daily_reminders/run \
    -H "Authorization: Bearer <ADMIN_TOKEN>"
  ```
  *Sends trek itinerary reminders via in-app notification, Google Chat webhook (if `GOOGLE_CHAT_WEBHOOK_URL` is set), SMTP email (default `localhost:1025`), or console logging.*

### 3. Scheduled Monthly Activity Report (`monthly_report`)
- **Automatic:** Fires on the 1st of every month at `00:00 UTC` via Celery Beat.
- **Immediate Admin Trigger:**
  ```bash
  curl -X POST http://127.0.0.1:5000/api/admin/jobs/monthly_report/run \
    -H "Authorization: Bearer <ADMIN_TOKEN>"
  ```
  *Generates an inline-CSS HTML report in `exports/monthly_report_YYYY_MM.html`, emails the admin, and issues an in-app alert.*

---

## 8. Redis Caching Architecture

### Cache Keys and TTLs
| Resource / Endpoint | Cache Key Pattern | TTL | Description |
| :--- | :--- | :--- | :--- |
| **User Catalog** (`GET /api/user/treks`) | `treks:user:q={q}:loc={loc}:diff={diff}:min={min}:max={max}:st={status}:p={p}:pp={pp}` | 180s | Paginated catalog with active filter state |
| **Trek Details** (`GET /api/user/treks/<id>`) | `trek:detail:{trek_id}` | 300s | Full expedition itinerary & slot state |
| **Admin Dashboard** (`GET /api/admin/dashboard`) | `admin:dashboard` | 60s | Aggregate platform stats and status counts |
| **Admin Stats** (`GET /api/admin/stats`) | `admin:stats` | 120s | Chart-ready arrays for popular treks & trends |

### Invalidation Triggers (`invalidate_trek_cache`)
The cache is systematically purged whenever mutations occur:
- **Admin:** Creating, updating, soft-deleting treks, or assigning staff.
- **Staff:** Adjusting capacity slots, toggling Open/Closed status, starting/completing treks.
- **Trekker:** Creating reservations (slots decremented), cancelling bookings (slots restored).

### Measured Latency Evidence (`curl -w`):
```bash
# 1st Call (Cache MISS - executes SQL query & writes to cache):
curl -s -w "\nHTTP: %{http_code} | Total Time: %{time_total}s | X-Cache: MISS\n" \
  -H "Authorization: Bearer <USER_TOKEN>" http://127.0.0.1:5000/api/user/treks

# 2nd Call (Cache HIT - served directly from Redis/memory):
curl -s -w "\nHTTP: %{http_code} | Total Time: %{time_total}s | X-Cache: HIT\n" \
  -H "Authorization: Bearer <USER_TOKEN>" http://127.0.0.1:5000/api/user/treks
```

| Request Attempt | `X-Cache` Header | Response Time | Execution Path |
| :--- | :--- | :--- | :--- |
| **Initial Request (MISS)** | `X-Cache: MISS` | `69.13 ms` | Database Query + Serialization + Cache Write |
| **Cached Request (HIT)** | `X-Cache: HIT` | `27.34 ms` | Direct Cache Retrieval (**2.5x speedup**) |
| **Post-Mutation Request** | `X-Cache: MISS` | `71.20 ms` | Cache purged by mutation; fresh data re-cached |

---

## 9. Comprehensive REST API Reference

### Health & Monitoring
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Public | System status, database connectivity, and timestamp |

### Authentication & Profile (`/api/auth`)
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Registers a trekker. Role forced to `'user'`. Validates email, password $\ge 6$, phone |
| `POST` | `/api/auth/login` | Public | Authenticates admin, staff, or user. Rejects blacklisted/inactive with 403 |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current authenticated profile and roles |
| `PUT` | `/api/auth/me` | Authenticated | Updates profile fields and optional password change |

### Admin Endpoints (`/api/admin`) — `role_required('admin')`
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/dashboard` | Admin | Total treks, users, staff, bookings, breakdown by status |
| `GET` | `/api/admin/treks` | Admin | Searchable, filterable list of all treks |
| `POST` | `/api/admin/treks` | Admin | Creates a trek. Validates dates (`end >= start`), slots, sets `available=total` |
| `GET` | `/api/admin/treks/<id>` | Admin | Detailed trek information |
| `PUT` | `/api/admin/treks/<id>` | Admin | Modifies trek details, dates, difficulty, status |
| `DELETE` | `/api/admin/treks/<id>` | Admin | Soft-deletes trek. Blocks or cancels associated bookings |
| `POST` | `/api/admin/treks/<id>/assign` | Admin | Assigns active staff guide to trek |
| `GET` | `/api/admin/staff` | Admin | Searchable list of staff members with profile metadata |
| `POST` | `/api/admin/staff` | Admin | Creates User with role `'staff'` and associated `StaffProfile` |
| `PUT` | `/api/admin/staff/<id>` | Admin | Updates staff contact, specialization, and status |
| `PATCH` | `/api/admin/staff/<id>/status` | Admin | Sets staff status (`active`, `inactive`, `blacklisted`) |
| `GET` | `/api/admin/users` | Admin | Searchable list of users filterable by status |
| `PATCH` | `/api/admin/users/<id>/status` | Admin | Sets user status (`active`, `inactive`, `blacklisted`). Admin cannot modify self |
| `GET` | `/api/admin/bookings` | Admin | Global ledger of bookings with user/trek details and status filters |
| `GET` | `/api/admin/search` | Admin | Unified global search across `users`, `staff`, and `treks` |
| `GET` | `/api/admin/stats` | Admin | Popular treks ranking and monthly booking time-series |
| `POST` | `/api/admin/jobs/<name>/run` | Admin | On-demand manual trigger for Celery batch jobs (`daily_reminders`, `monthly_report`) |

### Staff Endpoints (`/api/staff`) — `role_required('staff')`
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/staff/dashboard` | Staff | Summary of assigned treks and registered trekker headcount |
| `GET` | `/api/staff/treks` | Staff | Returns exclusively treks assigned to the calling staff guide |
| `PUT` | `/api/staff/treks/<id>/slots` | Staff | Updates total/available slots (cannot reduce total below booked headcount) |
| `PUT` | `/api/staff/treks/<id>/status` | Staff | Toggles trek intake between `Open` and `Closed` only |
| `GET` | `/api/staff/treks/<id>/participants` | Staff | Participant roster (name, phone, emergency contact, booking status) |
| `POST` | `/api/staff/treks/<id>/start` | Staff | Marks trek as started (`is_started = True`) |
| `POST` | `/api/staff/treks/<id>/complete` | Staff | Sets trek to `Completed` and updates all enrolled bookings to `Completed` |

### Trekker / User Endpoints (`/api/user`) — `role_required('user')`
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/user/dashboard` | User | Available treks count, booked treks, active status badges |
| `GET` | `/api/user/treks` | User | Catalog of `Open` & `Approved` treks. Filters: `q`, `location`, `difficulty`, `min_days`, `max_days` |
| `GET` | `/api/user/treks/<id>` | User | Full trek details with real-time remaining slot capacity |
| `POST` | `/api/user/bookings` | User | Transactional reservation: checks Open status, prevents duplicates, checks slots, decrements capacity |
| `POST` | `/api/user/bookings/<id>/pay` | User | Simulates payment gateway; marks reservation as `Paid` |
| `POST` | `/api/user/bookings/<id>/cancel` | User | Cancels reservation; restores slots to trek; creates confirmation alert |
| `GET` | `/api/user/bookings` | User | Active reservations |
| `GET` | `/api/user/history` | User | Historical record of past `Completed` and `Cancelled` reservations |
| `GET` | `/api/user/notifications` | User | Fetches user notifications |
| `POST` | `/api/user/notifications/read` | User | Marks notifications as read |
| `POST` | `/api/user/export` | User | Triggers async Celery CSV export job (returns `202 Accepted`) |
| `GET` | `/api/user/export/<task_id>` | User | Polls export generation progress and status |
| `GET` | `/api/user/exports/<filename>` | User | Secure download of generated CSV (verifies user ownership) |

---

## 10. End-to-End Rubric Verification Checklist

Every specification requirement has been verified via the automated test suite and regression tests:

| Rubric Verification Item | Specification Criteria | Automated Test Suite | Status |
| :--- | :--- | :--- | :--- |
| **1. Single Programmatic Admin** | Exactly one admin (`admin@tma.com` / `admin123`) seeded programmatically in `app.py` & `seed_demo.py`. No admin registration endpoint. | `test_phase1.py`, `test_phase2.py` | **PASS ✔** |
| **2. Role-Based Login** | Unified login for admin, staff, and user. Issues JWT with role claims. Refuses inactive/blacklisted accounts with descriptive 403. | `test_phase2.py` | **PASS ✔** |
| **3. Admin Capabilities** | Full Treks CRUD, staff onboarding/assignment, user blacklist/deactivation, unified search, analytics stats endpoints. | `test_phase3.py` | **PASS ✔** |
| **4. Staff Capabilities & Isolation** | Edit slots (preserving minimum booked), toggle Open/Closed, participant manifest, start/complete expedition. Assigned-only isolation (403 on unassigned treks). | `test_phase4.py` | **PASS ✔** |
| **5. User / Trekker Capabilities** | Self-registration (role forced to `user`), search/filter catalog, booking, cancellation with slot restore, history, and profile updates. | `test_phase5.py` | **PASS ✔** |
| **6. No Overbooking** | Enforced inside DB transaction. Decrements slots, rejects when `available_slots < count` with 409 Conflict ("Fully booked"). Capacity never negative. | `test_phase5.py` | **PASS ✔** |
| **7. Open-Only Booking** | Enforced on backend (400 Bad Request if trek not `Open`) and on frontend (book button disabled). | `test_phase5.py`, `test_phase10.py` | **PASS ✔** |
| **8. No Duplicate Booking** | Rejects booking if user already holds an active reservation for that trek with 409 Conflict. | `test_phase5.py` | **PASS ✔** |
| **9. Redis Cache with TTL** | `cache.py` with 60–300s TTLs on catalog, detail, and admin stats. Mutations trigger `invalidate_trek_cache()`. `X-Cache: HIT/MISS` headers. Graceful fallback. | `test_phase6.py` | **PASS ✔** |
| **10. Daily Reminder Job** | Daily Celery Beat crontab (08:00 UTC). Queries bookings starting within N days. Dispatches via Google Chat webhook, SMTP email, or console fallback. | `test_phase7.py` | **PASS ✔** |
| **11. Monthly HTML Report Job** | 1st of month Celery Beat crontab. Builds inline-CSS HTML report of previous month's completed treks and top rankings. Emails admin and saves to `exports/`. | `test_phase7.py` | **PASS ✔** |
| **12. CSV Export Job with Alert** | Async Celery export task with exact required schema. Creates in-app Notification with download link. Secure download route with user ownership checks. | `test_phase7.py`, `test_phase10.py` | **PASS ✔** |
| **13. Responsive Frontend UI** | Vue 3 SPA via CDN, Vue Router with role route guards, Bootstrap 5 responsive grid & mobile navbar. HTML5 form validations on all forms. | `test_phase8.py`, `test_phase9.py`, `test_phase10.py` | **PASS ✔** |
| **14. Chart.js Visualizations** | Admin dashboard features dynamic Bar Chart (top popular treks) and Line Chart (monthly booking volume trends) powered by CDN Chart.js. | `test_phase8.py` | **PASS ✔** |

---

## 11. Codebase Cleanliness & Final Notes

- All unused files and experimental scripts have been purged.
- No packages outside the allowed library specification exist in `requirements.txt`.
- SQLite database `tma.db` is strictly initialized and populated programmatically.
- Both client-side route guards (Vue Router `beforeEach`) and backend decorators (`login_required`, `role_required`) provide defense-in-depth security across all roles.
