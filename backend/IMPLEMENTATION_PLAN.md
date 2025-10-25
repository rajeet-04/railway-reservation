# Railway Reservation Backend - Implementation Plan

## Phase 1: Core Infrastructure ✅ COMPLETE

### ✅ Database Layer
- [x] SQLAlchemy async ORM models (11 models)
- [x] Async session management with dependency injection
- [x] Connection pooling configuration (Postgres/SQLite support)
- [x] Schema migration with models

### ✅ Seat Generation Service
- [x] Indian Railways coach layout implementation
- [x] Class-based seat allocation (SL, 3A, 2A, 1A, CC, 2S, GEN)
- [x] Berth type assignment (LB, MB, UB, SL, SU)
- [x] Bulk insert with batching (500 seats/batch)
- [x] Price calculation based on distance and class
- [x] Coach prefix mapping (S=Sleeper, A=3A, B=2A, H=1A, C=CC, D=2S, G=GEN)
- [x] Smoke test validation

### ✅ Application Foundation
- [x] FastAPI app factory with lifespan events
- [x] CORS middleware configuration
- [x] Pydantic settings with environment variables
- [x] Logging configuration
- [x] Health check endpoint

---

## Phase 2: Authentication & Authorization 🔄 IN PROGRESS

### User Management
- [ ] User registration endpoint (`POST /api/v1/auth/register`)
  - Email validation (regex + unique check)
  - Password hashing with argon2 (cost parameters: time=2, memory=102400, parallelism=8)
  - Create user record with is_admin=False default
  - Return success message (no auto-login)

- [ ] User login endpoint (`POST /api/v1/auth/login`)
  - Email/password validation
  - Argon2 password verification
  - Generate JWT access token (HS256, 24h expiry)
  - Return `{ access_token, token_type: "bearer" }`

- [ ] Current user endpoint (`GET /api/v1/users/me`)
  - JWT token validation
  - Return user profile (exclude password_hash)
  - Depends on `get_current_user` dependency

- [ ] Token refresh endpoint (`POST /api/v1/auth/refresh`)
  - Optional: implement refresh token flow
  - Short-lived access token (15min) + long-lived refresh token (7 days)

### Security Utilities
- [ ] `get_password_hash(password: str) -> str`
- [ ] `verify_password(plain: str, hashed: str) -> bool`
- [ ] `create_access_token(data: dict, expires_delta: timedelta) -> str`
- [ ] `get_current_user(token: str = Depends(oauth2_scheme)) -> User`
- [ ] `get_current_admin_user(user: User = Depends(get_current_user)) -> User`

### Pydantic Schemas
```python
# app/schemas/auth.py
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=255)
    phone: Optional[str] = Field(pattern=r'^\+?[1-9]\d{1,14}$')

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool
    created_at: datetime
```

---

## Phase 3: Station & Train APIs 🔄 NEXT

### Station Endpoints

**GET /api/v1/stations**
- Query params: `?query=mum&limit=10`
- Fuzzy search on name and code
- Return stations with coordinates
- Order by relevance (exact match first, then prefix, then contains)
- Use index `idx_stations_name` and `idx_stations_code`

**GET /api/v1/stations/{code}**
- Path param: station code (e.g., NDLS)
- Return full station details
- 404 if not found

### Train Endpoints

**GET /api/v1/trains**
- Query params: `?from=NDLS&to=BCT&limit=20`
- Optional filters: type, has_1a, has_2a, has_3a, has_sl, has_cc
- Join with stations for from/to details
- Return train list with route summary

**GET /api/v1/trains/{number}**
- Path param: train number (e.g., 12345)
- Return full train details
- Include class availability flags

**GET /api/v1/trains/{number}/route**
- Query param: `?date=2025-11-01` (optional, for run-specific info)
- Return all stops with arrival/departure times
- Include day_offset for multi-day journeys
- Order by stop_sequence

**GET /api/v1/trains/{number}/stops**
- Same as /route (alias endpoint)

