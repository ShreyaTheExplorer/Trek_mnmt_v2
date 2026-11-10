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

# Part 8: Frontend Foundation & Admin UI (Vue 3, Vue Router, Bootstrap 5, Chart.js)
python tma/test_phase8.py

# Part 9: Staff UI & Expedition Operations (StaffDashboard, StaffTrekDetail, Manifest, Slot Controls)
python tma/test_phase9.py

# Part 10: Trekker User UI (UserDashboard, TrekBrowse, TrekDetail, MyBookings, Profile, CSV Export)
python tma/test_phase10.py
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

---

## Part 8: Frontend Foundation & Admin UI Architecture

### 1. Technology & Architecture
- **Single Entry Point:** `templates/index.html` is the only Jinja2 template. All UI interactions are rendered via Vue 3 Single Page Application (SPA) components.
- **CDNs Only (Zero Node CLI / Build tools):**
  - **Bootstrap 5 & Icons:** Responsive grid, tables, cards, and modals.
  - **Vue 3:** Reactive composition and Options API components loaded via CDN.
  - **Vue Router 4:** Client-side hash routing with role-based guards.
  - **Chart.js:** Real-time analytics charts.

### 2. Frontend Structure (`static/js/`)
```
static/
  css/custom.css
  js/
    api.js               # Centralized fetch wrapper with Bearer token & 401 handling
    router.js            # Route definitions & beforeEach role-based guards
    app.js               # Vue 3 createApp & mount to #app
    components/
      Toast.js           # Global floating notification alerts
      Navbar.js          # Responsive navigation bar with role badges & notifications
      LoginPage.js       # Unified login for Admin, Staff, and User accounts
      RegisterPage.js    # HTML5-validated user registration form
      AdminView.js       # Top-level administrative navigation container
      AdminDashboard.js  # Stat cards & Chart.js charts (popular treks & monthly trends)
      AdminTreks.js      # Treks table, search, create/edit modal, delete, staff assignment
      AdminStaff.js      # Staff directory, onboarding modal, and status toggles
      AdminUsers.js      # User management, search, and deactivate/blacklist toggles
      AdminBookings.js   # Global booking ledger with status & trek filters
      AdminSearch.js     # Unified search portal querying /api/admin/search
      Placeholders.js    # Base scaffolding for /treks, /staff, and /my-bookings
```

### 3. Route Guard Enforcement
- Public Routes (`/login`, `/register`): Only accessible when logged out; logged-in users are automatically redirected to their role home.
- Protected Routes:
  - `/admin/*`: Restricted to `role='admin'`.
  - `/staff`: Restricted to `role='staff'`.
  - `/my-bookings`: Restricted to `role='user'`.
  - `/profile`: Requires any active authentication.

---

## Part 9: Staff UI & Expedition Operations Architecture

### 1. Staff Components
- **`StaffDashboard.js` (`/staff`)**:
  - Displays summary cards for each assigned trek showing:
    - Registered-user / trekker count (`total_participants`).
    - Status badge (`Pending`, `Approved`, `Open`, `Closed`, `Completed`).
    - Start and end dates, duration in days.
    - Slot availability (`available_slots / total_slots`).
    - Expedition in-progress flag (`is_started`).
  - Direct navigation link to `/staff/treks/:id`.
- **`StaffTrekDetail.js` (`/staff/treks/:id`)**:
  - **Slot Capacities Editor**:
    - Validates that available slots is a non-negative integer (`>= 0`).
    - Enforces that total capacity cannot be decreased below currently booked participants.
  - **Open / Closed Toggle**:
    - Switches intake status between `Open` and `Closed`.
  - **Expedition Lifecycle Controls**:
    - **"Start Trek" Button**: Triggers confirmation dialog; sets `is_started = True`.
    - **"Mark Completed" Button**: Triggers confirmation dialog; sets trek status to `Completed` and automatically updates all enrolled participant bookings to `Completed`.
  - **Participant Manifest Table**:
    - Roster of enrolled trekkers showing Name, Email, Phone, Emergency Contact, and Booking Status.
  - **Friendly Error Handling**:
    - `403 Forbidden`: Displays clear message that staff members are restricted to managing only treks assigned directly to them.
    - `409 Conflict`: Displays contextual conflict explanation.

---

## Part 10: Trekker / User UI Architecture

### 1. User Suite Components (`static/js/components/`)
- **`UserDashboard.js` (`/dashboard` or `/user/dashboard`)**:
  - Displays high-level counters: Available Treks count, Active Booked count, Completed count, and Cancelled count.
  - Active Booked Treks overview with quick navigation to `/my-bookings`.
  - Notifications panel with read/unread tracking and "Mark all read" button.
  - **"Export booking history (CSV)" Button**:
    - Calls `POST /api/user/export`.
    - Shows "Export started" and polls `/api/user/export/<task_id>` every 1.5s.
    - Displays direct download link button upon completion.
- **`TrekBrowse.js` (`/treks`)**:
  - Search box querying keyword `q` across trek names and descriptions.
  - Multi-parameter filters: Difficulty (`Easy`, `Moderate`, `Hard`), Location, and Duration range (`min_days` to `max_days`).
  - Paginated trek cards displaying:
    - Difficulty badge, Location, Duration, and Price per person.
    - Real-time slot tracker (`X slots left` or `Fully Booked`).
    - Open/Closed registration badge.
    - **"Book" Button**: Strictly disabled unless the trek is `Open` and has slots remaining (`available_slots > 0`).
- **`TrekDetail.js` (`/treks/:id`)**:
  - Full expedition metadata, duration, dates, pricing, detailed description, and gear/packing instructions.
  - Interactive participants count input (validated between `1` and `available_slots`).
  - Real-time total amount calculation (`participants * price`).
  - "Book Expedition" button (disabled unless Open and slots available).
  - Confirmed booking card with optional **"Pay (simulated)"** button that calls `POST /api/user/bookings/<id>/pay` and immediately marks the reservation as `Paid`.
- **`MyBookings.js` (`/my-bookings`)**:
  - **Active Reservations Tab**:
    - Reservation cards showing trek title, dates, enrolled headcount, payment badge, and total price.
    - **"Pay Now" Simulator**: Sets payment status to `Paid`.
    - **"Cancel" Button**: Opens modal confirmation dialog; restores slots to the trek, moves status to `Cancelled`, and creates an in-app alert.
  - **Booking History Tab**:
    - Full historical table of past `Completed` and `Cancelled` reservations.
- **`ProfileView.js` (`/profile`)**:
  - HTML5 validated profile form: Name, Phone (regex pattern `^\+?[0-9\s\-]{7,20}$`), Age, Emergency Contact, and Residential Address (`PUT /api/auth/me`).
  - Password change form (requires current password and new password $\ge 6$ characters).



