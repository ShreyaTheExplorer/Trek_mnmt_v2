# Trekking Management Application (TMA) - MAD-2 Project

A complete Trekking Management Application built according to MAD-2 project constraints.

## Tech Stack
- **Backend:** Flask REST API, Flask-SQLAlchemy, Werkzeug (password hashing), PyJWT (token authentication), Redis-py, Celery.
- **Frontend:** Vue 3 (via CDN), Vue Router (via CDN), Bootstrap 5 (via CDN). Single entry point: `templates/index.html`.
- **Database:** SQLite (`tma.db`) created programmatically with `db.create_all()`.
- **Cache & Asynchronous Jobs:** Redis & Celery with Redis broker/backend.

---

## Part 1 Deliverables & Architecture

### 1. Folder Structure
```
tma/
  app.py               # Flask app factory, route registration, programmatic DB & seeder
  config.py            # Environment-aware configuration (tma.db, Redis, Mail, Webhook)
  extensions.py        # SQLAlchemy db and Redis client
  models.py            # User, StaffProfile, Trek, Booking, Notification models
  auth.py              # JWT token generator, unified {success, message, data} response, decorators
  routes/
    auth_routes.py     # Register, Login, Me, Profile, Change Password
    admin_routes.py    # Admin management endpoints
    staff_routes.py    # Staff operations
    user_routes.py     # Trekker browsing and bookings
  cache.py             # Redis caching layer
  celery_app.py        # Celery application
  tasks.py             # Background jobs & CSV export tasks
  templates/
    index.html         # Single Jinja2 entry point (Bootstrap 5 + Vue mount point)
  static/
    css/custom.css     # TMA custom styles
    js/
      app.js
      router.js
      api.js
      components/
  exports/             # Generated CSV exports directory
  requirements.txt     # Python dependencies
  README.md            # Documentation & instructions
```

### 2. Database Models (`tma/models.py`)
- **`User`**: `id`, `name`, `email` (unique), `password_hash`, `phone`, `role` (`'admin' | 'staff' | 'user'`), `status` (`'active' | 'inactive' | 'blacklisted'`), `created_at`, plus profile fields (`age`, `emergency_contact`, `address`).
- **`StaffProfile`**: `id`, `user_id` (FK User, unique), `contact_details`, `specialization`, `status` (`'active' | 'inactive'`), `joined_on`.
- **`Trek`**: `id`, `name`, `location`, `difficulty` (`'Easy' | 'Moderate' | 'Hard'`), `duration_days`, `total_slots`, `available_slots`, `assigned_staff_id` (FK User, nullable), `status` (`'Pending' | 'Approved' | 'Open' | 'Closed' | 'Completed'`), `start_date`, `end_date`, `description`, `instructions`, `price`, `created_at`, `is_deleted` (soft delete flag).
- **`Booking`**: `id`, `user_id`, `trek_id`, `booking_date`, `status` (`'Booked' | 'Cancelled' | 'Completed'`), `payment_status` (`'Pending' | 'Paid' | 'NA'`), `participants_count` (default 1), `cancelled_at`. Contains `Booking.has_active_booking(user_id, trek_id)` check.
- **`Notification`**: `id`, `user_id`, `message`, `created_at`, `is_read`.
- Helper `to_dict()` methods on all models.

### 3. Programmatic Database Creation & Seeding (`tma/app.py`)
- Database tables are created programmatically with `db.create_all()` inside `app.app_context()`.
- Seeds exactly one admin account on startup only if no admin exists:
  - **Email:** `admin@tma.com`
  - **Password:** `admin123`
  - **Role:** `admin`
  - **Status:** `active`

### 4. Endpoints
- `GET /api/health`: Returns API health and database connection status (`200 OK`).
- `GET /`: Serves `templates/index.html` with Bootstrap 5 CDN and Vue 3 mount point (`<div id="app">`).

---

## Instructions to Run

### Step 1: Activate Virtual Environment
```powershell
# From project root:
.venv\Scripts\activate
```

### Step 2: Run Part 1 Self-Test Suite
```powershell
python tma/test_phase1.py
```

### Step 3: Start the Flask Application
```powershell
python tma/app.py
```
Visit:
- Home: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- Health Check: [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)
