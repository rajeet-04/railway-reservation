# Railway Reservation Backend

FastAPI backend for the Railway Reservation System with async PostgreSQL, seat generation, and route search.

## Features

- ✅ Async SQLAlchemy ORM with PostgreSQL/SQLite support
- ✅ Seat generation service with Indian Railways coach layouts
- ✅ JWT authentication with argon2 password hashing
- ✅ Route search with A* algorithm (planned)
- ✅ Atomic booking transactions with row-level locking
- ✅ Redis caching and background jobs
- ✅ Prometheus metrics and health checks

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL (via asyncpg) or SQLite (testing)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Auth**: JWT + argon2
- **Cache**: Redis
- **Testing**: pytest + pytest-asyncio

## Quick Start

### 1. Setup Virtual Environment

```powershell
# Create and activate virtual environment
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy example env file
Copy-Item .env.example .env

# Edit .env with your settings (database URL, secret key, etc.)
```

### 3. Run Smoke Test

```powershell
# Test seat generation service
python scripts\smoke_test_seatgen.py
```

Expected output:
```
============================================================
Seat Generation Smoke Test
============================================================

INFO - Creating in-memory SQLite database...
INFO - ✓ Tables created
INFO - ✓ Test station created
INFO - ✓ Test train created (ID: 1)
INFO - ✓ Train run created for 2025-10-25
INFO - ✓ Confirmed zero seats before generation

Running seat generation...

Generation Stats:
  Runs processed: 1
  Seats created: 15
  Trains processed: 1

Sample Seats:
  S1-1 [SL] LB - AVAILABLE
  S1-2 [SL] MB - AVAILABLE
  S1-3 [SL] UB - AVAILABLE
  S1-4 [SL] LB - AVAILABLE
  S1-5 [SL] MB - AVAILABLE

============================================================
✅ SMOKE TEST PASSED
============================================================
```

### 4. Run Development Server

```powershell
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use Python
python -m app.main
```

Access API docs at: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings (Pydantic)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # Async engine & session
│   │   └── models.py        # SQLAlchemy ORM models
│   ├── services/
│   │   ├── __init__.py
│   │   └── seatgen.py       # Seat generation service
│   └── api/                 # API routes (TODO)
│       └── v1/
│           ├── auth.py
│           ├── stations.py
│           ├── trains.py
│           ├── search.py
│           └── bookings.py
├── scripts/
│   └── smoke_test_seatgen.py
├── requirements.txt
├── .env.example
└── README.md
```

## Database Models

Core models implemented:
- `User` - Authentication and user management
- `Station` - Railway stations with GPS coordinates
- `Train` - Train metadata with class configuration
- `TrainStop` - Scheduled stops with arrival/departure times
- `TrainRun` - Date-specific train instances
- `Seat` - Individual seat inventory with coach splits
- `Booking` - Passenger bookings with PNR
- `BookingSeat` - Booking-to-seat mapping

## Seat Generation

The seat generation service creates realistic seat inventory based on Indian Railways coach layouts:

### Class Configurations

| Class | Code | Seats/Coach | Coach Prefix | Berth Types |
|-------|------|-------------|--------------|-------------|
| Sleeper | SL | 72 | S | LB, MB, UB, SL, SU |
| AC 3-Tier | 3A | 64 | A | LB, MB, UB, SL, SU |
| AC 2-Tier | 2A | 48 | B | LB, UB |
| AC First Class | 1A | 24 | H | LB, UB |
| Chair Car | CC | 78 | C | - |
| Second Sitting | 2S | 108 | D | - |
| General | GEN | 90 | G | - |

### Usage

```python
from app.services.seatgen import generate_seats_for_runs

# Generate seats for next 20 days
stats = await generate_seats_for_runs(session, days=20)

# Generate seats for specific train run
from app.services.seatgen import generate_seats_for_train_run
count = await generate_seats_for_train_run(session, train_run_id=123)
```

## Next Steps

### Immediate Tasks
1. ✅ Database models and migrations (Alembic)
2. ✅ Seat generation service
3. ⬜ Authentication endpoints (register/login/JWT)
4. ⬜ Station search and autocomplete
5. ⬜ Train search and details
6. ⬜ Route search with A* algorithm
7. ⬜ Booking endpoints with transactions
8. ⬜ Admin panel endpoints

### Testing
```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_seatgen.py -v
```

## Deployment

### Using Docker

```dockerfile
# Dockerfile included in project
docker build -t railway-backend .
docker run -p 8000:8000 --env-file .env railway-backend
```

### Render / Supabase

1. Create Postgres database on Supabase
2. Deploy backend to Render (Python service)
3. Set environment variables
4. Run Alembic migrations
5. Configure Redis (Render Redis or Upstash)

## Environment Variables

Required for production:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (generate with openssl)
- `REDIS_URL` - Redis connection string
- `ADMIN_EMAILS` - Comma-separated admin emails
- `CORS_ORIGINS` - Allowed frontend origins

## License

MIT
