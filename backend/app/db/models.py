"""SQLAlchemy ORM models matching database/schema.sql."""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Date, DateTime, Text, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class User(Base):
    """User model for authentication and bookings."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")


class Station(Base):
    """Railway station model."""
    
    __tablename__ = "stations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    zone: Mapped[Optional[str]] = mapped_column(String(10))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        Index('idx_stations_coords', 'latitude', 'longitude'),
    )


class Train(Base):
    """Train model with route and class information."""
    
    __tablename__ = "trains"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(50))
    zone: Mapped[Optional[str]] = mapped_column(String(10))
    from_station_code: Mapped[Optional[str]] = mapped_column(String(10))
    to_station_code: Mapped[Optional[str]] = mapped_column(String(10))
    from_station_name: Mapped[Optional[str]] = mapped_column(String(255))
    to_station_name: Mapped[Optional[str]] = mapped_column(String(255))
    departure_time: Mapped[Optional[str]] = mapped_column(String(10))
    arrival_time: Mapped[Optional[str]] = mapped_column(String(10))
    distance_km: Mapped[Optional[int]] = mapped_column(Integer)
    duration_h: Mapped[Optional[int]] = mapped_column(Integer)
    duration_m: Mapped[Optional[int]] = mapped_column(Integer)
    return_train: Mapped[Optional[str]] = mapped_column(String(10))
    
    # JSON field storing class configuration: {"SL": {"coaches": 2, "seats_per_coach": 72}, ...}
    # Note: In actual schema this is called "classes" (TEXT column)
    classes: Mapped[Optional[str]] = mapped_column("classes", Text)
    properties_json: Mapped[Optional[str]] = mapped_column(Text)
    
    # Class availability flags (actual schema uses different names)
    first_ac: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    second_ac: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    third_ac: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    sleeper: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    chair_car: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    first_class: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        Index('idx_trains_from_to', 'from_station_code', 'to_station_code'),
    )
    
    # Relationships
    train_stops: Mapped[list["TrainStop"]] = relationship("TrainStop", back_populates="train")
    train_runs: Mapped[list["TrainRun"]] = relationship("TrainRun", back_populates="train")


class TrainRoute(Base):
    """Train route geometry (GeoJSON LineString)."""
    
    __tablename__ = "train_routes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(Integer, ForeignKey("trains.id"), nullable=False, index=True)
    coordinates_json: Mapped[Optional[str]] = mapped_column(Text)


class TrainStop(Base):
    """Scheduled stops for trains."""
    
    __tablename__ = "train_stops"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(Integer, ForeignKey("trains.id"), nullable=False)
    station_code: Mapped[str] = mapped_column(String(10), ForeignKey("stations.code"), nullable=False)
    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_time: Mapped[Optional[str]] = mapped_column(String(10))
    departure_time: Mapped[Optional[str]] = mapped_column(String(10))
    day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distance_from_start_km: Mapped[Optional[int]] = mapped_column(Integer)
    halt_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    platform: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('train_id', 'stop_sequence', name='uq_train_stop_sequence'),
        Index('idx_train_stops_train', 'train_id'),
        Index('idx_train_stops_station', 'station_code'),
        Index('idx_train_stops_sequence', 'train_id', 'stop_sequence'),
    )
    
    # Relationships
    train: Mapped["Train"] = relationship("Train", back_populates="train_stops")


class TrainRun(Base):
    """Date-specific train run instances."""
    
    __tablename__ = "train_runs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(Integer, ForeignKey("trains.id"), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='SCHEDULED', nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('train_id', 'run_date', name='uq_train_run_date'),
        Index('idx_train_runs_train', 'train_id'),
        Index('idx_train_runs_date', 'run_date'),
        Index('idx_train_runs_status', 'status'),
    )
    
    # Relationships
    train: Mapped["Train"] = relationship("Train", back_populates="train_runs")
    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="train_run")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="train_run")


class Seat(Base):
    """Individual seat inventory per train run."""
    
    __tablename__ = "seats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("train_runs.id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)
    coach_number: Mapped[Optional[str]] = mapped_column(String(10))  # e.g., S1, A1
    seat_class: Mapped[str] = mapped_column(String(10), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # Price in cents/paise
    status: Mapped[str] = mapped_column(String(20), default='AVAILABLE', nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('train_run_id', 'seat_number', name='uq_seat_number'),
        Index('idx_seats_train_run', 'train_run_id'),
        Index('idx_seats_status', 'status'),
        Index('idx_seats_class', 'seat_class'),
    )
    
    # Relationships
    train_run: Mapped["TrainRun"] = relationship("TrainRun", back_populates="seats")
    booking_seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="seat")


class Booking(Base):
    """Passenger bookings."""
    
    __tablename__ = "bookings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    train_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("train_runs.id"), nullable=False)
    from_station_id: Mapped[int] = mapped_column(Integer, ForeignKey("stations.id"), nullable=False)
    to_station_id: Mapped[int] = mapped_column(Integer, ForeignKey("stations.id"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    journey_date: Mapped[date] = mapped_column(Date, nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_fare: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    status: Mapped[str] = mapped_column(String(20), default='CONFIRMED', nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default='PENDING', nullable=False)
    passenger_details: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_bookings_user', 'user_id'),
        Index('idx_bookings_train_run', 'train_run_id'),
        Index('idx_bookings_status', 'status'),
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="bookings")
    train_run: Mapped["TrainRun"] = relationship("TrainRun", back_populates="bookings")
    booking_seats: Mapped[list["BookingSeat"]] = relationship("BookingSeat", back_populates="booking")


class BookingSeat(Base):
    """Junction table linking bookings to seats."""
    
    __tablename__ = "booking_seats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    seat_id: Mapped[int] = mapped_column(Integer, ForeignKey("seats.id"), nullable=False)
    passenger_name: Mapped[Optional[str]] = mapped_column(String(255))
    passenger_age: Mapped[Optional[int]] = mapped_column(Integer)
    passenger_gender: Mapped[Optional[str]] = mapped_column(String(10))
    
    __table_args__ = (
        UniqueConstraint('booking_id', 'seat_id', name='uq_booking_seat'),
        Index('idx_booking_seats_booking', 'booking_id'),
        Index('idx_booking_seats_seat', 'seat_id'),
    )
    
    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="booking_seats")
    seat: Mapped["Seat"] = relationship("Seat", back_populates="booking_seats")


class ImportLog(Base):
    """Logs for data import operations."""
    
    __tablename__ = "import_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_success: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MappingWarning(Base):
    """Warnings from route coordinate mapping."""
    
    __tablename__ = "mapping_warnings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    train_id: Mapped[int] = mapped_column(Integer, ForeignKey("trains.id"), nullable=False, index=True)
    warning_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
