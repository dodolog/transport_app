// --- 1. Leaflet Map Initialization ---
const map = L.map('map').setView([51.1079, 17.0385], 13); // Centered on Wroclaw

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// --- 2. Global Variables for Points and Markers ---
let startPoint = null;
let destinationPoint = null;
let startMarker = null;
let destinationMarker = null;
let activeRoutePolyline = null;
let activeRouteStopMarkers = [];
let currentStopMarkers = []; // To store markers for search results

let settingStart = true; // Flag to determine which point is being set

// --- 3. DOM Elements ---
const startPointDisplay = document.getElementById('startPointDisplay');
const destinationPointDisplay = document.getElementById('destinationPointDisplay');
const setStartBtn = document.getElementById('setStartBtn');
const setDestinationBtn = document.getElementById('setDestinationBtn');
const departureTimeInput = document.getElementById('departureTime');
const findDeparturesBtn = document.getElementById('findDeparturesBtn');
const resultsList = document.getElementById('results-list');
const loadingIndicator = document.getElementById('loading-indicator');

// --- 4. Helper Functions ---

// Function to calculate distance between two lat/lng points (Haversine formula)
function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // metres
    const φ1 = lat1 * Math.PI / 180; // φ, λ in radians
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // in metres
}

// Function to format coordinates
function formatCoords(latlng) {
    return `Lat: ${latlng.lat.toFixed(5)}, Lng: ${latlng.lng.toFixed(5)}`;
}

// Function to set default departure time to now
function setDefaultDepartureTime() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset()); // Adjust for timezone
    departureTimeInput.value = now.toISOString().slice(0, 16);
}

// --- 5. Map Interaction ---

