# Trekking Management Application (TMA) - MAD-2 Project

A complete Trekking Management Application built according to MAD-2 project constraints.

## Tech Stack
- **Backend:** Flask REST API, Flask-SQLAlchemy, Werkzeug (password hashing), PyJWT (token authentication), Redis-py, Celery.
- **Frontend:** Vue 3 (via CDN), Vue Router (via CDN), Bootstrap 5 (via CDN). Single entry point: `templates/index.html`.
- **Database:** SQLite (`tma.db`) created programmatically with `db.create_all()`.
- **Cache & Asynchronous Jobs:** Redis & Celery with Redis broker/backend.

---

## Running the Application & Tests

### 1. Activate Environment
```powershell
.venv\Scripts\activate
```

### 2. Run Test Suites
```powershell
# Part 1: Models, programmatic seeding, health check
python tma/test_phase1.py

# Part 2: Auth, validations, token generation, profile update, RBAC
python tma/test_phase2.py

# Part 3: Admin API (Treks CRUD, Staff, Assignment, Users, Bookings, Search, Stats)
python tma/test_phase3.py

# Part 4: Staff API (Assigned Treks, Slots, Status Toggle, Manifest, Start/Complete, Isolation)
python tma/test_phase4.py

# Part 5: Trekker API (Catalog, Booking Rules, Overbooking/Duplicate checks, Cancel-Restore, Dashboard, Notifications, Export)
python tma/test_phase5.py

# Part 6: Redis Caching (Keys, TTLs, Invalidation, X-Cache HIT/MISS Headers, Latency Speedup)
python tma/test_phase6.py

# Part 7: Celery Jobs (Async CSV Export, Daily Reminders, Monthly HTML Report, Manual Triggers)
python tma/test_phase7.py
```

### 3. Start the Flask Application
```powershell
python tma/app.py
```
App runs at: `http://127.0.0.1:5000`

---

## Part 6: Redis Caching Architecture & Documentation

### 1. Cache Layer (`cache.py`)
The application encapsulates caching via `redis-py` with graceful degradation. If the Redis server is unreachable or offline, operations fall back seamlessly to database queries while logging a warning.

### 2. Cache Keys and TTLs
| Resource / Endpoint | Cache Key Pattern | TTL (Seconds) | Description |
| :--- | :--- | :--- | :--- |
| **User Trek Catalog** (`GET /api/user/treks`) | `treks:user:q={q}:loc={loc}:diff={diff}:min={min}:max={max}:st={status}:p={page}:pp={per_page}` | `180s` (3 min) | Paginated list of active/open treks with query filters |
| **Single Trek Details** (`GET /api/user/treks/<id>`) | `trek:detail:{trek_id}` | `300s` (5 min) | Full trek metadata and real-time slot information |
| **Admin Dashboard** (`GET /api/admin/dashboard`) | `admin:dashboard` | `60s` (1 min) | High-level summary metrics, breakdown of treks & bookings by status |
| **Admin Analytics** (`GET /api/admin/stats`) | `admin:stats` | `120s` (2 min) | Chart-ready arrays for popular treks, monthly volume, and participation |

### 3. Cache Invalidation Triggers (`invalidate_trek_cache`)
Whenever a mutation occurs, `invalidate_trek_cache(trek_id)` purges cached queries:
- **Admin Actions**: Creating, editing, soft-deleting treks, or assigning staff.
- **Staff Actions**: Modifying slot capacities, toggling `Open`/`Closed` status, starting or completing treks.
- **Trekker Actions**: Creating bookings (slots decremented), cancelling bookings (slots restored), and payment completion.

### 4. `X-Cache` Header
All cached endpoints include the response header:
- `X-Cache: MISS`: The response was queried from SQLite, formatted, and written into the cache.
- `X-Cache: HIT`: The response was served directly from the cache without database roundtrips.

---

## Response Time Evidence (cURL -w)

### Demonstration with `curl -w`:
```bash
# 1st Call (Cache MISS - executes database queries & formats payload):
curl -s -w "\nHTTP: %{http_code} | Total Time: %{time_total}s | X-Cache: MISS\n" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  http://127.0.0.1:5000/api/user/treks

# 2nd Call (Cache HIT - served directly from cache):
curl -s -w "\nHTTP: %{http_code} | Total Time: %{time_total}s | X-Cache: HIT\n" \
  -H "Authorization: Bearer <USER_TOKEN>" \
  http://127.0.0.1:5000/api/user/treks
```

