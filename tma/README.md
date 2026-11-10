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
```

### 3. Start the Flask Application
```powershell
python tma/app.py
```
App runs at: `http://127.0.0.1:5000`

---

## Part 3: Admin API cURL Reference

All admin routes require `Authorization: Bearer <ADMIN_TOKEN>`.

### 1. Dashboard Overview
```bash
curl -X GET http://127.0.0.1:5000/api/admin/dashboard \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 2. Create a Trek (Sets `available_slots = total_slots`)
```bash
curl -X POST http://127.0.0.1:5000/api/admin/treks \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hampta Pass Trek",
    "location": "Manali, Himachal Pradesh",
    "difficulty": "Moderate",
    "duration_days": 5,
    "total_slots": 20,
    "price": 11500.0,
    "start_date": "2026-11-20",
    "end_date": "2026-11-25",
    "description": "Dramatic crossover trek from lush Kullu valley to arid Spiti.",
    "instructions": "Carry windproof jacket and gaiters.",
    "status": "Pending"
  }'
```

### 3. Update Trek / Transition Status (`Pending` → `Approved` → `Open`)
```bash
curl -X PUT http://127.0.0.1:5000/api/admin/treks/1 \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Open",
    "price": 12000.0
  }'
```

### 4. Create Staff (Creates `User` + `StaffProfile`)
```bash
curl -X POST http://127.0.0.1:5000/api/admin/staff \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Karan Negi",
    "email": "karan.guide@tma.com",
    "password": "guidePassword123",
    "phone": "+91 9876543222",
    "contact_details": "Base Camp Channel 3",
    "specialization": "High Altitude Rescue"
  }'
```

### 5. Assign Staff to Trek (Only active staff permitted)
```bash
curl -X POST http://127.0.0.1:5000/api/admin/treks/1/assign \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 2
  }'
```

### 6. Update Staff Status (`PATCH /api/admin/staff/<id>/status`)
```bash
curl -X PATCH http://127.0.0.1:5000/api/admin/staff/2/status \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

### 7. Manage Users & Update Status (`PATCH /api/admin/users/<id>/status`)
```bash
curl -X PATCH http://127.0.0.1:5000/api/admin/users/3/status \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "blacklisted"}'
```

### 8. View All Bookings (Historical with User & Trek info)
```bash
curl -X GET "http://127.0.0.1:5000/api/admin/bookings?status=Booked" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 9. Unified Search
```bash
curl -X GET "http://127.0.0.1:5000/api/admin/search?q=Hampta&type=treks" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 10. Analytics Stats (Chart-Ready Arrays)
```bash
curl -X GET http://127.0.0.1:5000/api/admin/stats \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```
