-- Railway Reservation System Database Schema
-- SQLite 3.x compatible

-- Stations table (from stations.json)
CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    state TEXT,
    zone TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stations_code ON stations(code);
CREATE INDEX IF NOT EXISTS idx_stations_name ON stations(name);
CREATE INDEX IF NOT EXISTS idx_stations_coords ON stations(latitude, longitude) WHERE latitude IS NOT NULL;

-- Trains table (from trains.json properties)
CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    from_station_code TEXT NOT NULL,
    to_station_code TEXT NOT NULL,
    from_station_name TEXT,
    to_station_name TEXT,
    zone TEXT,
    type TEXT,
    distance_km INTEGER,
    duration_h INTEGER,
    duration_m INTEGER,
    departure_time TEXT,
    arrival_time TEXT,
    return_train TEXT,
    -- Seat class availability flags
    first_ac INTEGER DEFAULT 0,
    second_ac INTEGER DEFAULT 0,
    third_ac INTEGER DEFAULT 0,
    sleeper INTEGER DEFAULT 0,
    chair_car INTEGER DEFAULT 0,
    first_class INTEGER DEFAULT 0,
    -- Metadata
    classes TEXT,
    properties_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(from_station_code) REFERENCES stations(code),
    FOREIGN KEY(to_station_code) REFERENCES stations(code)
);

CREATE INDEX IF NOT EXISTS idx_trains_number ON trains(number);
CREATE INDEX IF NOT EXISTS idx_trains_from_to ON trains(from_station_code, to_station_code);

-- Train routes (geometry storage)
CREATE TABLE IF NOT EXISTS train_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    geometry_type TEXT DEFAULT 'LineString',
    coordinates_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(train_id) REFERENCES trains(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_train_routes_train ON train_routes(train_id);

-- Train stops (from schedules.json and mapped routes)
CREATE TABLE IF NOT EXISTS train_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    station_code TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    arrival_time TEXT,
    departure_time TEXT,
    day_offset INTEGER DEFAULT 0,
    distance_from_start_km INTEGER,
    platform TEXT,
    halt_minutes INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(train_id) REFERENCES trains(id) ON DELETE CASCADE,
    FOREIGN KEY(station_code) REFERENCES stations(code),
    UNIQUE(train_id, stop_sequence)
);

CREATE INDEX IF NOT EXISTS idx_train_stops_train ON train_stops(train_id);
CREATE INDEX IF NOT EXISTS idx_train_stops_station ON train_stops(station_code);
CREATE INDEX IF NOT EXISTS idx_train_stops_sequence ON train_stops(train_id, stop_sequence);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    is_admin INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Train runs (date-specific train instances)
CREATE TABLE IF NOT EXISTS train_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    run_date DATE NOT NULL,
    status TEXT DEFAULT 'SCHEDULED',
    total_seats INTEGER DEFAULT 0,
    available_seats INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(train_id) REFERENCES trains(id) ON DELETE CASCADE,
    UNIQUE(train_id, run_date)
);

CREATE INDEX IF NOT EXISTS idx_train_runs_train ON train_runs(train_id);
CREATE INDEX IF NOT EXISTS idx_train_runs_date ON train_runs(run_date);
CREATE INDEX IF NOT EXISTS idx_train_runs_status ON train_runs(status);

-- Seats (per train run)
CREATE TABLE IF NOT EXISTS seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_run_id INTEGER NOT NULL,
    seat_number TEXT NOT NULL,
    coach_number TEXT,
    seat_class TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    status TEXT DEFAULT 'AVAILABLE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(train_run_id) REFERENCES train_runs(id) ON DELETE CASCADE,
    UNIQUE(train_run_id, seat_number)
);

CREATE INDEX IF NOT EXISTS idx_seats_train_run ON seats(train_run_id);
CREATE INDEX IF NOT EXISTS idx_seats_status ON seats(status);
CREATE INDEX IF NOT EXISTS idx_seats_class ON seats(seat_class);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    train_run_id INTEGER NOT NULL,
    from_station_code TEXT NOT NULL,
    to_station_code TEXT NOT NULL,
    journey_date DATE NOT NULL,
    booking_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_cents INTEGER NOT NULL,
    num_passengers INTEGER NOT NULL,
    status TEXT DEFAULT 'CONFIRMED',
    payment_status TEXT DEFAULT 'PENDING',
    cancellation_time DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(train_run_id) REFERENCES train_runs(id),
    FOREIGN KEY(from_station_code) REFERENCES stations(code),
    FOREIGN KEY(to_station_code) REFERENCES stations(code)
);

CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_train_run ON bookings(train_run_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_booking_id ON bookings(booking_id);

-- Booking seats (passengers)
CREATE TABLE IF NOT EXISTS booking_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL,
    passenger_name TEXT NOT NULL,
    passenger_age INTEGER,
    passenger_gender TEXT,
    price_cents INTEGER NOT NULL,
    FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY(seat_id) REFERENCES seats(id),
    UNIQUE(booking_id, seat_id)
);

CREATE INDEX IF NOT EXISTS idx_booking_seats_booking ON booking_seats(booking_id);
CREATE INDEX IF NOT EXISTS idx_booking_seats_seat ON booking_seats(seat_id);

-- Import logs (for diagnostics)
CREATE TABLE IF NOT EXISTS import_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_type TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    details_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_import_logs_type ON import_logs(import_type);

-- Mapping warnings (coordinate -> station mapping issues)
CREATE TABLE IF NOT EXISTS mapping_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_number TEXT,
    coordinate_index INTEGER,
    latitude REAL,
    longitude REAL,
    nearest_station_code TEXT,
    distance_km REAL,
    warning_type TEXT,
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mapping_warnings_train ON mapping_warnings(train_number);
