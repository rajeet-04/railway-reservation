#!/usr/bin/env python3
"""
Data Migration Script: Transfer JSON data to Supabase
Transfers stations, trains, and schedules data to Supabase PostgreSQL database
"""

import json
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
    exit(1)

# Initialize Supabase client with service role key for admin access
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def load_json_file(filepath):
    """Load JSON file"""
    print(f"Loading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def batch_insert(table_name, data, batch_size=1000):
    """Insert data in batches"""
    total = len(data)
    print(f"Inserting {total} records into {table_name}...")
    
    for i in tqdm(range(0, total, batch_size)):
        batch = data[i:i + batch_size]
        try:
            supabase.table(table_name).insert(batch).execute()
        except Exception as e:
            print(f"Error inserting batch {i//batch_size + 1}: {e}")
            # Try inserting one by one if batch fails
            for item in batch:
                try:
                    supabase.table(table_name).insert(item).execute()
                except Exception as e2:
                    print(f"Error inserting item: {e2}")
                    continue


def migrate_stations():
    """Migrate stations from GeoJSON to Supabase"""
    print("\n=== Migrating Stations ===")
    
    data = load_json_file("data/stations.json")
    features = data.get("features", [])
    
    stations = []
    for feature in features:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None])
        
        station = {
            "code": props.get("code"),
            "name": props.get("name"),
            "state": props.get("state"),
            "zone": props.get("zone"),
            "address": props.get("address"),
            "longitude": coords[0] if coords[0] else None,
            "latitude": coords[1] if coords[1] else None,
        }
        
        if station["code"] and station["name"]:
            stations.append(station)
    
    batch_insert("stations", stations)
    print(f"✓ Migrated {len(stations)} stations")


def migrate_trains():
    """Migrate trains from GeoJSON to Supabase"""
    print("\n=== Migrating Trains ===")
    
    data = load_json_file("data/trains.json")
    features = data.get("features", [])
    
    trains = []
    routes = []
    
    for feature in features:
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        
        train = {
            "number": props.get("trainNumber"),
            "name": props.get("trainName"),
            "from_station_code": props.get("fromStationCode"),
            "to_station_code": props.get("toStationCode"),
            "from_station_name": props.get("fromStationName"),
            "to_station_name": props.get("toStationName"),
            "departure_time": props.get("departureTime"),
            "arrival_time": props.get("arrivalTime"),
            "duration_minutes": props.get("durationMinutes"),
            "distance_km": props.get("distance"),
            "has_ac": props.get("classes", {}).get("hasAC", False),
            "has_sleeper": props.get("classes", {}).get("hasSleeper", False),
            "has_general": props.get("classes", {}).get("hasGeneral", False),
        }
        
        if train["number"] and train["name"]:
            trains.append(train)
    
    # Insert trains first
    batch_insert("trains", trains)
    print(f"✓ Migrated {len(trains)} trains")
    
    # Get train IDs mapping
    print("Fetching train IDs...")
    train_ids = {}
    result = supabase.table("trains").select("id, number").execute()
    for train in result.data:
        train_ids[train["number"]] = train["id"]
    
    # Insert routes with geometry
    print("\nInserting train routes...")
    for feature in tqdm(features):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        train_number = props.get("trainNumber")
        
        if train_number and train_number in train_ids:
            route = {
                "train_id": train_ids[train_number],
                "geometry": geometry
            }
            try:
                supabase.table("train_routes").insert(route).execute()
            except Exception as e:
                print(f"Error inserting route for train {train_number}: {e}")
                continue
    
    print(f"✓ Migrated train routes")


def migrate_schedules():
    """Migrate train schedules to Supabase"""
    print("\n=== Migrating Train Schedules ===")
    
    data = load_json_file("data/schedules.json")
    
    # Get train IDs mapping
    print("Fetching train IDs...")
    train_ids = {}
    result = supabase.table("trains").select("id, number").execute()
    for train in result.data:
        train_ids[train["number"]] = train["id"]
    
    # Group schedules by train
    train_schedules = {}
    for schedule in data:
        train_number = schedule.get("trainNumber")
        if train_number not in train_schedules:
            train_schedules[train_number] = []
        train_schedules[train_number].append(schedule)
    
    # Insert stops
    stops = []
    for train_number, schedules in tqdm(train_schedules.items()):
        if train_number not in train_ids:
            continue
        
        train_id = train_ids[train_number]
        
        # Sort by sequence
        schedules.sort(key=lambda x: x.get("stopNumber", 0))
        
        for schedule in schedules:
            stop = {
                "train_id": train_id,
                "station_code": schedule.get("stationCode"),
                "stop_sequence": schedule.get("stopNumber"),
                "arrival_time": schedule.get("arrivalTime"),
                "departure_time": schedule.get("departureTime"),
                "day_offset": schedule.get("day", 0),
            }
            
            if stop["station_code"] and stop["stop_sequence"]:
                stops.append(stop)
    
    batch_insert("train_stops", stops)
    print(f"✓ Migrated {len(stops)} train stops")


def create_train_runs():
    """Create train runs for next 30 days"""
    print("\n=== Creating Train Runs ===")
    
    # Get all trains
    result = supabase.table("trains").select("id").execute()
    train_ids = [t["id"] for t in result.data]
    
    # Create runs for next 30 days
    today = datetime.now().date()
    runs = []
    
    for train_id in tqdm(train_ids):
        for day in range(30):
            run_date = today + timedelta(days=day)
            runs.append({
                "train_id": train_id,
                "run_date": run_date.isoformat(),
                "status": "SCHEDULED"
            })
    
    batch_insert("train_runs", runs)
    print(f"✓ Created {len(runs)} train runs")


def main():
    """Main migration function"""
    print("=" * 60)
    print("Railway Reservation System - Data Migration to Supabase")
    print("=" * 60)
    
    try:
        # Migrate data
        migrate_stations()
        migrate_trains()
        migrate_schedules()
        create_train_runs()
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
        # Print statistics
        stations_count = supabase.table("stations").select("count", count="exact").execute()
        trains_count = supabase.table("trains").select("count", count="exact").execute()
        stops_count = supabase.table("train_stops").select("count", count="exact").execute()
        runs_count = supabase.table("train_runs").select("count", count="exact").execute()
        
        print(f"\nDatabase Statistics:")
        print(f"  Stations: {stations_count.count}")
        print(f"  Trains: {trains_count.count}")
        print(f"  Train Stops: {stops_count.count}")
        print(f"  Train Runs: {runs_count.count}")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
