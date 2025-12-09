
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timezone
import sqlite3

# Ważne: nazwa modułu musi się zgadzać z plikiem (trips_service.py vs trips_services.py)
from ..services.trips_service import get_trip_details

trips_bp = Blueprint('trips', __name__, url_prefix='/public_transport/city/<string:city>/trip')

@trips_bp.route("/<string:trip_id>", methods=["GET"])
def handle_trip_details(city: str, trip_id: str):
    try:
        supported = current_app.config.get("SUPPORTED_CITIES", {"wroclaw"})
        if city.lower() not in supported:
            return jsonify({"error": "City not supported"}), 404

        if not trip_id:
            return jsonify({"error": "Invalid trip_id"}), 400

        # Przekaż ścieżkę do DB z konfiguracji aplikacji (nie twardo kodowane 'trips.sqlite')
        db_path = current_app.config.get("DB_PATH", "trips.sqlite")
        date_utc = datetime.now(timezone.utc)

        details = get_trip_details(trip_id=trip_id, db_path=db_path, date_utc=date_utc)
        if details is None:
            return jsonify({"error": "Trip not found"}), 404

        qs = request.query_string.decode("utf-8") if request.query_string else ""
        self_path = request.path + (("?" + qs) if qs else "")

        return jsonify({
            "metadata": {
                "self": self_path,
                "city": city.lower(),
                "trip_id": trip_id
            },
            "trip_details": details
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except sqlite3.Error as se:
        return jsonify({"error": f"Database error: {str(se)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
