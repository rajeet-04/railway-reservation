# Quick Start Guide

## What We've Built

✅ **Complete Railway Database** - 87.5 MB SQLite database containing:
- 8,990 stations (96.7% with GPS coordinates)
- 5,208 trains with full route geometries
- 417,080 scheduled train stops
- 156,240 train runs (30 days ahead)
- Spatial indexing for route search
- **100% successful route-to-station mapping**

## Files Overview

```
railway-reservation/
├── data/                           # Source data (DO NOT MODIFY)
│   ├── stations.json (3 MB)
│   ├── trains.json (33 MB)
│   └── schedules.json (93 MB)
├── database/
│   ├── schema.sql                  # Database schema
│   ├── queries.sql                 # Sample queries
│   └── railway.db (87.5 MB)        # ✅ READY TO USE
├── scripts/
│   ├── import_data.py              # Data importer
│   └── verify_db.py                # Verification tool
├── docs/
│   └── PROJECT_PLAN.md             # Complete roadmap
├── requirements.txt
└── README.md
```

## Using the Database

### 1. Explore with SQLite CLI

```powershell
# Open database
sqlite3 database/railway.db

# Run sample queries
.mode column
.headers on

-- Find stations
SELECT code, name, state FROM stations WHERE name LIKE '%Mumbai%' LIMIT 10;

-- Search trains
SELECT number, name, from_station_name, to_station_name 
FROM trains 
WHERE from_station_code = 'NDLS' 
LIMIT 10;

-- Get train route
SELECT ts.stop_sequence, s.name, ts.arrival_time, ts.departure_time
FROM train_stops ts
JOIN stations s ON ts.station_code = s.code
WHERE ts.train_id = (SELECT id FROM trains WHERE number = '12345')
ORDER BY ts.stop_sequence;
```

### 2. Verify Database

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/verify_db.py
```

### 3. Re-import (if needed)

```powershell
# Delete and recreate
Remove-Item database/railway.db
python scripts/import_data.py
```

## Next Steps

### Option A: Build Backend (Python FastAPI)

```powershell
# Create backend directory
mkdir backend
cd backend

# Install FastAPI
pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib[argon2]

# Create main.py
# (See docs/PROJECT_PLAN.md for structure)

# Run
uvicorn app.main:app --reload
```

### Option B: Build Frontend (Next.js + TypeScript)

```powershell
# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app

cd frontend

# Install dependencies
npm install axios zustand anime.js

# Run dev server
npm run dev
```

### Option C: Explore Data

```python
import sqlite3

conn = sqlite3.connect('database/railway.db')
cursor = conn.cursor()

# Get random train with full route
cursor.execute("""
    SELECT t.number, t.name, COUNT(ts.id) as stops
    FROM trains t
    LEFT JOIN train_stops ts ON t.id = ts.train_id
    GROUP BY t.id
    ORDER BY RANDOM()
    LIMIT 1
""")

train = cursor.fetchone()
print(f"Train {train[0]}: {train[1]} ({train[2]} stops)")
```

## Database Schema Quick Reference

### Main Tables

| Table | Records | Description |
|-------|---------|-------------|
| `stations` | 8,990 | Railway stations with coordinates |
| `trains` | 5,208 | Train metadata (number, name, route) |
| `train_routes` | 5,208 | GeoJSON LineString geometries |
| `train_stops` | 417,080 | Scheduled stops with times |
| `train_runs` | 156,240 | Date-specific train instances |
| `seats` | 0 | Seat inventory (to be populated) |
| `bookings` | 0 | User bookings (to be created) |
| `users` | 0 | User accounts (to be created) |

### Key Indexes

- `idx_stations_code` - Station lookup by code
- `idx_trains_number` - Train lookup by number
- `idx_train_stops_train` - Stops for a train
- `idx_train_stops_station` - Trains at a station
- `idx_train_runs_date` - Train runs by date

## Sample Queries

### Search Autocomplete
```sql
SELECT code, name, state 
FROM stations 
WHERE name LIKE '%' || ? || '%' 
ORDER BY name 
LIMIT 10;
```

### Direct Trains
```sql
SELECT t.number, t.name, t.departure_time, t.arrival_time
FROM trains t
WHERE t.from_station_code = ?
  AND t.to_station_code = ?
