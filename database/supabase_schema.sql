-- Railway Reservation System - Supabase Schema
-- PostgreSQL/Supabase Version

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stations table
CREATE TABLE IF NOT EXISTS stations (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100),
    zone VARCHAR(50),
    address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trains table
CREATE TABLE IF NOT EXISTS trains (
    id BIGSERIAL PRIMARY KEY,
    number VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    from_station_code VARCHAR(10) NOT NULL,
    to_station_code VARCHAR(10) NOT NULL,
    from_station_name VARCHAR(255),
    to_station_name VARCHAR(255),
    departure_time TIME,
    arrival_time TIME,
    duration_minutes INTEGER,
    distance_km DOUBLE PRECISION,
    has_ac BOOLEAN DEFAULT FALSE,
    has_sleeper BOOLEAN DEFAULT FALSE,
    has_general BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (from_station_code) REFERENCES stations(code) ON DELETE CASCADE,
    FOREIGN KEY (to_station_code) REFERENCES stations(code) ON DELETE CASCADE
);

-- Train routes (GeoJSON geometries)
CREATE TABLE IF NOT EXISTS train_routes (
    id BIGSERIAL PRIMARY KEY,
    train_id BIGINT NOT NULL UNIQUE,
    geometry JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE
);

-- Train stops
CREATE TABLE IF NOT EXISTS train_stops (
    id BIGSERIAL PRIMARY KEY,
    train_id BIGINT NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    stop_sequence INTEGER NOT NULL,
    arrival_time TIME,
    departure_time TIME,
    day_offset INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE,
    FOREIGN KEY (station_code) REFERENCES stations(code) ON DELETE CASCADE,
    UNIQUE (train_id, stop_sequence)
);

-- Train runs (date-specific instances)
CREATE TABLE IF NOT EXISTS train_runs (
    id BIGSERIAL PRIMARY KEY,
    train_id BIGINT NOT NULL,
    run_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (train_id) REFERENCES trains(id) ON DELETE CASCADE,
    UNIQUE (train_id, run_date)
);

-- Seats inventory
CREATE TABLE IF NOT EXISTS seats (
    id BIGSERIAL PRIMARY KEY,
    train_run_id BIGINT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    seat_class VARCHAR(10) NOT NULL,
    price_cents INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'AVAILABLE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (train_run_id) REFERENCES train_runs(id) ON DELETE CASCADE,
    UNIQUE (train_run_id, seat_number)
);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id BIGSERIAL PRIMARY KEY,
    booking_id VARCHAR(20) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    train_run_id BIGINT NOT NULL,
    from_station_code VARCHAR(10) NOT NULL,
    to_station_code VARCHAR(10) NOT NULL,
    journey_date DATE NOT NULL,
    total_cents INTEGER NOT NULL,
    num_passengers INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (train_run_id) REFERENCES train_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (from_station_code) REFERENCES stations(code) ON DELETE CASCADE,
    FOREIGN KEY (to_station_code) REFERENCES stations(code) ON DELETE CASCADE
);

-- Booking seats (passenger details)
CREATE TABLE IF NOT EXISTS booking_seats (
    id BIGSERIAL PRIMARY KEY,
    booking_id BIGINT NOT NULL,
    passenger_name VARCHAR(255) NOT NULL,
    passenger_age INTEGER NOT NULL,
    passenger_gender VARCHAR(10) NOT NULL,
    price_cents INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_stations_code ON stations(code);
CREATE INDEX IF NOT EXISTS idx_stations_name ON stations(name);
CREATE INDEX IF NOT EXISTS idx_trains_number ON trains(number);
CREATE INDEX IF NOT EXISTS idx_trains_from_station ON trains(from_station_code);
CREATE INDEX IF NOT EXISTS idx_trains_to_station ON trains(to_station_code);
CREATE INDEX IF NOT EXISTS idx_train_stops_train ON train_stops(train_id);
CREATE INDEX IF NOT EXISTS idx_train_stops_station ON train_stops(station_code);
CREATE INDEX IF NOT EXISTS idx_train_stops_sequence ON train_stops(train_id, stop_sequence);
CREATE INDEX IF NOT EXISTS idx_train_runs_train ON train_runs(train_id);
CREATE INDEX IF NOT EXISTS idx_train_runs_date ON train_runs(run_date);
CREATE INDEX IF NOT EXISTS idx_seats_train_run ON seats(train_run_id);
CREATE INDEX IF NOT EXISTS idx_seats_status ON seats(status);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_booking_id ON bookings(booking_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_seats ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid()::text = id::text OR is_admin = true);

CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- RLS Policies for bookings
CREATE POLICY "Users can view their own bookings" ON bookings
    FOR SELECT USING (auth.uid()::text = user_id::text OR EXISTS (
        SELECT 1 FROM users WHERE id = user_id AND is_admin = true
    ));

CREATE POLICY "Users can create their own bookings" ON bookings
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- RLS Policies for booking_seats
CREATE POLICY "Users can view their booking seats" ON booking_seats
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM bookings WHERE id = booking_id AND user_id::text = auth.uid()::text
    ));
