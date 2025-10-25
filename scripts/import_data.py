#!/usr/bin/env python3
"""
Railway Reservation System - Database Import Script

This script imports GeoJSON data (stations, trains, schedules) into a SQLite database
with spatial matching of train routes to station sequences.

Features:
- Loads stations from stations.json (GeoJSON FeatureCollection)
- Loads trains from trains.json with LineString geometries
- Maps train route coordinates to nearest stations using haversine distance
- Imports schedules from schedules.json (large file, streaming parse)
- Creates normalized relational schema for routing and bookings
- Generates diagnostic reports for mapping quality

Usage:
    python scripts/import_data.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import time

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, **kwargs):
        return iterable

try:
    from sklearn.neighbors import BallTree
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not installed. Falling back to slower nearest-neighbor search.")


@dataclass
class Station:
    code: str
    name: str
    state: Optional[str]
    zone: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass
class Train:
    number: str
    name: str
    from_station_code: str
    to_station_code: str
    from_station_name: str
    to_station_name: str
    zone: Optional[str]
    train_type: Optional[str]
    distance_km: Optional[int]
    duration_h: Optional[int]
    duration_m: Optional[int]
    departure_time: Optional[str]
    arrival_time: Optional[str]
    return_train: Optional[str]
    first_ac: int
    second_ac: int
    third_ac: int
    sleeper: int
    chair_car: int
    first_class: int
    classes: str
    geometry_coords: Optional[List[List[float]]]


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


class SpatialIndex:
    """Spatial index for fast nearest-neighbor station lookup."""
    
    def __init__(self, stations_with_coords: List[Tuple[str, float, float]]):
        """
        Initialize spatial index.
        
        Args:
            stations_with_coords: List of (station_code, lat, lon) tuples
        """
        self.stations_with_coords = stations_with_coords
        
        if HAS_SKLEARN and len(stations_with_coords) > 0:
            # Use BallTree for fast nearest neighbor search
            coords = np.array([[lat, lon] for _, lat, lon in stations_with_coords])
            # Convert to radians for haversine
            coords_rad = np.radians(coords)
            self.tree = BallTree(coords_rad, metric='haversine')
            self.use_tree = True
        else:
            self.use_tree = False
    
    def find_nearest(self, lat: float, lon: float, max_distance_km: float = 50.0) -> Optional[Tuple[str, float]]:
        """
        Find nearest station to given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            max_distance_km: Maximum search radius in kilometers
            
        Returns:
            Tuple of (station_code, distance_km) or None if no station within radius
        """
        if len(self.stations_with_coords) == 0:
            return None
        
        if self.use_tree:
            # Fast search using BallTree
            point = np.radians([[lat, lon]])
            dist, ind = self.tree.query(point, k=1)
            distance_km = dist[0][0] * 6371  # Convert radians to km
            
            if distance_km <= max_distance_km:
                station_code = self.stations_with_coords[ind[0][0]][0]
                return (station_code, distance_km)
            return None
        else:
            # Brute force search
            min_dist = float('inf')
            nearest_code = None
            
            for code, s_lat, s_lon in self.stations_with_coords:
                dist = haversine_distance(lon, lat, s_lon, s_lat)
                if dist < min_dist:
                    min_dist = dist
                    nearest_code = code
            
            if min_dist <= max_distance_km:
                return (nearest_code, min_dist)
            return None


class RailwayDatabaseImporter:
    """Main importer class for railway data."""
    
    def __init__(self, db_path: str, data_dir: str):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.conn: Optional[sqlite3.Connection] = None
        self.spatial_index: Optional[SpatialIndex] = None
        self.stats = {
            'stations_imported': 0,
            'stations_with_coords': 0,
            'trains_imported': 0,
            'stops_imported': 0,
            'route_coords_mapped': 0,
            'route_coords_unmapped': 0,
            'schedules_imported': 0,
        }
    
    def connect(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        print(f"✓ Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
    
    def create_schema(self, schema_path: str):
        """Execute schema SQL file."""
        print("Creating database schema...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        self.conn.executescript(schema_sql)
        self.conn.commit()
        print("✓ Schema created successfully")
    
    def import_stations(self):
        """Import stations from stations.json."""
        print("\nImporting stations...")
        stations_file = self.data_dir / 'stations.json'
        
        with open(stations_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stations = []
        stations_with_coords = []
        
        for feature in tqdm(data['features'], desc="Processing stations"):
            props = feature['properties']
            geom = feature.get('geometry')
            
            lat, lon = None, None
            if geom and geom.get('coordinates'):
                lon, lat = geom['coordinates']
            
            station = Station(
                code=props['code'],
                name=props['name'],
                state=props.get('state'),
                zone=props.get('zone'),
                address=props.get('address'),
                latitude=lat,
                longitude=lon
            )
            stations.append(station)
            
            if lat is not None and lon is not None:
                stations_with_coords.append((station.code, lat, lon))
        
        # Insert into database
        cursor = self.conn.cursor()
        for station in tqdm(stations, desc="Inserting stations"):
            cursor.execute("""
                INSERT OR IGNORE INTO stations 
                (code, name, state, zone, address, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                station.code,
                station.name,
                station.state,
                station.zone,
                station.address,
                station.latitude,
                station.longitude
            ))
        
        self.conn.commit()
        self.stats['stations_imported'] = len(stations)
        self.stats['stations_with_coords'] = len(stations_with_coords)
        
        print(f"✓ Imported {len(stations)} stations ({len(stations_with_coords)} with coordinates)")
        
        # Build spatial index
        print("Building spatial index...")
        self.spatial_index = SpatialIndex(stations_with_coords)
        print("✓ Spatial index built")
    
    def map_route_to_stations(self, train_number: str, coordinates: List[List[float]], 
                              threshold_km: float = 15.0) -> List[Tuple[str, int]]:
        """
        Map LineString coordinates to station sequence.
        
        Args:
            train_number: Train number for logging
            coordinates: List of [lon, lat] coordinate pairs
            threshold_km: Maximum distance for mapping
            
        Returns:
            List of (station_code, coord_index) tuples
        """
        if not self.spatial_index:
            return []
        
        mapped_stations = []
        prev_station = None
        
        for idx, coord in enumerate(coordinates):
            lon, lat = coord
            result = self.spatial_index.find_nearest(lat, lon, max_distance_km=threshold_km)
            
            if result:
                station_code, distance = result
                
                # Only add if different from previous station (remove consecutive duplicates)
                if station_code != prev_station:
                    mapped_stations.append((station_code, idx))
                    prev_station = station_code
                    self.stats['route_coords_mapped'] += 1
                
                # Log warning if distance is large
                if distance > 5.0:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        INSERT INTO mapping_warnings 
                        (train_number, coordinate_index, latitude, longitude, 
                         nearest_station_code, distance_km, warning_type, message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        train_number, idx, lat, lon, station_code, distance,
                        'LARGE_DISTANCE',
                        f'Station {station_code} is {distance:.2f}km from route point'
                    ))
            else:
                self.stats['route_coords_unmapped'] += 1
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO mapping_warnings 
                    (train_number, coordinate_index, latitude, longitude, 
                     nearest_station_code, distance_km, warning_type, message)
                    VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)
                """, (
                    train_number, idx, lat, lon,
                    'NO_STATION_NEARBY',
                    f'No station within {threshold_km}km of route point'
                ))
        
        return mapped_stations
    
    def import_trains(self):
        """Import trains from trains.json."""
        print("\nImporting trains...")
        trains_file = self.data_dir / 'trains.json'
        
        # Stream parse large file
        with open(trains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cursor = self.conn.cursor()
        
        for feature in tqdm(data['features'], desc="Processing trains"):
            props = feature['properties']
            geom = feature.get('geometry', {})
            
            train = Train(
                number=props['number'],
                name=props['name'],
                from_station_code=props['from_station_code'],
                to_station_code=props['to_station_code'],
                from_station_name=props.get('from_station_name', ''),
                to_station_name=props.get('to_station_name', ''),
                zone=props.get('zone'),
                train_type=props.get('type'),
                distance_km=props.get('distance'),
                duration_h=props.get('duration_h'),
                duration_m=props.get('duration_m'),
                departure_time=props.get('departure'),
                arrival_time=props.get('arrival'),
                return_train=props.get('return_train'),
                first_ac=props.get('first_ac', 0),
                second_ac=props.get('second_ac', 0),
                third_ac=props.get('third_ac', 0),
                sleeper=props.get('sleeper', 0),
                chair_car=props.get('chair_car', 0),
                first_class=props.get('first_class', 0),
                classes=props.get('classes', ''),
                geometry_coords=geom.get('coordinates') if geom else None
            )
            
            # Insert train
            cursor.execute("""
                INSERT OR IGNORE INTO trains 
                (number, name, from_station_code, to_station_code, from_station_name, 
                 to_station_name, zone, type, distance_km, duration_h, duration_m,
                 departure_time, arrival_time, return_train, first_ac, second_ac, 
                 third_ac, sleeper, chair_car, first_class, classes, properties_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                train.number, train.name, train.from_station_code, train.to_station_code,
                train.from_station_name, train.to_station_name, train.zone, train.train_type,
                train.distance_km, train.duration_h, train.duration_m, train.departure_time,
                train.arrival_time, train.return_train, train.first_ac, train.second_ac,
                train.third_ac, train.sleeper, train.chair_car, train.first_class,
                train.classes, json.dumps(props)
            ))
            
            # Get the train_id (need to re-query if INSERT OR IGNORE skipped)
            if cursor.lastrowid == 0:
                # Train already exists, get its ID
                cursor.execute("SELECT id FROM trains WHERE number = ?", (train.number,))
                result = cursor.fetchone()
                if result:
                    train_id = result[0]
                else:
                    continue  # Skip if can't find train
            else:
                train_id = cursor.lastrowid
            
            # Store geometry
            if train.geometry_coords:
                cursor.execute("""
                    INSERT INTO train_routes (train_id, geometry_type, coordinates_json)
                    VALUES (?, ?, ?)
                """, (train_id, 'LineString', json.dumps(train.geometry_coords)))
                
                # Map route to stations
                mapped_stations = self.map_route_to_stations(
                    train.number, 
                    train.geometry_coords
                )
                
                # Insert as train stops (will be refined by schedules later)
                for seq, (station_code, coord_idx) in enumerate(mapped_stations, start=1):
                    cursor.execute("""
                        INSERT OR IGNORE INTO train_stops 
                        (train_id, station_code, stop_sequence)
                        VALUES (?, ?, ?)
                    """, (train_id, station_code, seq))
            
            self.stats['trains_imported'] += 1
            
            # Commit every 1000 trains
            if self.stats['trains_imported'] % 1000 == 0:
                self.conn.commit()
        
        self.conn.commit()
        print(f"✓ Imported {self.stats['trains_imported']} trains")
    
    def import_schedules(self):
        """Import schedules from schedules.json (large file, streaming)."""
        print("\nImporting schedules...")
        schedules_file = self.data_dir / 'schedules.json'
        
        print(f"Reading large file: {schedules_file.name} ({schedules_file.stat().st_size / 1024 / 1024:.1f} MB)")
        
        # Load full file (streaming parse for very large files would use ijson)
        with open(schedules_file, 'r', encoding='utf-8') as f:
            schedules = json.load(f)
        
        print(f"Processing {len(schedules):,} schedule entries...")
        
        cursor = self.conn.cursor()
        
        # Group by train number
        from collections import defaultdict
        train_schedules = defaultdict(list)
        
        for schedule in tqdm(schedules, desc="Grouping schedules"):
            train_schedules[schedule['train_number']].append(schedule)
        
        print(f"Found schedules for {len(train_schedules)} trains")
        
        # Process each train's schedule
        for train_number, stops in tqdm(train_schedules.items(), desc="Processing train schedules"):
            # Get train_id
            cursor.execute("SELECT id FROM trains WHERE number = ?", (train_number,))
            result = cursor.fetchone()
            
            if not result:
                # Train not in database, skip
                continue
            
            train_id = result[0]
            
            # Sort stops by arrival/departure time and day
            # This is a simplification; real sorting needs time parsing
            # Handle None values in day field
            stops_sorted = sorted(stops, key=lambda s: (
                s.get('day') if s.get('day') is not None else 1,
                s.get('departure') if s.get('departure') is not None else '00:00:00'
            ))
            
            # Update or insert train stops with schedule data
            for seq, stop in enumerate(stops_sorted, start=1):
                cursor.execute("""
                    INSERT INTO train_stops 
                    (train_id, station_code, stop_sequence, arrival_time, departure_time, day_offset)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(train_id, stop_sequence) DO UPDATE SET
                        station_code = excluded.station_code,
                        arrival_time = excluded.arrival_time,
                        departure_time = excluded.departure_time,
                        day_offset = excluded.day_offset
                """, (
                    train_id,
                    stop['station_code'],
                    seq,
                    stop.get('arrival') if stop.get('arrival') != 'None' else None,
                    stop.get('departure') if stop.get('departure') != 'None' else None,
                    (stop.get('day') if stop.get('day') is not None else 1) - 1  # Convert to 0-based offset
                ))
                
                self.stats['stops_imported'] += 1
            
            # Commit every 100 trains
            if self.stats['stops_imported'] % 10000 == 0:
                self.conn.commit()
        
        self.conn.commit()
        print(f"✓ Imported {self.stats['stops_imported']:,} train stops")
    
    def create_sample_train_runs(self, days_ahead: int = 30):
        """Create sample train runs for the next N days."""
        print(f"\nCreating sample train runs for next {days_ahead} days...")
        
        cursor = self.conn.cursor()
        
        # Get all trains
        cursor.execute("SELECT id, number FROM trains")
        trains = cursor.fetchall()
        
        from datetime import date, timedelta
        today = date.today()
        
        for train_id, train_number in tqdm(trains, desc="Creating train runs"):
            for day_offset in range(days_ahead):
                run_date = today + timedelta(days=day_offset)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO train_runs (train_id, run_date, status, total_seats, available_seats)
                    VALUES (?, ?, 'SCHEDULED', 100, 100)
                """, (train_id, run_date.isoformat()))
        
        self.conn.commit()
        print(f"✓ Created train runs for {len(trains)} trains × {days_ahead} days")
    
    def generate_report(self):
        """Generate import statistics report."""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"Stations imported:           {self.stats['stations_imported']:,}")
        print(f"Stations with coordinates:   {self.stats['stations_with_coords']:,}")
        print(f"Trains imported:             {self.stats['trains_imported']:,}")
        print(f"Train stops imported:        {self.stats['stops_imported']:,}")
        print(f"Route coords mapped:         {self.stats['route_coords_mapped']:,}")
        print(f"Route coords unmapped:       {self.stats['route_coords_unmapped']:,}")
        
        if self.stats['route_coords_mapped'] + self.stats['route_coords_unmapped'] > 0:
            mapping_rate = 100 * self.stats['route_coords_mapped'] / (
                self.stats['route_coords_mapped'] + self.stats['route_coords_unmapped']
            )
            print(f"Mapping success rate:        {mapping_rate:.1f}%")
        
        # Check database stats
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mapping_warnings")
        warnings = cursor.fetchone()[0]
        print(f"Mapping warnings:            {warnings:,}")
        
        cursor.execute("SELECT COUNT(*) FROM train_runs")
        runs = cursor.fetchone()[0]
        print(f"Train runs created:          {runs:,}")
        
        print("="*60)
    
    def run_import(self, create_runs: bool = True):
        """Run complete import process."""
        start_time = time.time()
        
        try:
            self.connect()
            
            # Create schema
            schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
            self.create_schema(schema_path)
            
            # Import data
            self.import_stations()
            self.import_trains()
            self.import_schedules()
            
            if create_runs:
                self.create_sample_train_runs(days_ahead=30)
            
            # Generate report
            self.generate_report()
            
            elapsed = time.time() - start_time
            print(f"\n✓ Import completed in {elapsed:.1f} seconds")
            
        except Exception as e:
            print(f"\n✗ Error during import: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            self.close()


def main():
    """Main entry point."""
    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    db_path = project_root / 'database' / 'railway.db'
    
    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Railway Reservation System - Data Import")
    print("="*60)
    print(f"Data directory:  {data_dir}")
    print(f"Database:        {db_path}")
    print("="*60)
    
    # Run import
    importer = RailwayDatabaseImporter(str(db_path), str(data_dir))
    importer.run_import(create_runs=True)
    
    print("\n✓ All done! Database is ready at:", db_path)


if __name__ == '__main__':
    main()
