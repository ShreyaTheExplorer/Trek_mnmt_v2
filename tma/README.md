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
