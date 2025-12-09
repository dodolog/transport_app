from flask import Flask
from flask_cors import CORS

import sys

from public_transport_api.controllers.trips_controller import trips_bp
from public_transport_api.controllers.departures_controller import departures_bp


sys.path.append("..")


app = Flask(__name__)


# Konfiguracja
app.config["DB_PATH"] = "gtfs_database.db"
app.config["SUPPORTED_CITIES"] = {"wroclaw"}

CORS(app)

app.register_blueprint(departures_bp)
app.register_blueprint(trips_bp)


@app.route("/")
def index():
    return "Welcome to the Public Transport API for Wrocław!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)