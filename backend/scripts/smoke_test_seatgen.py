"""Smoke test for seat generation service.

This script tests the seat generation service using an in-memory SQLite database.
It verifies that seats are correctly generated with Indian Railways coach layouts.
"""

import sys
import asyncio
import logging
from datetime import date

# Check Python version
if sys.version_info < (3, 11):
    print("ERROR: Python 3.11+ required")
    print(f"Current version: {sys.version}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).replace('\\scripts\\smoke_test_seatgen.py', ''))

try:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, func
    from app.db.models import Base, Train, TrainRun, Seat, Station
    from app.services.seatgen import generate_seats_for_runs
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("\nInstall dependencies:")
    print("  cd backend")
    print("  pip install -r requirements.txt")
    sys.exit(1)


async def run_smoke_test():
    """Run smoke test for seat generation."""
    
    print("\n" + "="*60)
    print("Seat Generation Smoke Test")
    print("="*60 + "\n")
    
    # Create in-memory async engine
    logger.info("Creating in-memory SQLite database...")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ Tables created")
    
    # Create session
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Insert test station
        station = Station(
            code="TEST",
            name="Test Station",
            lat=28.6139,
            lon=77.2090,
        )
        session.add(station)
        await session.flush()
        logger.info("✓ Test station created")
        
        # Insert test train with Indian Railways class configuration
        # SL: 1 coach with 10 seats (for easy testing)
        # 3A: 1 coach with 5 seats (for easy testing)
        # Total expected: 15 seats
        train = Train(
            number="12345",
            name="Test Express",
            type="Express",
            from_station_code="TEST",
            to_station_code="TEST",
            distance_km=500.0,
            classes_json='{"SL": {"coaches": 1, "seats_per_coach": 10}, "3A": {"coaches": 1, "seats_per_coach": 5}}',
            has_sl=True,
            has_3a=True,
        )
        session.add(train)
        await session.flush()
        logger.info(f"✓ Test train created (ID: {train.id})")
        
        # Insert train run for today
        today = date.today()
        train_run = TrainRun(
            train_id=train.id,
            run_date=today,
            status="SCHEDULED",
        )
        session.add(train_run)
        await session.commit()
        logger.info(f"✓ Train run created for {today}")
        
        # Verify no seats exist
        count_query = select(func.count(Seat.id))
        result = await session.execute(count_query)
        initial_count = result.scalar()
        assert initial_count == 0, f"Expected 0 seats, found {initial_count}"
        logger.info("✓ Confirmed zero seats before generation")
        
        # Run seat generation
        print("\nRunning seat generation...")
        stats = await generate_seats_for_runs(session, days=1, batch_size=100)
        
        print(f"\nGeneration Stats:")
        print(f"  Runs processed: {stats['runs_processed']}")
        print(f"  Seats created: {stats['seats_created']}")
        print(f"  Trains processed: {stats['trains_processed']}")
        
        # Verify seat count
        result = await session.execute(count_query)
        final_count = result.scalar()
        
        expected_seats = 15  # 10 SL + 5 3A
        assert final_count == expected_seats, f"Expected {expected_seats} seats, found {final_count}"
        logger.info(f"✓ Verified {final_count} seats created")
        
        # Verify seat distribution
        sl_query = select(func.count(Seat.id)).where(Seat.seat_class == "SL")
        result = await session.execute(sl_query)
        sl_count = result.scalar()
        assert sl_count == 10, f"Expected 10 SL seats, found {sl_count}"
        
        ac3_query = select(func.count(Seat.id)).where(Seat.seat_class == "3A")
        result = await session.execute(ac3_query)
        ac3_count = result.scalar()
        assert ac3_count == 5, f"Expected 5 3A seats, found {ac3_count}"
        
        logger.info(f"✓ Seat distribution verified (SL: {sl_count}, 3A: {ac3_count})")
        
        # Verify coach assignments
        sl_seats_query = select(Seat).where(Seat.seat_class == "SL").limit(3)
        result = await session.execute(sl_seats_query)
        sl_seats = result.scalars().all()
        
        for seat in sl_seats:
            assert seat.coach == "S1", f"Expected coach S1, found {seat.coach}"
            assert seat.berth_type in ['LB', 'MB', 'UB', 'SL', 'SU'], f"Invalid berth type: {seat.berth_type}"
        
        logger.info("✓ Coach labels verified (S1 for Sleeper)")
        
        # Verify train_run totals updated
        await session.refresh(train_run)
        assert train_run.total_seats == expected_seats, f"Expected total_seats={expected_seats}, found {train_run.total_seats}"
        assert train_run.available_seats == expected_seats, f"Expected available_seats={expected_seats}, found {train_run.available_seats}"
        logger.info(f"✓ TrainRun totals updated (total={train_run.total_seats}, available={train_run.available_seats})")
        
        # Sample seat details
        print("\nSample Seats:")
        sample_query = select(Seat).limit(5)
        result = await session.execute(sample_query)
        sample_seats = result.scalars().all()
        
        for seat in sample_seats:
            print(f"  {seat.coach}-{seat.seat_number} [{seat.seat_class}] {seat.berth_type or 'N/A'} - {seat.status}")
    
    await engine.dispose()
    
    print("\n" + "="*60)
    print("✅ SMOKE TEST PASSED")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_smoke_test())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ SMOKE TEST FAILED: {e}", exc_info=True)
        print("\n" + "="*60)
        print("❌ SMOKE TEST FAILED")
        print("="*60)
        sys.exit(1)
