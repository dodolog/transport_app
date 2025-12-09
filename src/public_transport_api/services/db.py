import sqlite3
from typing import Any, Dict, List, Optional, Tuple

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    return conn

def fetch_all_stops(conn) -> List[Dict[str, Any]]:
    sql = """
        SELECT stop_id, stop_name, stop_lat, stop_lon
        FROM stops
    """
    return conn.execute(sql).fetchall()

def fetch_upcoming_for_stop(conn, stop_id: str, time_str: str, limit_per_stop: int = 10) -> List[Dict[str, Any]]:
    sql = """
    SELECT
        st.trip_id,
        st.arrival_time,
        st.departure_time,
        st.stop_sequence,
        t.route_id,
        t.trip_headsign
    FROM stop_times st
    JOIN trips t ON t.trip_id = st.trip_id
    WHERE st.stop_id = ?
      AND st.departure_time >= ?
    ORDER BY st.departure_time ASC
    LIMIT ?
    """
    return conn.execute(sql, (stop_id, time_str, limit_per_stop)).fetchall()

def fetch_next_stop_on_trip(conn, trip_id: str, after_sequence: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT st.stop_id, st.stop_sequence, s.stop_lat, s.stop_lon
    FROM stop_times st
    JOIN stops s ON s.stop_id = st.stop_id
    WHERE st.trip_id = ?
      AND st.stop_sequence > ?
    ORDER BY st.stop_sequence ASC
    LIMIT 1
    """
    return conn.execute(sql, (trip_id, after_sequence)).fetchone()

def fetch_last_stop_on_trip(conn, trip_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT st.stop_id, st.stop_sequence, s.stop_lat, s.stop_lon
    FROM stop_times st
    JOIN stops s ON s.stop_id = st.stop_id
    WHERE st.trip_id = ?
    ORDER BY st.stop_sequence DESC
    LIMIT 1
    """
    return conn.execute(sql, (trip_id,)).fetchone()