ORDER BY t.departure_time;
```

### Train Route
```sql
SELECT ts.stop_sequence, s.code, s.name, 
       ts.arrival_time, ts.departure_time
FROM train_stops ts
JOIN stations s ON ts.station_code = s.code
WHERE ts.train_id = (SELECT id FROM trains WHERE number = ?)
ORDER BY ts.stop_sequence;
```

### Seat Availability
```sql
SELECT seat_number, seat_class, price_cents, status
FROM seats
WHERE train_run_id = (
    SELECT id FROM train_runs 
    WHERE train_id = ? AND run_date = ?
)
AND status = 'AVAILABLE';
```

## Common Tasks

### Add Sample Seats
```sql
-- Insert 100 seats for a train run
INSERT INTO seats (train_run_id, seat_number, seat_class, price_cents, status)
SELECT 
    1 as train_run_id,
    'A' || seq as seat_number,
    'SL' as seat_class,
    50000 as price_cents,
    'AVAILABLE' as status
FROM (
    WITH RECURSIVE cnt(x) AS (
        SELECT 1
        UNION ALL
        SELECT x+1 FROM cnt WHERE x < 100
    )
    SELECT x as seq FROM cnt
);
```

### Create Admin User
```sql
INSERT INTO users (email, password_hash, full_name, is_admin)
VALUES ('admin@railway.com', '$argon2...', 'Admin User', 1);
```

### Booking Transaction
```sql
BEGIN TRANSACTION;

-- Lock seats
UPDATE seats 
SET status = 'BOOKED' 
WHERE id IN (123, 124) 
  AND status = 'AVAILABLE';

-- Create booking
INSERT INTO bookings (booking_id, user_id, train_run_id, ...)
VALUES ('PNR-001', 1, 1, ...);

COMMIT;
```

## Performance Tips

1. **Use Prepared Statements** - Faster & safer
2. **Index Foreign Keys** - Already done in schema
3. **EXPLAIN QUERY PLAN** - Analyze slow queries
4. **WAL Mode** - Already enabled (better concurrency)
5. **Connection Pooling** - Max 20 for desktop app

## Troubleshooting

### Database locked error
```powershell
# Check WAL mode
sqlite3 database/railway.db "PRAGMA journal_mode;"
# Should return: wal

# If not, enable:
sqlite3 database/railway.db "PRAGMA journal_mode=WAL;"
```

### Re-import taking too long
```powershell
# The import takes ~55 seconds
# Progress bars show status
# If stuck, check:
# 1. Enough disk space (need ~500 MB temp)
# 2. No antivirus blocking
# 3. Python 3.10+ installed
```

### Missing coordinates for stations
```powershell
# 293 stations have no coordinates (3.3%)
# This is expected from source data
# Route search will still work (uses hop-count heuristic)

# Check which stations:
sqlite3 database/railway.db "SELECT code, name FROM stations WHERE latitude IS NULL;"
```

## Resources

- **Full Documentation**: `docs/PROJECT_PLAN.md`
- **Database Schema**: `database/schema.sql`
- **Sample Queries**: `database/queries.sql`
- **Verification**: `python scripts/verify_db.py`

## Questions?

Check the database directly:
```powershell
sqlite3 database/railway.db
.tables         # List all tables
.schema trains  # See table structure
.help           # SQLite help
```

---

**Database Status**: ✅ Ready for backend development  
**Next Step**: Start building FastAPI backend or Next.js frontend  
**Estimated Time to MVP**: ~10 weeks
