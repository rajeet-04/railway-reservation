"""Seat generation service with Indian Railways coach layouts.

This module generates seat inventory for train runs based on class configurations.
Implements realistic coach layouts matching Indian Railways:
- SL (Sleeper): 72 seats per coach (8 bays × 8 berths + 4 side berths)
- 3A (AC 3-Tier): 64 seats per coach (8 bays × 8 berths)
- 2A (AC 2-Tier): 48 seats per coach (8 bays × 6 berths)
- 1A (AC First Class): 24 seats per coach (4 cabins × 4 berths + 2 coupes)
- CC (Chair Car): 78 seats per coach
- 2S (Second Sitting): 108 seats per coach
- GEN (General): 90+ seats per coach (unreserved)
"""

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, insert, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Train, TrainRun, Seat

logger = logging.getLogger(__name__)

# Default seats per coach for Indian Railways classes
DEFAULT_SEATS_PER_COACH: Dict[str, int] = {
    'SL': 72,   # Sleeper
    '3A': 64,   # AC 3-Tier
    '2A': 48,   # AC 2-Tier
    '1A': 24,   # AC First Class
    'CC': 78,   # Chair Car
    '2S': 108,  # Second Sitting
    'GEN': 90,  # General (unreserved, but we track inventory)
}

# Coach prefix mapping for class codes
COACH_PREFIX: Dict[str, str] = {
    'SL': 'S',   # S1, S2, ...
    '3A': 'A',   # A1, A2, ...
    '2A': 'B',   # B1, B2, ...
    '1A': 'H',   # H1, H2, ... (First Class coaches use 'H')
    'CC': 'C',   # C1, C2, ...
    '2S': 'D',   # D1, D2, ...
    'GEN': 'G',  # G1, G2, ...
}

# Base prices per class (in paise/cents for precise calculations)
BASE_PRICE_PER_KM: Dict[str, int] = {
    '1A': 500,  # ₹5.00/km
    '2A': 350,  # ₹3.50/km
    '3A': 250,  # ₹2.50/km
    'SL': 100,  # ₹1.00/km
    'CC': 120,  # ₹1.20/km
    '2S': 50,   # ₹0.50/km
    'GEN': 30,  # ₹0.30/km
}


def parse_classes_config(classes_json: Optional[str]) -> Dict[str, Dict[str, int]]:
    """Parse classes configuration JSON.
    
    Supports two formats:
    1. Simple format: {"SL": 2, "3A": 1} - number of coaches per class
    2. Detailed format: {"SL": {"coaches": 2, "seats_per_coach": 72}}
    
    Returns normalized format: {"SL": {"coaches": 2, "seats_per_coach": 72}}
    """
    if not classes_json:
        # Default: 1 Sleeper coach
        return {"SL": {"coaches": 1, "seats_per_coach": DEFAULT_SEATS_PER_COACH['SL']}}
    
    try:
        config = json.loads(classes_json)
    except json.JSONDecodeError:
        logger.warning(f"Invalid classes_json format, using default: {classes_json}")
        return {"SL": {"coaches": 1, "seats_per_coach": DEFAULT_SEATS_PER_COACH['SL']}}
    
    normalized = {}
    for class_code, value in config.items():
        if isinstance(value, int):
            # Simple format: number of coaches
            normalized[class_code] = {
                "coaches": value,
                "seats_per_coach": DEFAULT_SEATS_PER_COACH.get(class_code, 72)
            }
        elif isinstance(value, dict):
            # Detailed format
            coaches = value.get("coaches", 1)
            seats_per_coach = value.get("seats_per_coach", DEFAULT_SEATS_PER_COACH.get(class_code, 72))
            normalized[class_code] = {
                "coaches": coaches,
                "seats_per_coach": seats_per_coach
            }
    
    return normalized if normalized else {"SL": {"coaches": 1, "seats_per_coach": 72}}


