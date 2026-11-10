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

# Part 5: Trekker/User API (Catalog, Booking Rules, Overbooking/Duplicate checks, Cancel-Restore, Dashboard, Notifications, Export)
python tma/test_phase5.py
```

### 3. Start the Flask Application
```powershell
python tma/app.py
```
App runs at: `http://127.0.0.1:5000`

---

## Part 5: Trekker / User API cURL Reference

All user routes require `Authorization: Bearer <USER_TOKEN>`.

### 1. Browse Treks Catalog (Paginated with Filters)
```bash
curl -X GET "http://127.0.0.1:5000/api/user/treks?q=Valley&difficulty=Moderate&min_days=3&page=1&per_page=10" \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 2. Get Single Trek Details
```bash
curl -X GET http://127.0.0.1:5000/api/user/treks/1 \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 3. Book a Trek (Enforces Business Rules Inside DB Transaction)
1. Trek status must be `Open` (else `400`).
2. No duplicate active booking for same user and trek (else `409`).
3. Available slots must be >= participants (else `409 "Fully booked"`).
4. Decrements `available_slots` and creates booking with status `Booked`.
5. Creates confirmation notification.
```bash
curl -X POST http://127.0.0.1:5000/api/user/bookings \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"trek_id": 1, "participants_count": 2}'
```

### 4. Simulate Payment
Sets `payment_status = 'Paid'`.
```bash
curl -X POST http://127.0.0.1:5000/api/user/bookings/1/pay \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 5. Cancel Booking & Restore Slots
Only owner can cancel; restores slots back to the trek and creates a notification.
```bash
curl -X POST http://127.0.0.1:5000/api/user/bookings/1/cancel \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 6. View My Bookings & History
- Active/current bookings:
```bash
curl -X GET http://127.0.0.1:5000/api/user/bookings \
  -H "Authorization: Bearer <USER_TOKEN>"
```
- Historical past/completed/cancelled bookings:
```bash
curl -X GET http://127.0.0.1:5000/api/user/history \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 7. User Dashboard
Available treks count, booked treks, and status counts.
```bash
curl -X GET http://127.0.0.1:5000/api/user/dashboard \
  -H "Authorization: Bearer <USER_TOKEN>"
```

### 8. Notifications & Mark as Read
- Fetch notifications:
```bash
curl -X GET http://127.0.0.1:5000/api/user/notifications \
  -H "Authorization: Bearer <USER_TOKEN>"
```
- Mark all as read:
```bash
curl -X POST http://127.0.0.1:5000/api/user/notifications/read \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 9. CSV Export Trigger & Download
- Trigger CSV export job (returns `202 Accepted`):
```bash
curl -X POST http://127.0.0.1:5000/api/user/export \
  -H "Authorization: Bearer <USER_TOKEN>"
```
- Download exported file (restricted to file owner):
```bash
curl -X GET "http://127.0.0.1:5000/api/user/exports/<filename>" \
  -H "Authorization: Bearer <USER_TOKEN>"
```
