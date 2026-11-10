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
```

### 3. Start the Flask Application
```powershell
python tma/app.py
```
App runs at: `http://127.0.0.1:5000`

---

## Part 4: Staff API cURL Reference

All staff routes require `Authorization: Bearer <STAFF_TOKEN>`.
Staff users can only view and modify treks **assigned to them** (`assigned_staff_id == current_staff_id`). Attempting to access another staff member's trek returns `403 Forbidden`.

### 1. Staff Dashboard
Returns assigned treks and registered-user count per trek.
```bash
curl -X GET http://127.0.0.1:5000/api/staff/dashboard \
  -H "Authorization: Bearer <STAFF_TOKEN>"
```

### 2. List Assigned Treks Only
```bash
curl -X GET http://127.0.0.1:5000/api/staff/treks \
  -H "Authorization: Bearer <STAFF_TOKEN>"
```

### 3. Update Slots for Assigned Trek
Cannot set `total_slots` below the number of booked users; keeps `available_slots` consistent.
```bash
curl -X PUT http://127.0.0.1:5000/api/staff/treks/1/slots \
  -H "Authorization: Bearer <STAFF_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"total_slots": 25}'
```

### 4. Toggle Trek Status (Open/Closed only)
Opening is allowed only if the trek is currently `Approved` or `Closed`.
```bash
curl -X PUT http://127.0.0.1:5000/api/staff/treks/1/status \
  -H "Authorization: Bearer <STAFF_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "Open"}'
```

### 5. Participant Roster / Manifest
Returns list of registered users with name, phone, emergency contact, and booking status.
```bash
curl -X GET http://127.0.0.1:5000/api/staff/treks/1/participants \
  -H "Authorization: Bearer <STAFF_TOKEN>"
```

### 6. Mark Trek as Started
Marks the trek as started (`is_started = True`) and notifies booked participants.
```bash
curl -X POST http://127.0.0.1:5000/api/staff/treks/1/start \
  -H "Authorization: Bearer <STAFF_TOKEN>"
```

### 7. Mark Trek as Completed
Sets the trek to `Completed` and automatically updates all 'Booked' bookings to `Completed`.
```bash
curl -X POST http://127.0.0.1:5000/api/staff/treks/1/complete \
  -H "Authorization: Bearer <STAFF_TOKEN>"
```

### 8. Staff Multi-Tenancy Isolation Verification
Staff A attempting to access Staff B's trek will be rejected with `403 Forbidden`:
```bash
curl -X PUT http://127.0.0.1:5000/api/staff/treks/2/slots \
  -H "Authorization: Bearer <STAFF_A_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"total_slots": 30}'
```
*Expected response (403 Forbidden):*
```json
{
  "data": null,
  "message": "Access forbidden: you are not assigned to this trek.",
  "success": false
}
```