def generate_seat_rows(
    train_run_id: int,
    class_code: str,
    num_coaches: int,
    seats_per_coach: int,
    distance_km: Optional[float] = None,
) -> List[Dict]:
    """Generate seat rows for a class with realistic coach splits.
    
    Args:
        train_run_id: ID of the train run
        class_code: Class code (SL, 3A, 2A, 1A, CC, 2S, GEN)
        num_coaches: Number of coaches for this class
        seats_per_coach: Seats per coach
        distance_km: Train distance for price calculation
        
    Returns:
        List of seat dictionaries ready for bulk insert
    """
    seats = []
    coach_prefix = COACH_PREFIX.get(class_code, 'X')
    
    # Calculate base price (use average 500km distance if actual distance not available)
    if distance_km and class_code in BASE_PRICE_PER_KM:
        price = int(distance_km * BASE_PRICE_PER_KM[class_code])
    else:
        # Fallback: use 500km as default distance
        default_km = 500
        price = int(default_km * BASE_PRICE_PER_KM.get(class_code, 100))  # Default ₹1/km
    
    for coach_num in range(1, num_coaches + 1):
        coach_name = f"{coach_prefix}{coach_num}"
        
        for seat_num in range(1, seats_per_coach + 1):
            # Generate unique seat number including coach (e.g., "S1-1", "A1-1")
            # This ensures uniqueness across different coaches/classes
            seat_number = f"{coach_name}-{seat_num}"
            
            # Determine berth type for sleeper classes
            berth_type = None
            if class_code in ['SL', '3A', '2A', '1A']:
                # Berth types: LB (Lower), MB (Middle - only SL/3A), UB (Upper), SL (Side Lower), SU (Side Upper)
                if class_code in ['SL', '3A']:
                    # 8 bays × 8 berths + side berths
                    if seat_num % 8 in [1, 4]:
                        berth_type = 'LB'
                    elif seat_num % 8 in [2, 5]:
                        berth_type = 'MB'
                    elif seat_num % 8 in [3, 6]:
                        berth_type = 'UB'
                    elif seat_num % 8 == 7:
                        berth_type = 'SL'
                    else:  # seat_num % 8 == 0
                        berth_type = 'SU'
                elif class_code == '2A':
                    # 2A has no middle berth
                    if seat_num % 6 in [1, 3, 5]:
                        berth_type = 'LB'
                    else:
                        berth_type = 'UB'
                elif class_code == '1A':
                    # 1A cabins with 4 berths each
                    if seat_num % 4 in [1, 3]:
                        berth_type = 'LB'
                    else:
                        berth_type = 'UB'
            
            seats.append({
                'train_run_id': train_run_id,
                'seat_number': seat_number,
                'coach_number': coach_name,
                'seat_class': class_code,
                'status': 'AVAILABLE',
                'price_cents': price,
            })
    
    return seats