### Pydantic Schemas
```python
# app/schemas/stations.py
class StationBase(BaseModel):
    code: str
    name: str
    lat: Optional[float]
    lon: Optional[float]

class StationDetail(StationBase):
    zone: Optional[str]
    state: Optional[str]
    address: Optional[str]

# app/schemas/trains.py
class TrainBase(BaseModel):
    number: str
    name: str
    type: Optional[str]

class TrainListItem(TrainBase):
    from_station_code: str
    to_station_code: str
    departure_time: str
    arrival_time: str
    distance_km: float
    duration_minutes: int

class TrainDetail(TrainListItem):
    zone: Optional[str]
    has_1a: bool
    has_2a: bool
    has_3a: bool
    has_sl: bool
    has_cc: bool
    has_2s: bool
    has_gen: bool

class TrainStop(BaseModel):
    station_code: str
    station_name: str
    arrival_time: Optional[str]
    departure_time: Optional[str]
    stop_sequence: int
    day_offset: int
    distance_km: Optional[float]
    platform: Optional[str]
```

---

## Phase 4: Route Search (A* Algorithm) 🔄 CRITICAL

### Design

**Endpoint**: `GET /api/v1/search`

**Query Params**:
- `from`: station code (required)
- `to`: station code (required)
- `date`: journey date YYYY-MM-DD (required)
- `time`: departure time HH:MM (optional, default: 00:00)
- `max_transfers`: int (default: 2, max: 3)
- `preference`: "fastest" | "cheapest" | "least_transfers" (default: "fastest")
- `class`: seat class filter (optional)

**Response**:
```json
{
  "from": "NDLS",
  "to": "BCT",
  "date": "2025-11-01",
  "itineraries": [
    {
      "total_duration_minutes": 960,
      "total_distance_km": 1384,
      "transfer_count": 0,
      "estimated_fare": 145000,
      "segments": [
        {
          "train_number": "12951",
          "train_name": "Mumbai Rajdhani",
          "from_station": "NDLS",
          "to_station": "BCT",
          "departure_time": "16:55",
          "arrival_time": "08:35",
          "duration_minutes": 960,
          "distance_km": 1384,
          "day_offset": 1,
          "available_classes": ["1A", "2A", "3A"],
          "seats_available": true
        }
      ]
    }
  ]
}
```

### A* Implementation

**Data Structures**:
```python
@dataclass
class SearchState:
    station_id: int
    time_minutes: int  # Minutes since midnight of journey date
    current_train_id: Optional[int]
    path: List[Segment]
    g_cost: int  # Actual time elapsed (minutes)
    h_cost: int  # Heuristic (haversine distance / 80 km/h)
    
    def f_cost(self) -> int:
        return self.g_cost + self.h_cost

@dataclass
class Segment:
    train_id: int
    train_number: str
    from_station_id: int
    to_station_id: int
    departure_time: int  # Minutes
    arrival_time: int  # Minutes
    day_offset: int
```

**Algorithm**:
1. Load start/goal station coordinates for heuristic
2. Initialize priority queue with start state (g=0, h=haversine estimate)
3. Build adjacency map from train_stops (precompute or query on-demand)
4. Expand states:
   - If on train: next stop on same train (no transfer penalty)
   - If at station: all trains departing after current time (+30min transfer if transferring)
5. Track visited states: (station_id, time_window, train_id)
6. Goal test: station_id == goal_id
7. Return top K paths (K=5)

**Optimizations**:
- Preload train_stops adjacency at startup (cache in memory or Redis)
- Use time windows (round to 30-min buckets) to reduce state space
- Limit search depth (max 12 hours travel time)
- Prune dominated paths (longer time + more transfers)

**Heuristic Function**:
```python
def haversine_heuristic(current_station: Station, goal_station: Station) -> int:
    """Return estimated minutes remaining."""
    distance_km = haversine_distance(
        current_station.lat, current_station.lon,
        goal_station.lat, goal_station.lon
    )
    avg_speed_kmh = 80  # Conservative estimate
    return int((distance_km / avg_speed_kmh) * 60)
```

**Transfer Penalty**: 30 minutes minimum connection time

**Service Class**:
```python
# app/services/routing.py
class RouteSearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.adjacency_cache: Dict[int, List[Edge]] = {}
    
    async def search_routes(
        self,
        from_code: str,
        to_code: str,
        date: date,
        time: Optional[str] = None,
        max_transfers: int = 2,
        preference: str = "fastest",
    ) -> List[Itinerary]:
        """A* route search with time-dependent edges."""
        # Implementation here
```

---

## Phase 5: Seat Availability & Booking 🔄 HIGH PRIORITY

