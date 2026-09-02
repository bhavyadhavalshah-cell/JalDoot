# JalDoot — Machhuaare Ka Saathi , Samundar Ka Saarthi 🌊⚓

**JalDoot** is an advanced, zero-cost, full-stack marine safety and oceanographic advisory system designed for artisanal fishermen, coastal communities, marine researchers, and Coast Guard / Disaster Management authorities.

---

## 🌟 Key Capabilities & Features

### 1. 🚨 Real-Time Automated SOS Email Alerting
- **Automated Dispatch to Command Email**: Whenever a fisherman activates an SOS emergency beacon, an automated alert email is sent in real time to **`jaldootprojectsih@gmail.com`**.
- **Real-Time Payload**:
  - Fisherman Name & Registered Contact
  - Vessel Registration Number & Model
  - Exact GPS Latitude & Longitude
  - Direct One-Click **Google Maps Navigation Link** (`https://www.google.com/maps?q=lat,lon`)
  - Accurate Indian Standard Time (IST) Timestamp
  - Automatic fleet broadcast notifying all vessels within a 20 km radius.

### 2. 🗺️ 80 High-Density Sea-Only PFZ Zones (Gujarat, Maharashtra & Goa)
- **100% Waterbody & Oceanic Placement**: Comprehensive catalog of **80 Potential Fishing Zones (PFZs)** situated strictly in the marine waters and continental shelf of **Gujarat, Maharashtra, and Goa** with **zero land overlap**.
- **Large-Scale Oceanic Fronts**: High fish frequency with radii up to **22.0 km** (e.g. *Mumbai High Pelagic Ridge (22 km)*, *Angria Bank Coral Shelf (22 km)*, *Porbandar Deep Trench (18.5 km)*, *Jakhau Deep Shelf (18 km)*, *Goa Offshore Pelagic Ridge (20 km)*).
- **Interactive Map vs. Nearest 5 List**:
  - **Fisherman Portal Map**: Renders all active regional PFZ zones in the sea for total navigational situational awareness.
  - **Fisherman Portal Sidebar / List**: Strictly calculates and displays **only the nearest 5 PFZ zones** relative to the fisherman's live GPS coordinates, complete with direct compass bearing lines, distances in km & NM, estimated travel time, and target fish catch.
  - **Admin Command Portal Map**: Renders all **80 PFZ zones** across Gujarat, Maharashtra, and Goa in waterbodies simultaneously, giving commanders a complete multi-state marine operational picture.

### 3. 🤖 Simple, Location-Aware Multilingual AI Marine Chatbot
- **Location Intelligence across 3 States**: Recognizes any coastal town, harbor, or landing center across **Gujarat, Maharashtra, and Goa** in English, Gujarati (ગુજરાતી), or Hindi (हिन्दी) (e.g. *Dwarka, Veraval, Porbandar, Okha, Diu, Surat, Mumbai, Sassoon Dock, Ratnagiri, Malvan, Panaji, Vasco, Canacona*, etc.).
- **Simple, Jargon-Free Fisherman Language**: Formulates natural, conversational harbor advice tailored for local fishermen (eliminating complex terms like *chlorophyll concentration contours* or *bathymetric depths*).
- **Strict Non-Marine Query Rejection**: Off-topic inquiries (e.g. stocks, general knowledge, cricket, jokes) are politely filtered out with instructions to ask only relevant sea and marine questions.
- **Real-Time Timestamps**: Live IST timestamps (`hh:mm:ss A IST`) displayed on every fisherman inquiry and AI advisory bubble.

### 4. 🧭 Coastal vs. Non-Coastal Safe to Sail Score
- **Coastal & Marine Regions**: Computes a real-time 0–100 **Safe to Sail Score** based on live Open-Meteo wave swell, wind velocity, and database hazard zones.
- **Inland / Non-Coastal Regions**: Automatically detects when a device is located inland (>50 km from coast) and displays a dashed score (`--`) with a **"Non-Coastal Region"** badge.