async def generate_seats_for_runs(
    session: AsyncSession,
    days: int = 20,
    batch_size: int = 500,
    train_ids: Optional[List[int]] = None,
) -> Dict[str, int]:
    """Generate seats for train runs that don't have seat inventory.
    
    Args:
        session: Async database session
        days: Number of days from today to process (default: 20)
        batch_size: Batch size for bulk inserts (default: 500)
        train_ids: Optional list of specific train IDs to process
        
    Returns:
        Dict with statistics: {
            'runs_processed': int,
            'seats_created': int,
            'trains_processed': int,
        }
    """
    logger.info(f"Starting seat generation for {days} days (batch_size={batch_size})")
    
    stats = {
        'runs_processed': 0,
        'seats_created': 0,
        'trains_processed': 0,
    }
    
    # Determine date range
    today = date.today()
    end_date = today + timedelta(days=days - 1)
    
    # Find train runs without seats
    query = (
        select(TrainRun, Train)
        .join(Train, TrainRun.train_id == Train.id)
        .outerjoin(Seat, Seat.train_run_id == TrainRun.id)
        .where(
            and_(
                TrainRun.run_date >= today,
                TrainRun.run_date <= end_date,
            )
        )
        .group_by(TrainRun.id, Train.id)
        .having(func.count(Seat.id) == 0)
    )
    
    if train_ids:
        query = query.where(TrainRun.train_id.in_(train_ids))
    
    result = await session.execute(query)
    runs_to_process = result.all()
    
    logger.info(f"Found {len(runs_to_process)} train runs needing seat generation")
    
    processed_trains = set()
    
    for train_run, train in runs_to_process:
        logger.info(f"Generating seats for train {train.number} on {train_run.run_date}")
        
        # Parse class configuration (actual schema uses "classes" column, not "classes_json")
        classes_config = parse_classes_config(train.classes)
        
        # Generate seats for each class
        all_seats = []
        for class_code, config in classes_config.items():
            num_coaches = config['coaches']
            seats_per_coach = config['seats_per_coach']
            
            seats = generate_seat_rows(
                train_run_id=train_run.id,
                class_code=class_code,
                num_coaches=num_coaches,
                seats_per_coach=seats_per_coach,
                distance_km=train.distance_km,
            )
            all_seats.extend(seats)
        
        # Bulk insert seats in batches
        for i in range(0, len(all_seats), batch_size):
            batch = all_seats[i:i + batch_size]
            await session.execute(insert(Seat).values(batch))
        
        # Update train_run totals
        total_seats = len(all_seats)
        train_run.total_seats = total_seats
        train_run.available_seats = total_seats
        
        await session.commit()
        
        stats['runs_processed'] += 1
        stats['seats_created'] += total_seats
        processed_trains.add(train.id)
        
        logger.info(
            f"Created {total_seats} seats for train {train.number} "
            f"({len(classes_config)} classes, {sum(c['coaches'] for c in classes_config.values())} coaches)"
        )
    
    stats['trains_processed'] = len(processed_trains)
    
    logger.info(
        f"Seat generation complete: {stats['runs_processed']} runs, "
        f"{stats['seats_created']} seats, {stats['trains_processed']} trains"
    )
    
    return stats


async def generate_seats_for_train_run(
    session: AsyncSession,
    train_run_id: int,
) -> int:
    """Generate seats for a specific train run.
    
    Args:
        session: Async database session
        train_run_id: ID of the train run
        
    Returns:
        Number of seats created
    """
    # Check if seats already exist
    count_query = select(func.count(Seat.id)).where(Seat.train_run_id == train_run_id)
    result = await session.execute(count_query)
    existing_count = result.scalar()
    
    if existing_count > 0:
        logger.warning(f"Train run {train_run_id} already has {existing_count} seats")
        return 0
    
    # Load train run and train
    query = (
        select(TrainRun, Train)
        .join(Train, TrainRun.train_id == Train.id)
        .where(TrainRun.id == train_run_id)
    )
    result = await session.execute(query)
    row = result.first()
    
    if not row:
        logger.error(f"Train run {train_run_id} not found")
        return 0
    
    train_run, train = row
    
    # Parse class configuration (actual schema uses "classes" column, not "classes_json")
    classes_config = parse_classes_config(train.classes)
    
    # Generate seats
    all_seats = []
    for class_code, config in classes_config.items():
        seats = generate_seat_rows(
            train_run_id=train_run.id,
            class_code=class_code,
            num_coaches=config['coaches'],
            seats_per_coach=config['seats_per_coach'],
            distance_km=train.distance_km,
        )
        all_seats.extend(seats)
    
    # Bulk insert
    if all_seats:
        await session.execute(insert(Seat).values(all_seats))
        
        # Update train_run totals
        train_run.total_seats = len(all_seats)
        train_run.available_seats = len(all_seats)
        
        await session.commit()
    
    logger.info(f"Created {len(all_seats)} seats for train run {train_run_id}")
    
    return len(all_seats)