### Seat Availability Endpoints

**GET /api/v1/train_runs/{run_id}/availability**
- Query params: `?class=SL,3A`
- Return seat counts per class:
  ```json
  {
    "train_run_id": 123,
    "train_number": "12345",
    "run_date": "2025-11-01",
    "classes": [
      {"class": "SL", "total": 144, "available": 120, "price": 50000},
      {"class": "3A", "total": 64, "available": 50, "price": 125000}
    ]
  }
  ```

**GET /api/v1/train_runs/{run_id}/seats**
- Query params: `?class=SL&status=AVAILABLE&limit=50&offset=0`
- Pagination support
- Return seat list with coach, seat_number, berth_type, status, price

### Booking Endpoints

**POST /api/v1/bookings**
- Request body:
  ```json
  {
    "train_run_id": 123,
    "from_station_id": 1,
    "to_station_id": 50,
    "seat_class": "SL",
    "seat_count": 2,
    "seat_ids": [101, 102],  // Optional: specific seats or auto-assign
    "passengers": [
      {"name": "John Doe", "age": 30, "gender": "M"},
      {"name": "Jane Doe", "age": 28, "gender": "F"}
    ],
    "contact_email": "user@example.com",
    "contact_phone": "+911234567890"
  }
  ```
- Response:
  ```json
  {
    "booking_id": "PNR1234567890",
    "status": "CONFIRMED",
    "total_fare": 100000,
    "seats": [
      {"seat_number": "S1-1", "coach": "S1", "berth_type": "LB", "passenger_name": "John Doe"},
      {"seat_number": "S1-2", "coach": "S1", "berth_type": "UB", "passenger_name": "Jane Doe"}
    ],
    "journey_date": "2025-11-01",
    "from_station": "NDLS",
    "to_station": "BCT"
  }
  ```

**GET /api/v1/bookings/{booking_id}**
- Return full booking details
- Include seat assignments and passenger info
- Verify user owns booking (unless admin)

**DELETE /api/v1/bookings/{booking_id}**
- Cancel booking (set status=CANCELLED)
- Release seats (set status=AVAILABLE, booking_id=NULL)
- Update train_run.available_seats
- Transactional (BEGIN; UPDATE seats; UPDATE bookings; UPDATE train_runs; COMMIT)
- Only owner or admin can cancel

**GET /api/v1/bookings**
- Query params: `?user_id=current&status=CONFIRMED&limit=10`
- List user's bookings
- Filter by status (CONFIRMED, CANCELLED, PENDING)
- Order by created_at DESC

### Booking Transaction Logic (Postgres)

```python
async def create_booking(
    session: AsyncSession,
    train_run_id: int,
    seat_class: str,
    seat_count: int,
    seat_ids: Optional[List[int]],
    passengers: List[PassengerInfo],
    user_id: Optional[int],
) -> Booking:
    """Atomically book seats using Postgres row-level locking."""
    
    async with session.begin():
        # Step 1: Lock and select seats
        if seat_ids:
            # User specified seats
            query = (
                select(Seat)
                .where(
                    Seat.id.in_(seat_ids),
                    Seat.train_run_id == train_run_id,
                    Seat.status == 'AVAILABLE'
                )
                .with_for_update(skip_locked=True)  # Skip locked rows
            )
        else:
            # Auto-assign best available
            query = (
                select(Seat)
                .where(
                    Seat.train_run_id == train_run_id,
                    Seat.seat_class == seat_class,
                    Seat.status == 'AVAILABLE'
                )
                .limit(seat_count)
                .with_for_update(skip_locked=True)
            )
        
        result = await session.execute(query)
        seats = result.scalars().all()
        
        if len(seats) != seat_count:
            raise HTTPException(409, "Requested seats not available")
        
        # Step 2: Create booking record
        booking_id_str = generate_pnr()
        total_fare = sum(seat.price for seat in seats)
        
        booking = Booking(
            booking_id=booking_id_str,
            user_id=user_id,
            train_run_id=train_run_id,
            from_station_id=from_station_id,
            to_station_id=to_station_id,
            booking_date=date.today(),
            journey_date=journey_date,
            passenger_count=len(passengers),
            total_fare=total_fare,
            status='CONFIRMED',
            payment_status='PENDING',
            passenger_details=json.dumps([p.dict() for p in passengers]),
            contact_email=contact_email,
            contact_phone=contact_phone,
        )
        session.add(booking)
        await session.flush()
        
        # Step 3: Update seats and create booking_seats
        for i, seat in enumerate(seats):
            seat.status = 'BOOKED'
            
            booking_seat = BookingSeat(
                booking_id=booking.id,
                seat_id=seat.id,
                passenger_name=passengers[i].name,
                passenger_age=passengers[i].age,
                passenger_gender=passengers[i].gender,
            )
            session.add(booking_seat)
        
        # Step 4: Update train_run available_seats
        train_run = await session.get(TrainRun, train_run_id)
        train_run.available_seats -= seat_count
        
        # Commit happens automatically on context exit
    
    return booking
```