### 5. 🚢 Scaled Fleet Management (2,500 Fishermen Dataset)
- **Fleet Scale**: Seeded database with **2,500 registered fishing vessels** and live telemetry pings for over 1,600 active boats in the Arabian Sea.
- **Admin Priority Sorting**: The Disaster Command fleet table strictly orders vessels as:
  1. **🚨 SOS Distress Ships (First Priority)**
  2. **🟢 Active Telemetry Ships**
  3. **⚪ Inactive Ships**

---

## 🎨 UI Semantic Design Palette

- **Brand / Primary Blue**: `#087E8B` (Buttons, headers, active markers)
- **Teal Accent Light**: `#DDF7EC` (Pills, badges, background highlights)
- **Teal Accent Dark**: `#0F7A6A` (Status text, active links)
- **Canvas Background**: `#F4F7F6` (App backdrop)
- **Surface Background**: `#FFFFFF` (Cards, panels, modals)
- **Bot Bubble Background**: `#EFF6F7` (AI assistant speech bubbles)
- **Border Light**: `#BAE6E8` (Card dividers, input strokes)
- **Text Primary**: `#1E293B` & **Text Muted**: `#64748B`
- **Marker Amber**: `#E07A5F` (Potential Fishing Zones) & **Marker Red**: `#D9383A` (Hazard Sectors / SOS Signals)

---

## 🛠️ Technology Stack (100% Free Tier, Zero Cost)

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3, Leaflet.js (Marine Mapping), Chart.js (Oceanographic Simulator), Web Speech API.
- **Backend**: Python 3.10+ with FastAPI, Uvicorn, SQLAlchemy, PyJWT, Passlib, Bcrypt.
- **Database**: Local SQLite database (`jaldoot.db`) with automatic schema creation and fallback support.
- **Live APIs**:
  - **Open-Meteo Marine & Weather API**: Real-time wave swell, wind velocity, and sea temperature (Free, no API key required).
  - **FormSubmit HTTPS Dispatcher**: Real-time automated email delivery to `jaldootprojectsih@gmail.com`.

---

## 🚀 How to Run the Project (Step-by-Step Terminal Commands)

### 📋 Prerequisites
- **Python 3.10 or higher** installed on your system. Verify with:
  ```bash
  python --version
  ```

---

### Option A: One-Click Startup (Recommended)

1. Open your terminal / PowerShell in the `jal-doot` project root directory:
   ```bash
   cd jal-doot
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the one-click launcher:
   ```bash
   python run.py
   ```

4. Open your web browser and visit:
   🌐 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

### Option B: Manual Step-by-Step Startup

If you prefer starting the backend and database manually from the terminal:

1. **Navigate to the Backend Directory**:
   ```bash
   cd jal-doot/backend
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Seed the Database** (Initializes 2,500 fishermen, admin account, and 20 hazard sectors):
   ```bash
   python seed_data.py
   ```

4. **Launch the FastAPI & Frontend Server**:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Access the Application**:
   Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

### 🧪 Running the Verification Test Suite

To run the automated maritime verification test suite (validates SOS email delivery, nearest 5 PFZ zones, location chatbot, coastal score detection, and fleet sorting):

```bash
cd jal-doot/backend
python test_suite.py
```

---

## 🔑 Demo Login Credentials (Instant Access — Zero GPS Permission Prompts)

> **💡 Zero-Prompt State Coastal Access**: When logging in with any of the 3 state demo accounts or the Admin account, the app **never asks for browser location access**. Each demo account is pre-anchored to its state's coastal marine waters, immediately initializing live weather, nearest 5 PFZ zones, safe to sail scores, and localized AI advice.

