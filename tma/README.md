# Trekking Management Application (TMA) - MAD-2 Project

A complete Trekking Management Application built according to MAD-2 project constraints.

## Tech Stack
- **Backend:** Flask REST API, Flask-SQLAlchemy, Werkzeug (password hashing), PyJWT (token authentication), Redis-py, Celery.
- **Frontend:** Vue 3 (via CDN), Vue Router (via CDN), Bootstrap 5 (via CDN). Single entry point: `templates/index.html`.
- **Database:** SQLite (`tma.db`) created programmatically with `db.create_all()`.
- **Cache & Asynchronous Jobs:** Redis & Celery with Redis broker/backend.

---

## Part 1 & Part 2 Deliverables

### Project Structure
```
tma/
  app.py               # Flask app factory, route registration, programmatic DB & seeder
  config.py            # Environment-aware configuration (tma.db, Redis, Mail, Webhook)
  extensions.py        # SQLAlchemy db and Redis client
  models.py            # User, StaffProfile, Trek, Booking, Notification models
  auth.py              # Password hashing, JWT tokens, login_required, role_required
  routes/
    auth_routes.py     # Register, Login, Me (GET & PUT)
    admin_routes.py    # Admin management & dashboard endpoints
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
  exports/             # Generated CSV exports directory
  requirements.txt     # Python dependencies
  test_phase1.py       # Part 1 self-test suite
  test_phase2.py       # Part 2 self-test suite
  README.md            # Documentation & instructions
```

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
```

### 3. Start the Flask Application
```powershell
python tma/app.py
```
App runs at: `http://127.0.0.1:5000`

---

## Part 2: Authentication & RBAC cURL Reference

### 1. Register a New User (Trekkers Only)
> **Rule:** Only `user` accounts can self-register. The `role` field is strictly forced to `'user'`.
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pooja Verma",
    "email": "pooja@example.com",
    "password": "password123",
    "phone": "+91 9876543210",
    "age": 25,
    "emergency_contact": "9876543211",
    "address": "Park Street, Kolkata"
  }'
```

### 2. Login (Works for all three roles)
#### A. User Login:
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pooja@example.com",
    "password": "password123"
  }'
```

#### B. Admin Login:
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tma.com",
    "password": "admin123"
  }'
```

### 3. Get Current User Profile (`GET /api/auth/me`)
```bash
curl -X GET http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 4. Update Profile & Change Password (`PUT /api/auth/me`)
```bash
curl -X PUT http://127.0.0.1:5000/api/auth/me \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pooja V. Sharma",
    "phone": "+91 9876500000",
    "age": 26,
    "current_password": "password123",
    "new_password": "newpassword456"
  }'
```

### 5. Role-Based Access Control (RBAC) Verification
#### A. User token accessing Admin route -> **403 Forbidden**
```bash
curl -X GET http://127.0.0.1:5000/api/admin/dashboard \
  -H "Authorization: Bearer <USER_TOKEN>"
```
*Expected response (403 Forbidden):*
```json
{
  "data": null,
  "message": "Access forbidden: role 'user' is not authorized to access this resource.",
  "success": false
}
```

#### B. Admin token accessing Admin route -> **200 OK**
```bash
curl -X GET http://127.0.0.1:5000/api/admin/dashboard \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```
*Expected response (200 OK):*
```json
{
  "data": {
    "recent_bookings": [],
    "stats": { ... }
  },
  "message": "Admin dashboard statistics retrieved.",
  "success": true
}
```