---

## Phase 6: Admin Endpoints 🔄 MEDIUM PRIORITY

### Train Management
- `POST /api/v1/admin/trains` - Create train
- `PUT /api/v1/admin/trains/{number}` - Update train
- `DELETE /api/v1/admin/trains/{number}` - Delete train (cascade to stops/runs)

### Seat Generation
- `POST /api/v1/admin/seed-seats` - Generate seats for N days
  - Body: `{ "days": 20, "train_ids": [1, 2, 3] }`
  - Returns stats: runs_processed, seats_created

### Analytics
- `GET /api/v1/admin/stats` - Dashboard statistics
  - Total bookings, revenue, occupancy rate
  - Popular routes, peak times
  - User growth metrics

### Reports
- `GET /api/v1/admin/bookings?from_date=&to_date=&export=csv`
- `GET /api/v1/admin/revenue?group_by=train|class|date`

---

## Phase 7: Background Jobs & Caching 🔄 OPTIMIZATION

### Background Jobs (RQ + Redis)

**Job 1: Seat Generation Cron**
- Schedule: Daily at 2 AM
- Task: Generate seats for D+30 train runs
- Delete seats for past runs (D-7)

**Job 2: Booking Cleanup**
- Schedule: Every 15 minutes
- Task: Cancel PENDING bookings older than 30 minutes
- Release held seats

**Job 3: Analytics Aggregation**
- Schedule: Hourly
- Task: Compute occupancy stats, revenue summaries
- Store in Redis or separate analytics table

### Caching Strategy (Redis)

**Cache 1: Station Autocomplete**
- Key: `autocomplete:{query}`
- TTL: 5 minutes
- Invalidate: On station data update

**Cache 2: Route Search Results**
- Key: `route:{from}:{to}:{date}:{time}`
- TTL: 30 minutes
- Invalidate: On schedule changes (rare)

**Cache 3: Seat Availability Summary**
- Key: `avail:{train_run_id}`
- TTL: 2 minutes
- Invalidate: On booking/cancellation

**Cache 4: Train Details**
- Key: `train:{number}`
- TTL: 1 hour
- Invalidate: On train data update

---

## Phase 8: Testing 🔄 CONTINUOUS

### Unit Tests
- `tests/test_auth.py` - Password hashing, JWT creation/validation
- `tests/test_seatgen.py` - Seat generation logic ✅
- `tests/test_routing.py` - A* algorithm, heuristics
- `tests/test_bookings.py` - Atomic booking transactions

### Integration Tests
- `tests/integration/test_api.py` - Full API flow tests
  - Register → Login → Search → Book → Cancel
- Use TestClient (httpx) with test database
- Fixture: `@pytest.fixture async def test_session()`

### Load Tests (Locust or k6)
- Concurrent booking requests (100 users)
- Route search under load (200 req/s)
- Verify no double-bookings under race conditions

---

## Phase 9: Deployment 🔄 FINAL

### Local Development
```powershell
# Start Postgres + Redis
docker-compose up -d

# Run migrations
alembic upgrade head

# Seed seats
python scripts/seed_seats.py

# Start server
uvicorn app.main:app --reload
```

### Production (Render + Supabase)

**Supabase Setup**:
1. Create Postgres database
2. Copy connection string (pooled mode)
3. Run migrations via Render deploy hook

**Render Setup**:
1. Create Web Service (Python runtime)
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Environment variables:
   - DATABASE_URL (Supabase pooled URL)
   - SECRET_KEY (generate: `openssl rand -hex 32`)
   - REDIS_URL (Upstash or Render Redis)
