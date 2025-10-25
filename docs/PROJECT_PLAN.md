# Railway Reservation System - Complete Project Plan

## ✅ COMPLETED: Database Implementation

### Database Statistics (As of Import)
- **Total Stations**: 8,990 (96.7% with GPS coordinates)
- **Total Trains**: 5,208 (all with routes and schedules)
- **Train Stops**: 417,080 scheduled stops
- **Average Stops/Train**: 80.1
- **Train Runs**: 156,240 (5,208 trains × 30 days)
- **Database Size**: 87.5 MB
- **Mapping Success**: 100% (all route coordinates mapped)
- **Import Time**: 55 seconds

### Files Created
```
✅ database/schema.sql       - Complete SQLite schema (15 tables, 24 indexes)
✅ database/queries.sql      - Sample queries for backend APIs
✅ database/railway.db       - Populated database (87.5 MB)
✅ scripts/import_data.py    - Data import with spatial matching
✅ scripts/verify_db.py      - Database verification & diagnostics
✅ requirements.txt          - Python dependencies
✅ README.md                 - Project documentation
```

---

## 🚧 NEXT PHASE: Backend API Development

### Technology Stack
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens + argon2 password hashing
- **Validation**: Pydantic v2 models
- **CORS**: FastAPI middleware
- **Sessions**: Server-side with SQLite store

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Settings & environment
│   ├── database.py             # DB connection & session
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── station.py
│   │   ├── train.py
│   │   ├── booking.py
│   │   └── user.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── station.py
│   │   ├── train.py
│   │   ├── booking.py
│   │   └── user.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── auth.py             # Login, register, logout
│   │   ├── stations.py         # Station search & details
│   │   ├── trains.py           # Train search & details
│   │   ├── search.py           # Route search (A*)
│   │   ├── bookings.py         # Create, list, cancel bookings
│   │   └── admin.py            # Admin operations
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Password hashing, JWT
│   │   ├── route_search.py     # A* algorithm implementation
│   │   ├── booking_service.py  # Seat allocation, transactions
│   │   └── seat_service.py     # Seat availability
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   └── auth.py             # JWT verification
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── haversine.py        # Distance calculations
│       └── pnr_generator.py    # Booking ID generation
├── tests/
│   ├── test_auth.py
│   ├── test_search.py
│   └── test_booking.py
├── requirements.txt
└── .env.example
```

### Core API Endpoints

#### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

#### Stations
```
GET    /api/v1/stations              # List/search stations
GET    /api/v1/stations/{code}       # Station details
GET    /api/v1/stations/autocomplete # Autocomplete search
```

#### Trains
```
GET    /api/v1/trains                # List trains
GET    /api/v1/trains/{number}       # Train details
GET    /api/v1/trains/{number}/route # Full route with stops
GET    /api/v1/trains/{number}/seats # Seat availability for date
```

#### Search & Routing
```
GET    /api/v1/search?from=NDLS&to=BCT&date=2025-11-01
       # Returns: Direct and connecting trains with:
       # - Journey duration
       # - Departure/arrival times
       # - Seat availability
       # - Fare estimates
```

#### Bookings
```
POST   /api/v1/bookings              # Create booking
GET    /api/v1/bookings              # User's bookings
GET    /api/v1/bookings/{id}         # Booking details
POST   /api/v1/bookings/{id}/cancel  # Cancel booking
```

#### Admin (Authenticated, admin role only)
```
POST   /api/v1/admin/trains          # Add train
PUT    /api/v1/admin/trains/{id}     # Update train
DELETE /api/v1/admin/trains/{id}     # Remove train
GET    /api/v1/admin/bookings        # All bookings
GET    /api/v1/admin/analytics       # Revenue, occupancy stats
```

### Route Search Algorithm (A*)

```python
# Pseudocode for multi-hop train search
def search_routes(from_station, to_station, date, max_transfers=2):
    """
    A* search for optimal train routes
    
    Returns:
        List of itineraries sorted by total duration
    """
    
    # Priority queue: (f_score, current_state)
    # State: (station, arrival_time, path, transfers)
    
    open_set = [(0, (from_station, date_start_time, [], 0))]
    closed_set = set()
    
    while open_set:
        f_score, (station, time, path, transfers) = heappop(open_set)
        
        if station == to_station:
            yield path  # Found a route
            continue
        
        if (station, time) in closed_set or transfers > max_transfers:
            continue
        
        closed_set.add((station, time))
        
        # Get outbound trains from current station after arrival time
        trains = get_trains_from_station(station, after_time=time)
        
        for train in trains:
            next_stops = train.get_stops_after(station)
            
            for stop in next_stops:
                # Calculate costs
                g_score = time_to_minutes(stop.arrival_time - date_start_time)
                h_score = haversine_heuristic(stop.station, to_station) / 80 * 60
                f_score = g_score + h_score
                
                # Check transfer penalty
                if path and path[-1].train_number != train.number:
                    g_score += TRANSFER_PENALTY  # e.g., 30 minutes
                    new_transfers = transfers + 1
                else:
                    new_transfers = transfers
                
                new_path = path + [TrainSegment(
                    train=train,
                    from_station=station,
                    to_station=stop.station,
                    departure=train.departure_at(station),
                    arrival=stop.arrival_time
                )]
                
                heappush(open_set, (
                    f_score,
                    (stop.station, stop.arrival_time, new_path, new_transfers)
                ))
