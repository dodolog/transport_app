
# services/geo.py
import math
from datetime import datetime, timezone
from typing import Tuple

def parse_coords(s: str) -> Tuple[float, float]:
    try:
        lat_s, lon_s = s.split(",", 1)
        lat, lon = float(lat_s.strip()), float(lon_s.strip())
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
        return lat, lon
    except Exception:
        raise ValueError("Coordinates must be in format 'lat,lon' with valid ranges.")

def parse_iso8601_or_now(s: str | None) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(s)
        return dt.astimezone(timezone.utc)
    except Exception:
        raise ValueError("start_time must be ISO 8601, e.g., 2025-04-02T08:30:00Z")

def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def initial_bearing_deg(lat1, lon1, lat2, lon2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlmb = math.radians(lon2 - lon1)
    x = math.sin(dlmb) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlmb)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0

def angular_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d

def iso_from_date_and_gtfs_time(date_utc: datetime, gtfs_time: str) -> str:
    """
    Skleja datę ze start_time z czasem GTFS (HH:MM:SS).
    Uwaga: brak wsparcia dla godzin >= 24 (jeśli feed je stosuje – dodaj obsługę dobowego rollovera).
    """
    hh, mm, ss = [int(x) for x in gtfs_time.split(":")]
    dt = datetime(
        year=date_utc.year, month=date_utc.month, day=date_utc.day,
        hour=hh, minute=mm, second=ss, tzinfo=timezone.utc
    )
    return dt.isoformat().replace("+00:00", "Z")