5. Health check path: `/health`

**Redis Setup** (Upstash):
1. Create database
2. Copy REDIS_URL
3. Configure in Render

---

## File Checklist

### ✅ Created
- [x] backend/requirements.txt
- [x] backend/.env.example
- [x] backend/app/__init__.py
- [x] backend/app/config.py
- [x] backend/app/main.py
- [x] backend/app/db/__init__.py
- [x] backend/app/db/session.py
- [x] backend/app/db/models.py
- [x] backend/app/services/__init__.py
- [x] backend/app/services/seatgen.py
- [x] backend/scripts/smoke_test_seatgen.py
- [x] backend/README.md

### 🔄 To Create
- [ ] backend/app/schemas/ (Pydantic models)
  - [ ] auth.py
  - [ ] stations.py
  - [ ] trains.py
  - [ ] bookings.py
- [ ] backend/app/api/v1/ (Route handlers)
  - [ ] auth.py
  - [ ] stations.py
  - [ ] trains.py
  - [ ] search.py
  - [ ] bookings.py
  - [ ] admin.py
- [ ] backend/app/services/
  - [ ] routing.py (A* algorithm)
  - [ ] booking_service.py
  - [ ] auth_service.py
- [ ] backend/app/utils/
  - [ ] security.py (JWT, password hashing)
  - [ ] validators.py
- [ ] backend/alembic/ (Migrations)
  - [ ] env.py
  - [ ] versions/001_initial.py
- [ ] backend/tests/
  - [ ] test_auth.py
  - [ ] test_seatgen.py ✅ (smoke test exists)
  - [ ] test_routing.py
  - [ ] test_bookings.py
  - [ ] integration/test_api.py
- [ ] backend/scripts/
  - [ ] seed_seats.py (bulk seat generation for existing DB)
  - [ ] migrate_from_sqlite.py
- [ ] backend/docker-compose.yml
- [ ] backend/Dockerfile

---

## Next Immediate Steps

### Step 1: Generate Seats for Existing Database
Create `scripts/seed_seats.py` to populate seats for existing 156k train runs:

```python
# Run: python scripts/seed_seats.py --days 20
async def main():
    engine = create_async_engine(DATABASE_URL)
    async with async_sessionmaker(engine)() as session:
        stats = await generate_seats_for_runs(session, days=20)
        print(f"Generated {stats['seats_created']} seats for {stats['runs_processed']} runs")
```

### Step 2: Implement Authentication (2-3 hours)
- Create schemas (UserRegister, UserLogin, Token, UserResponse)
- Implement security utils (hash/verify password, create/decode JWT)
- Create auth router with register/login endpoints
- Add get_current_user dependency
- Test with httpx client

### Step 3: Implement Station/Train APIs (2-3 hours)
- Create schemas (StationBase, TrainDetail, TrainStop)
- Implement CRUD functions in app/db/crud.py
- Create routers with endpoints
- Add pagination support
- Test autocomplete performance

### Step 4: Implement Route Search (6-8 hours)
- Design and implement A* algorithm
- Preload train_stops adjacency graph
- Implement heuristic function
- Create search endpoint
- Performance test (target: <500ms for simple routes)

### Step 5: Implement Bookings (4-6 hours)
- Create booking schemas
- Implement atomic booking transaction
- Add availability check endpoint
- Test concurrent bookings
- Verify no double-booking possible

---

## Performance Targets

- **Seat Generation**: 156k runs in <10 minutes (batch_size=500)
- **Station Autocomplete**: <50ms response
- **Route Search**: <500ms for direct trains, <2s for 2-transfer routes
- **Booking Transaction**: <200ms
- **Concurrent Bookings**: 100 req/s without errors

---

## Success Criteria

- ✅ Smoke test passes for seat generation
- ⬜ All unit tests pass (>90% coverage)
- ⬜ Integration test: full booking flow works
- ⬜ Load test: 100 concurrent bookings, zero double-bookings
- ⬜ Production deployment succeeds (Render + Supabase)
- ⬜ Frontend can consume all APIs

---

**Status**: Phase 1 Complete ✅  
**Next**: Phase 2 (Auth) + Seat Generation Script  
**ETA to MVP**: 3-4 weeks with dedicated development
