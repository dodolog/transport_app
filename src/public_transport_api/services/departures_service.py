from typing import Any, Dict, List, Optional
from datetime import datetime

from ..services.db import (
    get_conn,
    fetch_all_stops,
    fetch_upcoming_for_stop,
    fetch_next_stop_on_trip,
    fetch_last_stop_on_trip,
)
from ..services.geo import (
    haversine_m,
    initial_bearing_deg,
    angular_diff,
    iso_from_date_and_gtfs_time,
)

def _trip_is_heading_towards(conn, desired_bearing: float,
                             stop_lat: float, stop_lon: float,
                             trip_id: str, current_sequence: int,
                             direction_threshold_deg: float = 90.0) -> bool:
    """
    Szacujemy kierunek kursu jako bearing z bieżącego przystanku do kolejnego.
    Jeśli to ostatni przystanek, bierzemy bearing do przystanku końcowego.
    """
    nxt = fetch_next_stop_on_trip(conn, trip_id, current_sequence)
    if not nxt:
        nxt = fetch_last_stop_on_trip(conn, trip_id)
        if not nxt:
            return False

    brng_trip = initial_bearing_deg(stop_lat, stop_lon, nxt["stop_lat"], nxt["stop_lon"])
    return angular_diff(brng_trip, desired_bearing) <= direction_threshold_deg

def find_closest_departures(
    db_path: str,
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    start_dt_utc: datetime,
    limit: int,
) -> List[Dict[str, Any]]:
    """
    Zwraca listę odjazdów (max 'limit'), posortowanych wg odległości przystanku od miejsca startu.
    Filtrowane do kursów poruszających się w ogólnym kierunku do end_coordinates.
    """
    desired_bearing = initial_bearing_deg(start_lat, start_lon, end_lat, end_lon)
    gtfs_time_from = start_dt_utc.strftime("%H:%M:%S")

    with get_conn(db_path) as conn:
        # Wszystkie przystanki + dystans do startu
        stops = fetch_all_stops(conn)
        for st in stops:
            st["_distance_m"] = haversine_m(start_lat, start_lon, st["stop_lat"], st["stop_lon"])
        stops.sort(key=lambda s: s["_distance_m"])

        departures_out: List[Dict[str, Any]] = []
        MAX_STOPS_TO_SCAN = 200  # heurystyka

        for stop in stops[:MAX_STOPS_TO_SCAN]:
            if len(departures_out) >= limit:
                break

            upcoming = fetch_upcoming_for_stop(conn, stop["stop_id"], gtfs_time_from, limit_per_stop=10)

            for row in upcoming:
                if len(departures_out) >= limit:
                    break

                if not _trip_is_heading_towards(
                    conn=conn,
                    desired_bearing=desired_bearing,
                    stop_lat=stop["stop_lat"],
                    stop_lon=stop["stop_lon"],
                    trip_id=row["trip_id"],
                    current_sequence=row["stop_sequence"],
                    direction_threshold_deg=90.0
                ):
                    continue

                departures_out.append({
                    "trip_id": row["trip_id"],
                    "route_id": row["route_id"],
                    "trip_headsign": row["trip_headsign"],
                    "stop": {
                        "name": stop["stop_name"],
                        "coordinates": {
                            "latitude": round(float(stop["stop_lat"]), 6),
                            "longitude": round(float(stop["stop_lon"]), 6),
                        },
                        "arrival_time": iso_from_date_and_gtfs_time(start_dt_utc, row["arrival_time"]),
                        "departure_time": iso_from_date_and_gtfs_time(start_dt_utc, row["departure_time"]),
                    }
                })

        return departures_out