| State / Role | Username | Password | Default Coastal Location | Default Language | Destination Portal |
|---|---|---|---|---|---|
| **Gujarat Coast** 📍 | `gujarat_fisherman` | `password1234` | **Porbandar / Veraval** (`21.64, 69.60`) | Gujarati (ગુજરાતી) | **Fisherman Portal** |
| **Maharashtra Coast** 📍 | `maharashtra_fisherman` | `password1234` | **Mumbai / Sassoon Dock** (`18.92, 72.83`) | Hindi (हिन्दी) | **Fisherman Portal** |
| **Goa Coast** 📍 | `goa_fisherman` | `password1234` | **Panaji / Aguada** (`15.49, 73.82`) | English | **Fisherman Portal** |
| **Disaster Command Admin** 🛡️ | `admin@gmail.com` | `admin1234` | **Arabian Sea Command Center** | English | **Admin Fleet Operations** |
| **Active SOS Demo Vessel** 🚨 | `bhavesh_patel` | `password1234` | **Porbandar Sea Trench** | Gujarati | **Fisherman Portal (Active SOS)** |

---

## 📂 Project Directory Structure

```
jal-doot/
├── backend/
│   ├── app/
│   │   ├── config.py             # Configuration & environment loader
│   │   ├── database.py           # SQLAlchemy SQLite database connector
│   │   ├── models.py             # User, GPSPing, SOSAlert, ChatMessage, HazardZone models
│   │   ├── schemas.py            # Pydantic schemas for requests and responses
│   │   ├── auth.py               # JWT tokens, password hashing, role-based guards
│   │   ├── main.py               # FastAPI application entry point & static routes
│   │   ├── routers/
│   │   │   ├── auth_routes.py    # Login, registration, token validation
│   │   │   ├── weather_routes.py # Marine weather & coastal score endpoint
│   │   │   ├── pfz_routes.py     # 80 Sea-Only PFZ zones & Nearest 5 recommendation endpoint
│   │   │   ├── sos_routes.py     # SOS trigger & email dispatch
│   │   │   ├── chat_routes.py    # Multilingual conversational AI endpoint
│   │   │   ├── gps_routes.py     # Real-time GPS ping handler
│   │   │   ├── admin_routes.py   # Fleet priority sorting & disaster management
│   │   │   ├── researcher_routes.py # Oceanographic historical datasets
│   │   │   └── hazard_routes.py  # Maritime hazard zones
│   │   └── services/
│   │       ├── email_service.py  # Real SOS email dispatcher (jaldootprojectsih@gmail.com)
│   │       ├── weather_service.py# Coastal proximity check & Safe to Sail score
│   │       ├── gemini_service.py # Gujarat/MH/Goa location database & simple AI chatbot
│   │       ├── sms_service.py    # Emergency SMS broadcast service
│   │       └── alert_service.py  # Geofencing & proximity calculation
│   ├── jaldoot.db                # SQLite database
│   ├── seed_data.py              # Seeder for 2,500 fishermen & master data
│   ├── test_suite.py             # Automated maritime verification suite
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # Environment configuration
├── frontend/
│   ├── index.html                # Single-Page Application (SPA) shell
│   ├── css/
│   │   └── styles.css            # Responsive layout & custom property styling
│   ├── js/
│   │   ├── config.js             # API base URL & global configuration
│   │   ├── i18n.js               # Gujarati, Hindi, English translations
│   │   ├── storage.js            # Offline IndexedDB storage manager
│   │   ├── auth.js               # Session state & authentication handlers
│   │   ├── map.js                # Leaflet.js tactical & navigational maps
│   │   ├── fisherman.js          # Weather card, nearest 5 PFZ list, real-time chat, SOS modal
│   │   ├── researcher.js         # Oceanographic trends & What-If simulator
│   │   ├── admin.js              # Real-time fleet monitor & all-PFZ command map
│   │   └── app.js                # App bootstrap & network monitors
│   ├── sw.js                     # Offline Service Worker
│   └── manifest.json             # PWA Web App Manifest
├── run.py                        # One-click startup runner
└── README.md                     # Comprehensive project documentation
```

---

## 🛡️ License & Acknowledgements
- Developed for the **Smart India Hackathon (SIH)**.
- Integrates live meteorological telemetry from **Open-Meteo** and oceanographic PFZ modeling based on **ISRO Oceansat-3 OCM-3 & INCOIS** advisory parameters.

