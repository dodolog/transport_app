
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Jeśli chcesz, możesz wynieść time helper do utils/timefmt.py
def iso_from_date_and_gtfs_time(date_utc: datetime, gtfs_time: str) -> str:
    """
    Łączy datę (UTC) z czasem GTFS HH:MM:SS do ISO 8601, np. 2025-04-02T08:34:00Z.
    Uwaga: jeśli feed używa godzin >= 24 (np. 25:10:00), dodaj rollover dnia.
    """
    hh, mm, ss = [int(x) for x in gtfs_time.split(":")]
    dt = datetime(
        year=date_utc.year, month=date_utc.month, day=date_utc.day,
        hour=hh, minute=mm, second=ss, tzinfo=timezone.utc
    )
    return dt.isoformat().replace("+00:00", "Z")


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = _dict_factory
    return conn


def get_trip_details(
    trip_id: str,
    db_path: str = "trips.sqlite",
    date_utc: datetime = None
) -> Optional[Dict[str, Any]]:
    """
    Zwraca szczegóły kursu o danym trip_id:
    {
        "trip_id": ...,
        "route_id": ...,
        "trip_headsign": ...,
        "stops": [
            {
                "name": ...,
                "coordinates": {"latitude": float, "longitude": float},
                "arrival_time": ISO8601,
                "departure_time": ISO8601
            }, ...
        ]
    }
    Jeśli nie znaleziono kursu -> None.

    :param trip_id: identyfikator kursu z tabeli trips
    :param db_path: ścieżka do pliku SQLite (domyślnie 'trips.sqlite')
    :param date_utc: data, której użyjemy do złożenia ISO 8601 z czasów GTFS (domyślnie dziś w UTC)
    """
    if not trip_id or not isinstance(trip_id, str):
        raise ValueError("Invalid trip_id")

    if date_utc is None:
        date_utc = datetime.now(timezone.utc)

    # Połącz się z DB
    with _get_conn(db_path) as conn:
        # 1) Pobierz trip (route_id, trip_headsign)
        trip_row = conn.execute(
            """
            SELECT trip_id, route_id, trip_headsign
            FROM trips
            WHERE trip_id = ?
            """,
            (trip_id,),
        ).fetchone()

        if trip_row is None:
            # Brak kursu o tym trip_id
            return None

        # 2) Pobierz przystanki w kolejności stop_sequence, z czasami i współrzędnymi
        stop_rows = conn.execute(
            """
            SELECT
                st.stop_sequence,
                st.arrival_time,
                st.departure_time,
                s.stop_name,
                s.stop_lat,
                s.stop_lon
            FROM stop_times st
            JOIN stops s ON s.stop_id = st.stop_id
            WHERE st.trip_id = ?
            ORDER BY st.stop_sequence ASC
            """,
            (trip_id,),
        ).fetchall()

        # 3) Zbuduj listę stops
        stops_out: List[Dict[str, Any]] = []
        for st in stop_rows:
            stops_out.append({
                "name": st["stop_name"],
                "coordinates": {
                    "latitude": round(float(st["stop_lat"]), 6),
                    "longitude": round(float(st["stop_lon"]), 6),
                },
                "arrival_time": iso_from_date_and_gtfs_time(date_utc, st["arrival_time"]),
                "departure_time": iso_from_date_and_gtfs_time(date_utc, st["departure_time"]),
            })

        return {
            "trip_id": trip_row["trip_id"],
            "route_id": trip_row["route_id"],
            "trip_headsign": trip_row["trip_headsign"],
            "stops": stops_out
        }
