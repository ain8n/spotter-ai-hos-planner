# Spotter AI — FMCSA Hours of Service (HOS) Trip Planner & ELD Daily Log Generator

A production-grade, full-stack commercial motor vehicle (CMV) trip planning platform built with **Django REST Framework** and **React (Vite)**. Designed specifically for property-carrying interstate truck drivers operating under the **70-hour / 8-day rolling HOS schedule** (49 CFR Part 395).

The application plans compliant routes, schedules all mandatory breaks, daily resets, fueling stops, and freight loading/unloading windows, renders an interactive Leaflet route map with turn-by-turn guidance, and dynamically generates official **FMCSA Form 395 Driver's Daily Log (ELD) sheets in vector SVG** with 100% mathematical accuracy.

---

## 🌟 Live Demo & Deployment

- **Live Production URL (HTTPS):** [https://fmcsa.mywire.org](https://fmcsa.mywire.org)
- **API Health Check Endpoint:** [https://fmcsa.mywire.org/api/health/](https://fmcsa.mywire.org/api/health/)
- **Trip Plan API Endpoint:** [https://fmcsa.mywire.org/api/trips/plan/](https://fmcsa.mywire.org/api/trips/plan/)
- **Geocoding & Autocomplete Endpoint:** [https://fmcsa.mywire.org/api/trips/geocode/?q=Chicago](https://fmcsa.mywire.org/api/trips/geocode/?q=Chicago)

---

## 📋 Main Features

### 1. FMCSA Hours of Service (HOS) Engine (49 CFR Part 395)
- **11-Hour Driving Limit**: Limits driving to a maximum of 11.0 cumulative hours between 10-hour consecutive off-duty rest periods.
- **14-Hour Duty Window**: Prohibits driving beyond the 14th consecutive hour from coming on duty. Off-duty breaks do not extend this window.
- **30-Minute Rest Break**: Enforces a 30-minute off-duty rest break before exceeding 8.0 cumulative driving hours.
- **10-Hour Consecutive Daily Rest**: Automatically schedules 10.0 consecutive hours of Sleeper Berth / Off Duty to reset both the 11-hour driving and 14-hour duty windows.
- **70-Hour / 8-Day Rolling Cycle**: Continuously computes rolling on-duty hours across an 8-consecutive-day window.
- **34-Hour Restart**: Schedules a 34.0 consecutive hour restart whenever remaining cycle hours are insufficient for the next driving shift, resetting cumulative cycle hours to 0.0.
- **Fueling Stops**: Schedules mandatory 30-minute on-duty fueling stops at or before every 1,000 miles.
- **Pickup & Drop-off Duty Time**: Allocates exactly 1.0 hour of On-Duty (not driving) time for cargo loading at pickup and 1.0 hour for unloading at drop-off.
- **Pre-Trip Safety Inspection**: Automatically logs 0.25 hours (15 minutes) on-duty before departure.

### 2. Form 395 Vector SVG Driver's Daily Log (ELD)
- **Exact Form 395 Standard Layout**: Faithfully generates 24.0-hour calendar day log sheets matching official DOT/FMCSA specifications.
- **4-Row Duty Grid**:
  1. *1. Off Duty*
  2. *2. Sleeper Berth*
  3. *3. Driving*
  4. *4. On Duty (Not Driving)*
- **Complete Time-Axis Headings**: 25-step header banner from `Mid-night` to `1` through `11`, `Noon`, `1` through `11`, to `Mid-night`, with a dedicated `Total Hours` column.
- **Mathematical Total Validation**: Every calendar day strictly sums to **24.00 total hours** across the 4 rows.
- **Remarks at Status Transitions**: City/town and State abbreviations recorded for every duty status change.
- **Complete 70-Hour / 8-Day Driver Recap Table**:
  - *Lines 3 & 4 On Duty today*
  - *Column A: Total hours on duty last 7 days including today*
  - *Column B: Total hours available tomorrow (70 minus A, or 70 after 34h restart)*
  - *Column C: Total hours on duty last 8 days including today*
- **Multi-Day Journey Splitting**: Slices trips across calendar midnight (00:00:00 to 24:00:00) with status continuity across days.
- **Interactive Pinch-to-Zoom & Pan**: Smooth mobile and desktop pan/zoom controls with 1-click full-sheet fit and SVG vector download/print.

### 3. Location & Timezone Intelligence
- **GPS Direct Routing**: When acquired via device geolocation, numeric coordinates are the sole source of truth for routing. The UI displays `"Your Location"` and routes directly from exact coordinates.
- **Manual Autocomplete Search**: Search any city, highway interchange, street address, or decimal coordinate using OpenStreetMap Nominatim and Photon.
- **Automatic Timezone Resolution**: Automatically resolves the IANA timezone (e.g., `America/New_York`, `America/Chicago`, `America/Denver`, `America/Los_Angeles`) based on origin coordinates, applying localized times across all stops, directions, and log sheets.

### 4. Interactive Map & Turn-by-Turn Guidance
- Built on Leaflet and OpenStreetMap tiles with highway routing via OSRM.
- Color-coded map markers for Start, Pickup, Drop-off, 30m Rest, Fuel, 10h Overnight, and 34h Restart.
- Full turn-by-turn driving directions, highway step instructions, cumulative mileage, and localized arrival/departure schedules.
- Desktop Fullscreen Map mode (`100vw × 100vh`) and responsive mobile navigation.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.13, Django 6.1, Django REST Framework, Gunicorn, Pytest, TimezoneFinder |
| **Frontend** | React 18, Vite, Lucide Icons, Leaflet, Pure CSS (No Tailwind/Bootstrap bloat) |
| **Routing & Geocoding** | OpenStreetMap Nominatim, Photon, OSRM, OpenRouteService API integration |
| **Deployment & Containers** | Docker, Docker Compose, Nginx, Let's Encrypt SSL |

---

## 📁 Project Folder Structure

```
.
├── Dockerfile                  # Multi-stage production container build
├── docker-compose.yml          # Production & local Docker compose configuration
├── .env.example                # Example environment variables template
├── .gitignore                  # Comprehensive Python, Django, React, Node exclusions
├── README.md                   # Complete project documentation
├── backend/                    # Django Backend Application
│   ├── manage.py
│   ├── pytest.ini              # Pytest configuration with DJANGO_SETTINGS_MODULE
│   ├── requirements.txt        # Backend dependencies
│   ├── config/                 # Django core project configuration
│   │   ├── asgi.py
│   │   ├── settings.py         # App settings, CORS, DRF, allowed hosts
│   │   ├── urls.py             # Root URL routing
│   │   └── wsgi.py
│   └── trips/                  # Main HOS application module
│       ├── apps.py
│       ├── serializers.py      # Input validation & carrier header serializers
│       ├── urls.py             # /api/trips/ endpoints
│       ├── views.py            # API views (plan, geocode, health)
│       ├── services/           # Decoupled business logic service layer
│       │   ├── hos/            # Pure Python HOS simulation engine
│       │   │   ├── constants.py
│       │   │   ├── engine.py   # Deterministic FMCSA simulation engine
│       │   │   └── recap.py    # 70-hour / 8-day rolling recap calculator
│       │   ├── logs/           # ELD Daily Log generators
│       │   │   ├── generator.py # Midnight slicer & 24h day structurer
│       │   │   └── svg_renderer.py # Form 395 vector SVG generator
│       │   ├── geocoding/      # Geocoding & timezone resolution
│       │   │   ├── geocoder.py
│       │   │   └── timezone.py # Coordinate to IANA timezone resolver
│       │   └── routing/        # Highway routing engine
│       │       └── router.py   # OSRM / ORS highway routing & fallback
│       └── tests/              # Automated test suite (21 test cases)
│           ├── test_api.py
│           ├── test_fmcsa_examples.py
│           ├── test_hos_engine.py
│           ├── test_log_generator.py
│           ├── test_recap.py
│           └── test_timezone.py
└── frontend/                   # React Frontend Application
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── public/                 # Favicons, Web Manifest, App Icons
    └── src/
        ├── App.jsx             # Main application orchestrator & tab routing
        ├── main.jsx            # React root with ErrorBoundary
        ├── index.css           # Modern responsive design & layout rules
        ├── api/                # Backend API client functions
        ├── components/         # Reusable React components
        │   ├── DailyLogViewer.jsx
        │   ├── MapView.jsx
        │   ├── PinchZoomSvgViewer.jsx
        │   ├── RouteDirections.jsx
        │   ├── TripForm.jsx
        │   └── TripSummary.jsx
        └── utils/              # Client-side formatters and timezone lookup
            ├── formatters.js
            └── timezone.js
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django secret key (set a secure key in production) |
| `DEBUG` | `True` | Django debug mode (`True` for dev, `False` for production) |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames |
| `CORS_ALLOW_ALL_ORIGINS` | `True` | Allow cross-origin requests from frontend |
| `ORS_API_KEY` | `""` (Optional) | OpenRouteService API key (fallback OSRM engine active by default) |
| `VITE_API_BASE_URL` | `/api` | Base API endpoint for the React frontend |

---

## 🚀 How to Run Locally

### Option A: Using Docker Compose (Fastest)

Prerequisites: [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/).

```bash
# 1. Clone repository
git clone <repository-url>
cd spotter-ai-hos-planner

# 2. Start all services
docker compose up --build

# 3. Open your browser
# Frontend & API available at: http://localhost:8000
```

---

### Option B: Running Backend & Frontend Manually

#### Backend Setup (Django)

Prerequisites: Python 3.10+ (Python 3.13 recommended).

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations (optional for stateless planner)
python manage.py migrate

# 5. Start Django development server
python manage.py runserver 0.0.0.0:8000
```
Backend API will be live at `http://localhost:8000/api/health/`.

#### Frontend Setup (React + Vite)

Prerequisites: Node.js 18+ and npm.

```bash
# 1. Open a new terminal and navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server
npm run dev

# 4. Open in browser: http://localhost:5173
```

---

## 📡 API Endpoints Reference

### 1. Health Check
- **`GET /api/health/`**
- Returns service status and current UTC timestamp.

### 2. Location Autocomplete & Geocoding
- **`GET /api/trips/geocode/?q={query}`**
- Returns a list of matched locations with display names, cities, states, and coordinates.

### 3. Trip Planning & ELD Generation
- **`POST /api/trips/plan/`**
- **Request Body:**
```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Atlanta, GA",
  "dropoff_location": "Miami, FL",
  "current_cycle_used_hrs": 20.0,
  "start_lat": 41.8781,
  "start_lng": -87.6298,
  "pickup_lat": 33.7490,
  "pickup_lng": -84.3880,
  "dropoff_lat": 25.7617,
  "dropoff_lng": -80.1918,
  "header_details": {
    "carrier_name": "US Freight Express LLC",
    "main_office_address": "100 Logistics Blvd, Indianapolis, IN 46204",
    "home_terminal_address": "450 Transport Way, Chicago, IL 60601",
    "driver_name": "John E. Doe",
    "driver_id": "DRV-84920",
    "truck_tractor_num": "T-804 (VIN: 1XKWD49X)",
    "trailer_num": "TR-5309 (IL Lic: 982-TRK)"
  }
}
```
- **Response Structure:**
```json
{
  "route": {
    "total_distance_miles": 1344.5,
    "total_driving_duration_hours": 24.45,
    "coordinates": [[-87.6298, 41.8781], ...]
  },
  "summary": {
    "total_distance_miles": 1344.5,
    "total_driving_hours": 24.45,
    "total_on_duty_hours": 26.70,
    "total_trip_duration_hours": 66.0,
    "rest_breaks_30m_count": 1,
    "fuel_stops_count": 1,
    "daily_rests_10h_count": 2,
    "restarts_34h_count": 0,
    "timezone": "America/Chicago"
  },
  "stops": [...],
  "timeline": [...],
  "instructions": [...],
  "logs": [
    {
      "day_number": 1,
      "date": "2026-10-02",
      "date_formatted": "10 / 02 / 2026",
      "totals": {
        "off_duty": 13.5,
        "sleeper_berth": 0.0,
        "driving": 8.5,
        "on_duty_not_driving": 2.0,
        "total_hours": 24.0
      },
      "recap": {
        "on_duty_today": 10.5,
        "column_a_last_7_days": 30.5,
        "column_b_available_tomorrow": 39.5,
        "column_c_last_8_days": 30.5
      },
      "svg_content": "<svg ...>...</svg>"
    }
  ]
}
```

---

## 🧪 Running Automated Tests

The backend test suite includes 21 comprehensive test cases validating HOS limit enforcement, 34-hour restarts, 1,000-mile fuel stops, Form 395 24-hour mathematical totals, 70-hour recap calculations, and coordinate timezone determination.

```bash
# Navigate to backend and run pytest
cd backend
PYTHONPATH=. pytest
```

### Test Suite Coverage:
- `backend/trips/tests/test_api.py` — API endpoints, input validation, and HTTP response codes.
- `backend/trips/tests/test_fmcsa_examples.py` — FMCSA guide sample scenarios.
- `backend/trips/tests/test_hos_engine.py` — 11h driving, 14h window, 30m breaks, 10h resets, 34h restarts.
- `backend/trips/tests/test_log_generator.py` — Midnight calendar day slicing and 24.00-hour status line invariants.
- `backend/trips/tests/test_recap.py` — 70-hour / 8-day rolling recap calculations (Columns A, B, C).
- `backend/trips/tests/test_timezone.py` — Geographic coordinate to IANA timezone resolution.

---

## 📜 Compliance & License

Built in strict adherence to:
- **Title 49 CFR Part 395** — Federal Motor Carrier Safety Regulations (FMCSR).
- **FMCSA Interstate Truck Driver's Guide to Hours of Service**.
- **FMCSA Form 395** Driver's Daily Log specification.

Licensed under the [MIT License](LICENSE).