```

### Seat Booking Transaction

```python
@router.post("/bookings")
async def create_booking(
    booking_request: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new booking with transactional seat locking
    """
    
    try:
        db.begin()
        
        # 1. Check seat availability
        seats = db.query(Seat).filter(
            Seat.train_run_id == booking_request.train_run_id,
            Seat.seat_number.in_(booking_request.seat_numbers),
            Seat.status == "AVAILABLE"
        ).with_for_update().all()  # Row-level lock
        
        if len(seats) != len(booking_request.seat_numbers):
            raise HTTPException(409, "One or more seats already booked")
        
        # 2. Update seat status
        for seat in seats:
            seat.status = "BOOKED"
        
        # 3. Create booking
        booking = Booking(
            booking_id=generate_pnr(),
            user_id=current_user.id,
            train_run_id=booking_request.train_run_id,
            from_station_code=booking_request.from_station,
            to_station_code=booking_request.to_station,
            journey_date=booking_request.date,
            total_cents=sum(s.price_cents for s in seats),
            num_passengers=len(seats),
            status="CONFIRMED"
        )
        db.add(booking)
        db.flush()
        
        # 4. Link seats to booking
        for seat, passenger in zip(seats, booking_request.passengers):
            booking_seat = BookingSeat(
                booking_id=booking.id,
                seat_id=seat.id,
                passenger_name=passenger.name,
                passenger_age=passenger.age,
                passenger_gender=passenger.gender,
                price_cents=seat.price_cents
            )
            db.add(booking_seat)
        
        db.commit()
        return booking
        
    except Exception as e:
        db.rollback()
        raise
```

---

## 🎨 NEXT PHASE: Frontend Development

### Technology Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: anime.js
- **State**: Zustand or React Context
- **HTTP**: Axios with interceptors
- **Forms**: React Hook Form + Zod validation
- **Theme**: next-themes (dark/light/system)

### Project Structure
```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Home/Search page
│   ├── login/page.tsx
│   ├── register/page.tsx
│   ├── trains/
│   │   └── [number]/page.tsx  # Train details
│   ├── book/
│   │   └── [id]/page.tsx      # Booking flow
│   ├── bookings/
│   │   ├── page.tsx           # Booking history
│   │   └── [id]/page.tsx      # Booking details
│   └── admin/
│       └── (dashboard)/
│           ├── page.tsx        # Admin dashboard
│           └── trains/page.tsx
├── components/
│   ├── ui/                     # Shadcn UI components
│   ├── Header.tsx
│   ├── Footer.tsx
│   ├── ThemeToggle.tsx
│   ├── TrainCard.tsx
│   ├── SeatPicker.tsx
│   ├── BookingSummary.tsx
│   └── SearchForm.tsx
├── lib/
│   ├── api.ts                  # Axios instance & endpoints
│   ├── auth.ts                 # Auth utilities
│   └── utils.ts                # Helper functions
├── hooks/
│   ├── useAuth.ts
│   ├── useSearch.ts
│   └── useBooking.ts
├── contexts/
│   └── AuthContext.tsx
├── styles/
│   └── globals.css
├── public/
│   └── backgrounds/            # SVG backgrounds
├── tailwind.config.ts
├── next.config.js
└── package.json
```

### Key Pages & Flows

#### 1. Home/Search Page
- Large hero section with SVG gradient background
- Search form: From, To, Date, Class
- Station autocomplete with fuzzy search
- Featured trains carousel
- Quick stats (total trains, stations, routes)

#### 2. Search Results
- Filter sidebar (train type, departure time, class)
- Train cards with:
  - Train number & name
  - Departure → Arrival with duration
  - Seat availability badges
  - Price range
  - "View Details" button
- Animate card entry (stagger effect)

#### 3. Train Details
- Header with train info
- Interactive route map (SVG path with station markers)
- Timetable with stop sequence
- Seat class tabs
- Seat picker component (grid layout)
- Book button → booking flow

#### 4. Booking Flow
- Step 1: Seat selection (visual seat map)
- Step 2: Passenger details form
- Step 3: Review & confirm
- Step 4: Success with PNR + download ticket

#### 5. Booking History
- List of user bookings
- Filter: Upcoming, Past, Cancelled
- Each card: Train, route, date, PNR, status
- Quick actions: View details, Cancel, Download

### UI/UX Design System

#### Color Palette
```css
/* Light theme */
--primary: #0B5FFF;        /* Vivid blue */
--secondary: #00C2A8;      /* Teal */
--accent: #FF6B6B;         /* Coral */
--background: #F7FAFF;     /* Light blue-gray */
--surface: #FFFFFF;
--text: #0B2545;           /* Dark blue */
--text-muted: #64748B;

/* Dark theme */
--primary: #3B82F6;
--secondary: #14B8A6;
--accent: #F87171;
--background: #0B1220;     /* Dark blue */
--surface: #1E293B;
--text: #F1F5F9;
--text-muted: #94A3B8;
```

#### Typography
```css
/* Headings */
font-family: 'Roboto Slab', serif;
font-weight: 700;

/* Body */
font-family: 'Inter', sans-serif;
font-weight: 400;

/* Monospace (PNR, train numbers) */
font-family: 'JetBrains Mono', monospace;
```

#### Animation Examples
```javascript
// Train card hover
anime({
  targets: '.train-card',
  scale: 1.02,
  boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
  duration: 200,
  easing: 'easeOutQuad'
});

// Seat selection
anime({
  targets: '.seat.selected',
  scale: [0.8, 1],
  rotate: [0, 360],
  backgroundColor: ['#FFF', '#0B5FFF'],
  duration: 400,
  easing: 'easeOutElastic(1, .6)'
});

// Booking success
anime({
  targets: '.success-icon',
  scale: [0, 1],
  opacity: [0, 1],
  duration: 600,
  easing: 'easeOutBack'
});
```

---

## 📦 DEPLOYMENT: Desktop App with Tauri

### Why Tauri?
- Lightweight (2-5 MB vs 200+ MB Electron)
- Rust-native (security, performance)
- Better suited for Python backend (spawn as subprocess)
- Cross-platform (Windows, macOS, Linux)

### Setup

1. **Package Python Backend**
```bash
pip install pyinstaller
pyinstaller --onefile --name railway-backend backend/app/main.py
```

2. **Initialize Tauri**
```bash
cd frontend
npm install --save-dev @tauri-apps/cli
npm install @tauri-apps/api
npx tauri init
```

3. **Configure Tauri to Launch Backend**
```rust
// src-tauri/src/main.rs
use std::process::Command;

fn main() {
    // Start Python backend
    let _backend = Command::new("./resources/railway-backend.exe")
        .spawn()
        .expect("Failed to start backend");
    
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("Error while running Tauri application");
}
```

4. **Build**
```bash
npm run tauri build
```

Output: Single executable installer for Windows/macOS/Linux

---

## 🧪 TESTING PLAN

### Backend Tests
- **Unit**: Route algorithm, seat allocation logic
- **Integration**: API endpoints with test DB
- **Load**: 1000 concurrent searches, 100 concurrent bookings

### Frontend Tests
- **Unit**: Components with Jest + Testing Library
- **E2E**: Playwright for full booking flow
- **Accessibility**: axe-core for WCAG 2.1 AA

### Test Database
- Use in-memory SQLite for tests
- Seed with 100 stations, 50 trains, 500 stops
- Mock user authentication

---

## 📊 PERFORMANCE TARGETS

### Backend
- Search query: < 200ms (direct trains)
- Search query: < 500ms (1-hop routes)
- Booking creation: < 300ms
- Concurrent bookings: 50 req/sec

### Frontend
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse Score: 90+

### Database
- Query optimization: indexes on all foreign keys
- Prepared statements for frequent queries
- Connection pooling (max 20 connections)

---

## 🗓️ ESTIMATED TIMELINE

### Week 1-2: Backend Core
- FastAPI setup & configuration
- SQLAlchemy models
- Authentication & JWT
- Station & train APIs

### Week 3-4: Search & Booking
- A* route search implementation
- Seat availability service
- Booking transaction logic
- Testing & optimization

### Week 5-6: Frontend Core
- Next.js setup with Tailwind
- Home & search page
- Train details & route display
- Theme system

### Week 7-8: Booking Flow
- Seat picker component
- Booking form & validation
- Payment mock
- Booking confirmation

### Week 9: Admin & Polish
- Admin dashboard
- Analytics
- Animations
- Accessibility

### Week 10: Desktop App
- Tauri setup
- Backend packaging
- Integration testing
- Installer builds

**Total**: ~10 weeks for MVP

---

## 🎯 SUCCESS METRICS

- ✅ Database: 8,990 stations, 5,208 trains, 100% mapping
- 🎯 Backend: All endpoints tested, <200ms avg response
- 🎯 Frontend: Responsive, accessible, <3s load time
- 🎯 Desktop: <50 MB installer, <200 MB RAM usage
- 🎯 UX: Intuitive booking in <5 clicks from search

---

**Status**: Database phase complete ✅  
**Next**: Begin backend API development  
**Estimated MVP**: ~10 weeks from today