map.on('click', function(e) {
    if (settingStart) {
        if (startMarker) {
            map.removeLayer(startMarker);
        }
        startPoint = e.latlng;
        startMarker = L.marker(startPoint, {
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: '<div style="background-color:#007bff; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">S</div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(map).bindPopup('Start Point').openPopup();
        startPointDisplay.textContent = formatCoords(startPoint);
        setStartBtn.textContent = 'Change Start Point (Click Map)';
    } else {
        if (destinationMarker) {
            map.removeLayer(destinationMarker);
        }
        destinationPoint = e.latlng;
        destinationMarker = L.marker(destinationPoint, {
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: '<div style="background-color:#dc3545; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">D</div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(map).bindPopup('Destination Point').openPopup();
        destinationPointDisplay.textContent = formatCoords(destinationPoint);
        setDestinationBtn.textContent = 'Change Destination Point (Click Map)';
    }
});

setStartBtn.addEventListener('click', () => {
    settingStart = true;
    setStartBtn.style.backgroundColor = '#0056b3'; // Highlight active button
    setDestinationBtn.style.backgroundColor = '#28a745';
});

setDestinationBtn.addEventListener('click', () => {
    settingStart = false;
    setDestinationBtn.style.backgroundColor = '#0056b3'; // Highlight active button
    setStartBtn.style.backgroundColor = '#28a745';
});


// --- 6. Simulated API Data (Wroclaw Public Transport) ---
// This data simulates a small subset of Wroclaw's public transport system.
// Coordinates are approximate for demonstration.

const mockStops = [
    { id: 'stop1', name: 'Plac Grunwaldzki', lat: 51.1105, lng: 17.0601 },
    { id: 'stop2', name: 'Most Grunwaldzki', lat: 51.1090, lng: 17.0490 },
    { id: 'stop3', name: 'Galeria Dominikańska', lat: 51.1070, lng: 17.0390 },
    { id: 'stop4', name: 'Renoma', lat: 51.1000, lng: 17.0270 },
    { id: 'stop5', name: 'Arkady Capitol', lat: 51.0980, lng: 17.0290 },
    { id: 'stop6', name: 'Dworzec Główny (Main Station)', lat: 51.0995, lng: 17.0360 },
    { id: 'stop7', name: 'Opera', lat: 51.1030, lng: 17.0300 },
    { id: 'stop8', name: 'Rynek', lat: 51.1100, lng: 17.0320 }, // Near Rynek
    { id: 'stop9', name: 'Uniwersytet', lat: 51.1130, lng: 17.0340 },
    { id: 'stop10', name: 'Katedra', lat: 51.1120, lng: 17.0460 }, // Ostrów Tumski area
    { id: 'stop11', name: 'Politechnika Wrocławska', lat: 51.1070, lng: 17.0660 },
    { id: 'stop12', name: 'Biskupin', lat: 51.1070, lng: 17.0850 },
    { id: 'stop13', name: 'ZOO', lat: 51.1050, lng: 17.0760 },
    { id: 'stop14', name: 'Hala Stulecia', lat: 51.1060, lng: 17.0780 },
    { id: 'stop15', name: 'Krzyki', lat: 51.0700, lng: 17.0100 }, // Further south
    { id: 'stop16', name: 'Powstańców Śląskich', lat: 51.0900, lng: 17.0200 },
    { id: 'stop17', name: 'FAT', lat: 51.0800, lng: 16.9900 },
    { id: 'stop18', name: 'Kwiska', lat: 51.1200, lng: 16.9800 }, // Further west
];

const mockRoutes = {
    // Route 1: Plac Grunwaldzki -> Galeria Dominikańska -> Dworzec Główny
    'route_A': {
        geometry: [
            [51.1105, 17.0601], [51.1090, 17.0490], [51.1070, 17.0390], [51.1030, 17.0300], [51.0995, 17.0360]
        ],
        stops: ['Plac Grunwaldzki', 'Most Grunwaldzki', 'Galeria Dominikańska', 'Opera', 'Dworzec Główny (Main Station)']
    },
    // Route 2: Dworzec Główny -> Renoma -> Arkady Capitol -> Powstańców Śląskich
    'route_B': {
        geometry: [
            [51.0995, 17.0360], [51.1000, 17.0270], [51.0980, 17.0290], [51.0900, 17.0200]
        ],
        stops: ['Dworzec Główny (Main Station)', 'Renoma', 'Arkady Capitol', 'Powstańców Śląskich']
    },
    // Route 3: Uniwersytet -> Rynek -> Galeria Dominikańska -> Katedra
    'route_C': {
        geometry: [
            [51.1130, 17.0340], [51.1100, 17.0320], [51.1070, 17.0390], [51.1120, 17.0460]
        ],
        stops: ['Uniwersytet', 'Rynek', 'Galeria Dominikańska', 'Katedra']
    },
    // Route 4: Politechnika -> ZOO -> Hala Stulecia -> Biskupin
    'route_D': {
        geometry: [
            [51.1070, 17.0660], [51.1050, 17.0760], [51.1060, 17.0780], [51.1070, 17.0850]
        ],
        stops: ['Politechnika Wrocławska', 'ZOO', 'Hala Stulecia', 'Biskupin']
    },
    // Route 5: Dworzec Główny -> Plac Grunwaldzki -> Politechnika
    'route_E': {
        geometry: [
            [51.0995, 17.0360], [51.1090, 17.0490], [51.1105, 17.0601], [51.1070, 17.0660]
        ],
        stops: ['Dworzec Główny (Main Station)', 'Most Grunwaldzki', 'Plac Grunwaldzki', 'Politechnika Wrocławska']
    }
};

// Function to generate mock departures for a given time
function generateMockDepartures(baseTime) {
    const departures = [];
    const lines = ['1', '2', '3', '4', '5', '6', '7', '10', '14', '20', 'A', 'N', '106', '122', '148'];
    const headsigns = [
        'Krzyki', 'Biskupin', 'Poświętne', 'Leśnica', 'Stadion Wrocław',
        'Zajezdnia Gaj', 'Sępolno', 'Oporów', 'Kleczków', 'Dworzec Główny',
        'Plac Grunwaldzki', 'Galeria Dominikańska', 'Rynek', 'FAT', 'Kwiska'
    ];
    const routeIds = Object.keys(mockRoutes);

    mockStops.forEach(stop => {
        // Generate 1-3 departures per stop
        const numDepartures = Math.floor(Math.random() * 3) + 1;
        for (let i = 0; i < numDepartures; i++) {
            const departureTime = new Date(baseTime.getTime() + (i * 5 + Math.floor(Math.random() * 3)) * 60 * 1000); // 5-8 min apart
            departures.push({
                stop_id: stop.id,
                line: lines[Math.floor(Math.random() * lines.length)],
                headsign: headsigns[Math.floor(Math.random() * headsigns.length)],
                departure_time: departureTime.toISOString(),
                route_id: routeIds[Math.floor(Math.random() * routeIds.length)] // Assign a random route
            });
        }
    });
    return departures;
}

// --- 7. Main Search Logic (Simulated API Call) ---
async function findNearestDepartures() {
    if (!startPoint) {
        alert('Please select a Start Point on the map.');
        return;
    }

    loadingIndicator.style.display = 'block';
    findDeparturesBtn.disabled = true;
    resultsList.innerHTML = '<li>Searching for departures...</li>';
    clearMapMarkersAndRoutes(); // Clear previous results on map

    const selectedTime = new Date(departureTimeInput.value);
    const mockDepartures = generateMockDepartures(selectedTime); // Generate fresh departures

    const MAX_DISTANCE_KM = 1; // Search radius
    const results = {}; // Group departures by stop

    mockStops.forEach(stop => {
        const distance = getDistance(startPoint.lat, startPoint.lng, stop.lat, stop.lng);
        if (distance <= MAX_DISTANCE_KM * 1000) { // Convert KM to meters
            const relevantDepartures = mockDepartures.filter(dep =>
                dep.stop_id === stop.id &&
                new Date(dep.departure_time) >= selectedTime
            ).sort((a, b) => new Date(a.departure_time) - new Date(b.departure_time)); // Sort by time

            if (relevantDepartures.length > 0) {
                results[stop.id] = {
                    stop: stop,
                    departures: relevantDepartures
                };
            }
        }
    });

    displayResults(results);

    loadingIndicator.style.display = 'none';
    findDeparturesBtn.disabled = false;
}

// --- 8. Display Results ---

function clearMapMarkersAndRoutes() {
    currentStopMarkers.forEach(marker => map.removeLayer(marker));
    currentStopMarkers = [];
    if (activeRoutePolyline) {
        map.removeLayer(activeRoutePolyline);
        activeRoutePolyline = null;
    }
    activeRouteStopMarkers.forEach(marker => map.removeLayer(marker));
    activeRouteStopMarkers = [];
}

function displayResults(results) {
    resultsList.innerHTML = ''; // Clear previous results

    const stopIds = Object.keys(results);

    if (stopIds.length === 0) {
        resultsList.innerHTML = '<li>No departures found within 1km of your start point for the selected time.</li>';
        return;
    }

    stopIds.forEach(stopId => {
        const stopData = results[stopId].stop;
        const departures = results[stopId].departures;

        // Create a marker for the stop
        const stopMarker = L.marker([stopData.lat, stopData.lng], {
            icon: L.divIcon({
                className: 'custom-stop-icon',
                html: `<div style="background-color:#007bff; width: 25px; height: 25px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.8em;">${stopData.name.charAt(0)}</div>`,
                iconSize: [25, 25],
                iconAnchor: [12, 12]
            })
        }).addTo(map);
        currentStopMarkers.push(stopMarker);

        // ⭐ Bonus Point I: Group multiple results in the same popup
        let popupContent = `<strong>${stopData.name}</strong><br><small>Departures:</small><br>`;
        departures.forEach(dep => {
            const depTime = new Date(dep.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            popupContent += `<p><span class="line">${dep.line}</span> to <span class="headsign">${dep.headsign}</span> at <span class="time">${depTime}</span></p>`;
        });
        stopMarker.bindPopup(popupContent);

        // Add results to the list
        departures.forEach(dep => {
            const listItem = document.createElement('li');
            listItem.classList.add('result-item');
            listItem.dataset.routeId = dep.route_id; // Store route_id for Bonus II
            listItem.dataset.stopId = dep.stop_id; // Store stop_id for highlighting

            const depTime = new Date(dep.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            listItem.innerHTML = `
                <p><strong>${stopData.name}</strong></p>
                <p><span class="line">${dep.line}</span> to <span class="headsign">${dep.headsign}</span></p>
                <p>Departure: <span class="time">${depTime}</span></p>
            `;
            resultsList.appendChild(listItem);

            // ⭐ Bonus Point II: Display route on click
            listItem.addEventListener('click', () => {
                // Clear previous selection and route
                document.querySelectorAll('.result-item').forEach(item => item.classList.remove('selected'));
                if (activeRoutePolyline) {
                    map.removeLayer(activeRoutePolyline);
                    activeRoutePolyline = null;
                }
                activeRouteStopMarkers.forEach(marker => map.removeLayer(marker));
                activeRouteStopMarkers = [];

                // Mark current item as selected
                listItem.classList.add('selected');

                const routeId = listItem.dataset.routeId;
                const route = mockRoutes[routeId];

                if (route && route.geometry) {
                    activeRoutePolyline = L.polyline(route.geometry, { color: '#007bff', weight: 5, opacity: 0.7 }).addTo(map);
                    map.fitBounds(activeRoutePolyline.getBounds()); // Zoom to route

                    // Add markers for stops along the route
                    route.stops.forEach((stopName, index) => {
                        // Find the actual stop object to get its coordinates
                        const routeStop = mockStops.find(s => s.name === stopName);
                        if (routeStop) {
                            const routeStopMarker = L.marker([routeStop.lat, routeStop.lng], {
                                icon: L.divIcon({
                                    className: 'custom-route-stop-icon',
                                    html: `<div style="background-color:#6c757d; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.7em;">${index + 1}</div>`,
                                    iconSize: [20, 20],
                                    iconAnchor: [10, 10]
                                })
                            }).addTo(map).bindPopup(`<strong>${stopName}</strong><br>Stop on route ${dep.line}`);
                            activeRouteStopMarkers.push(routeStopMarker);
                        }
                    });
                } else {
                    console.warn(`Route geometry not found for route_id: ${routeId}`);
                }
            });
        });
    });
}


// --- 9. Event Listeners and Initial Setup ---
findDeparturesBtn.addEventListener('click', findNearestDepartures);

// Set default time on load
setDefaultDepartureTime();