### Measured Latency Evidence:
| Request Attempt | `X-Cache` Header | Response Time | Execution Path |
| :--- | :--- | :--- | :--- |
| **Initial Request (MISS)** | `X-Cache: MISS` | `69.13 ms` | Database Query + Serialization + Cache Write |
| **Cached Request (HIT)** | `X-Cache: HIT` | `27.34 ms` | Direct Cache Retrieval (`2.5x` speedup) |
| **After Trek Booking (Invalidated)** | `X-Cache: MISS` | `71.20 ms` | Cache purged by mutation; fresh data re-cached |

---

## Part 7: Celery Jobs & Batch Processing Architecture

### 1. Celery Architecture & Scheduling (`celery_app.py`, `tasks.py`)
Celery is configured with the Flask application context using Redis as both broker and result backend.
- **Broker:** `redis://localhost:6379/1`
- **Result Backend:** `redis://localhost:6379/2`

### 2. Commands to Start TMA Infrastructure

#### Terminal 1: Redis Server
```powershell
# Start local Redis server
redis-server
```

#### Terminal 2: Celery Worker
```powershell
# Windows requires '-P solo' or 'threads' for Celery pool execution
.venv\Scripts\activate
celery -A celery_app.celery worker -l info -P solo
```

#### Terminal 3: Celery Beat (Periodic Scheduler)
```powershell
# Runs daily reminders and monthly report on cron schedules
.venv\Scripts\activate
celery -A celery_app.celery beat -l info
```

#### Terminal 4: Flask API Application
```powershell
.venv\Scripts\activate
python tma/app.py
```

---

### 3. Asynchronous & Scheduled Tasks

#### Task 1: Asynchronous User Bookings CSV Export (`export_bookings_csv`)
- **Trigger:** `POST /api/user/export` (Returns `202 Accepted` with `task_id`).
- **Processing:** Asynchronously queries the authenticated user's bookings, builds a CSV with exact required columns:
  - `User ID, Trek Name, Location, Booking Status, Booking Date, Trek Start Date, Trek End Date`
- **Storage:** Saved to `exports/bookings_user_<user_id>_<timestamp>.csv`.
- **Completion Alert:** Emits an in-app `Notification`: *"Your export is ready. Download link: /api/user/exports/<filename>"*.
- **Status Check:** `GET /api/user/export/<task_id>` returns task status, result, and download link.
- **Secure Download:** `GET /api/user/exports/<filename>` validates ownership, allowing only the file owner to download (others receive `403 Forbidden`).

#### Task 2: Scheduled Daily Reminders (`daily_reminders`)
- **Schedule:** Daily at `08:00 UTC` (crontab: `0 8 * * *`, configurable via `REMINDER_CRON_HOUR`).
- **Logic:** Identifies `Booked` bookings for treks scheduled to start within the next `N` days (default `2` days, configurable via `REMINDER_DAYS_AHEAD`).
- **Notification Channels:**
  1. **In-App Notification:** Recorded in database with trek instructions and itinerary details.
  2. **Google Chat Webhook:** Dispatched via HTTP POST to `GOOGLE_CHAT_WEBHOOK_URL` if configured.
  3. **SMTP Email:** Dispatched via `smtplib` to `user.email` (configured via `MAIL_SERVER` / `MAIL_PORT`, default `localhost:1025`).
  4. **Fallback:** If an external channel is offline or unconfigured, the message is logged to the console instead of failing.

#### Task 3: Scheduled Monthly Activity Report (`monthly_report`)
- **Schedule:** 1st day of every month at `00:00 UTC` (crontab: `0 0 1 * *`).
- **Logic:** Compiles metrics for the preceding month:
  - Total treks conducted (`Completed` in that month).
  - Unique trekkers participating.
  - Top 5 popular treks ranked by booking and participant counts.
- **Output:** Formats an executive HTML report with responsive inline-CSS styles, saves a permanent archive copy in `exports/monthly_report_YYYY_MM.html`, sends an HTML email to the admin, and issues an in-app admin alert.

---

### 4. Admin Manual Job Execution (`POST /api/admin/jobs/<name>/run`)
Administrators can trigger batch jobs on demand for testing, auditing, or immediate dispatch:
```bash
# Run daily reminders immediately:
curl -X POST http://127.0.0.1:5000/api/admin/jobs/daily_reminders/run \
  -H "Authorization: Bearer <ADMIN_TOKEN>"

# Run monthly activity report immediately:
curl -X POST http://127.0.0.1:5000/api/admin/jobs/monthly_report/run \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```
