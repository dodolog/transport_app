import sqlite3

from flask import Blueprint, current_app, jsonify, request

from ..services.departures_service import find_closest_departures
from ..services import geo

departures_bp = Blueprint('departures', __name__, url_prefix='/public_transport/city/<string:city>/closest_departures')

#
# http://localhost:5000/public_transport/city/Wroclaw/closest_departures?start_coordinates=51.11618980246768,17.034468173747534&end_coordinates=51.11247527875757,17.030530373185027&start_time=2025-12-09T14:11:00.000Z&limit=5
#
@departures_bp.route("/", methods=["GET"])
def closest_departures(city: str):
    try:
        # 404 gdy miasto nieobsługiwane
        supported = current_app.config.get("SUPPORTED_CITIES", set())
        if city.lower() not in supported:
            return jsonify({"error": "City not supported"}), 404

        # Pobranie i walidacja parametrów zapytania
        start_coordinates = request.args.get("start_coordinates", type=str)
        end_coordinates = request.args.get("end_coordinates", type=str)
        start_time_raw = request.args.get("start_time", type=str)
        limit = request.args.get("limit", default=5, type=int)

        if not start_coordinates or not end_coordinates:
            return jsonify({"error": "Missing required parameters: start_coordinates, end_coordinates"}), 400
        if limit is None or limit <= 0 or limit > 50:
            return jsonify({"error": "limit must be an integer in 1..50"}), 400

        start_lat, start_lon = geo.parse_coords(start_coordinates)
        end_lat, end_lon = geo.parse_coords(end_coordinates)
        start_dt_utc = geo.parse_iso8601_or_now(start_time_raw)

        # Złożenie listy odjazdów (serwis)
        departures = find_closest_departures(
            db_path=current_app.config["DB_PATH"],
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            start_dt_utc=start_dt_utc,
            limit=limit,
        )

        # self URL (z zachowaniem query string)
        qs = request.query_string.decode("utf-8") if request.query_string else ""
        self_path = request.path + (("?" + qs) if qs else "")

        # Odpowiedź wg specyfikacji
        resp = {
            "metadata": {
                "self": self_path,
                "city": city.lower(),
                "query_parameters": {
                    "start_coordinates": f"{start_lat},{start_lon}",
                    "end_coordinates": f"{end_lat},{end_lon}",
                    "start_time": start_dt_utc.isoformat().replace("+00:00", "Z"),
                    "limit": limit
                }
            },
            "departures": departures
        }
        return jsonify(resp), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except sqlite3.Error as se:
        return jsonify({"error": f"Database error: {str(se)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
