"""Generate seats for existing train runs in the database.

Usage:
    # Generate seats for next 20 days (default)
    python scripts/seed_seats.py
    
    # Generate seats for next 30 days
    python scripts/seed_seats.py --days 30
    
    # Generate for specific trains only
    python scripts/seed_seats.py --train-ids 123,456,789
    
    # Dry run (don't commit to database)
    python scripts/seed_seats.py --dry-run
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func

from app.db.models import Train, TrainRun, Seat
from app.services.seatgen import generate_seats_for_runs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def seed_seats(
    database_url: str,
    days: int = 20,
    train_ids: list[int] | None = None,
    dry_run: bool = False,
    batch_size: int = 500,
):
    """Generate seats for train runs."""
    
    logger.info("="*60)
    logger.info("Railway Seat Generation Script")
    logger.info("="*60)
    logger.info(f"Database: {database_url[:50]}...")
    logger.info(f"Days to process: {days}")
    logger.info(f"Batch size: {batch_size}")
    if train_ids:
        logger.info(f"Train IDs filter: {train_ids}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("="*60)
    
    # Create async engine
    engine_kwargs = {"echo": False}
    if "sqlite" not in database_url:
        engine_kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
        })
    
    engine = create_async_engine(database_url, **engine_kwargs)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Get statistics before generation
        logger.info("\nDatabase Statistics (Before):")
        
        result = await session.execute(select(func.count(Train.id)))
        total_trains = result.scalar()
        logger.info(f"  Total trains: {total_trains:,}")
        
        result = await session.execute(select(func.count(TrainRun.id)))
        total_runs = result.scalar()
        logger.info(f"  Total train runs: {total_runs:,}")
        
        result = await session.execute(select(func.count(Seat.id)))
        existing_seats = result.scalar()
        logger.info(f"  Existing seats: {existing_seats:,}")
        
        # Calculate runs without seats
        today = date.today()
        runs_without_seats_query = (
            select(func.count(TrainRun.id))
            .outerjoin(Seat, Seat.train_run_id == TrainRun.id)
            .where(TrainRun.run_date >= today)
            .group_by(TrainRun.id)
            .having(func.count(Seat.id) == 0)
        )
        result = await session.execute(runs_without_seats_query)
        runs_needing_seats = len(result.all())
        logger.info(f"  Runs needing seats: {runs_needing_seats:,}")
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes will be committed")
        
        # Run seat generation
        logger.info("\nStarting seat generation...")
        logger.info("-"*60)
        
        stats = await generate_seats_for_runs(
            session,
            days=days,
            batch_size=batch_size,
            train_ids=train_ids,
        )
        
        if dry_run:
            await session.rollback()
            logger.info("\n⚠️  Changes rolled back (dry run)")
        else:
            # Final commit happens in generate_seats_for_runs
            pass
        
        # Get statistics after generation
        logger.info("\n" + "="*60)
        logger.info("Generation Complete")
        logger.info("="*60)
        logger.info(f"Runs processed: {stats['runs_processed']:,}")
        logger.info(f"Seats created: {stats['seats_created']:,}")
        logger.info(f"Trains processed: {stats['trains_processed']:,}")
        
        if stats['seats_created'] > 0:
            avg_seats_per_run = stats['seats_created'] / stats['runs_processed']
            logger.info(f"Average seats per run: {avg_seats_per_run:.1f}")
        
        # Verify final counts
        if not dry_run:
            result = await session.execute(select(func.count(Seat.id)))
            final_seats = result.scalar()
            new_seats = final_seats - existing_seats
            logger.info(f"\nTotal seats in database: {final_seats:,} (+{new_seats:,})")
    
    await engine.dispose()
    logger.info("\n✅ Seat generation complete!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate seat inventory for train runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database URL (default: from DATABASE_URL env or sqlite+aiosqlite:///./database/railway.db)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=20,
        help="Number of days from today to process (default: 20)"
    )
    
    parser.add_argument(
        "--train-ids",
        type=str,
        help="Comma-separated list of train IDs to process (default: all trains)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for bulk inserts (default: 500)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to database"
    )
    
    args = parser.parse_args()
    
    # Determine database URL
    if args.database_url:
        database_url = args.database_url
    else:
        # Try environment variable
        import os
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            # Default to SQLite in parent directory
            db_path = Path(__file__).parent.parent.parent / "database" / "railway.db"
            database_url = f"sqlite+aiosqlite:///{db_path}"
            logger.info(f"Using default database: {db_path}")
    
    # Parse train IDs
    train_ids = None
    if args.train_ids:
        try:
            train_ids = [int(tid.strip()) for tid in args.train_ids.split(",")]
        except ValueError:
            logger.error("Invalid train IDs format. Use comma-separated integers.")
            sys.exit(1)
    
    # Run async main
    try:
        asyncio.run(seed_seats(
            database_url=database_url,
            days=args.days,
            train_ids=train_ids,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
        ))
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
