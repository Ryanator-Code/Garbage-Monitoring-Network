# Wireless Sensor Mesh Dashboard - API Specification

## Backend Server

**Base URL:** `http://10.0.0.234:5001`

---

## Endpoints

### 1. GET /dashboard
**Description:** Retrieve all sensor nodes in the network

**Response Format:**
```json
[
  {
    "name": "Kitchen Bin",
    "distance": 45.2,
    "battery": 4.8,
    "role": "HEAD",
    "chip_id": "EEFF"
  },
  {
    "name": "Living Room",
    "distance": 32.5,
    "battery": 4.6,
    "role": "WORKER",
    "chip_id": "AABB"
  }
]
```

**Fields:**
- `chip_id` (string): Last 4 hex chars of ESP32 MAC (extracted from POST data)
- `name` (string): Human-readable name (defaults to chip_id if unnamed)
- `distance` (float): Distance measurement in cm
- `battery` (float): Battery voltage (3.0–8.0V for 4-cell AA)
- `role` (string): Either `"HEAD"` or `"WORKER"`

---

### 2. GET /dashboard/:chip_id
**Description:** Get historical data for a specific sensor node

**Parameters:**
- `chip_id` (path): The node's chip ID (e.g., "EEFF")

**Response Format:**
```json
[
  {
    "timestamp": "2025-11-25 14:32:45",
    "distance": 45.2,
    "battery": 4.8
  },
  {
    "timestamp": "2025-11-25 14:32:40",
    "distance": 45.0,
    "battery": 4.8
  }
]
```

**Fields:**
- `timestamp` (string): Formatted as `YYYY-MM-DD HH:MM:SS`
- `distance` (float): Distance measurement in cm
- `battery` (float): Battery voltage

**Error (404):**
```json
{
  "error": "Node not found"
}
```

---

### 3. POST /dashboard/:chip_id
**Description:** Update sensor node's display name

**Parameters:**
- `chip_id` (path): The node's chip ID

**Request Body:**
```json
{
  "name": "New Sensor Name"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Node name updated",
  "chip_id": "EEFF",
  "name": "New Sensor Name"
}
```

**Error (404):**
```json
{
  "success": false,
  "error": "Node not found"
}
```

---

### 4. POST /api/data
**Description:** Receive sensor data batch from ESP32 mesh (called by firmware)

**Request Body:**
```json
[
  {
    "node_mac": "AA:BB:CC:DD:EE:FF",
    "distance": 45.2,
    "uptime_ms": 5000,
    "battery": 4.23,
    "role": "WORKER",
    "chipId": "EEFF"
  },
  {
    "node_mac": "11:22:33:44:55:66",
    "distance": 32.5,
    "uptime_ms": 5100,
    "battery": 3.98,
    "role": "WORKER",
    "chipId": "AABB"
  },
  {
    "node_mac": "AA:BB:CC:DD:EE:01",
    "distance": 38.75,
    "uptime_ms": 5200,
    "battery": 4.15,
    "role": "HEAD",
    "chipId": "EE01"
  }
]
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Processed 3 of 3 nodes",
  "processed": 3,
  "total": 3,
  "errors": null
}
```

**Required Fields:**
- `node_mac` (string): MAC address in format `XX:XX:XX:XX:XX:XX`
- `distance` (float): Ultrasonic sensor reading in cm
- `battery` (float): Battery voltage (V)
- `uptime_ms` (int): Time since cycle start in milliseconds
- `role` (string): `"HEAD"` or `"WORKER"`
- `chipId` (string): Last 4 hex chars of MAC (e.g., `"EEFF"`)

---

## Data Flow

### ESP32 → Backend (Firmware sends)
1. **Discovery + Election phase:** Nodes elect a HEAD node (highest RSSI)
2. **HEAD phase:** HEAD node collects sensor data from all WORKERS
3. **Upload phase:** HEAD connects to WiFi, POSTs batch data to `POST /api/data`
4. **Sleep phase:** All nodes sleep for `SLEEP_TIME_SEC` (default 5 seconds)
5. Repeat

### Backend → Frontend (Dashboard polls)
1. **Node list:** Frontend polls `GET /dashboard` every 3 seconds
2. **Node history:** When node selected, frontend polls `GET /dashboard/:chip_id` every 2 seconds
3. **Network topology:** Frontend automatically renders mesh based on `role` field

---

## Notes for Frontend

- **Hardcoded IP:** Backend is at `10.0.0.234:5001` (no dynamic discovery)
- **Polling intervals:** Adjust in `src/api.js` if needed
- **Node identification:** Use `chip_id` as primary key, not `node_mac`
- **Battery display:** Raw voltage, not percentage (typically 4.0–6.0V for healthy 4-cell AA)
- **Timestamp format:** Provided by backend as `YYYY-MM-DD HH:MM:SS` (local server time)
- **Error handling:** No mock data fallback; empty arrays on API failure

---

## Frontend Configuration

Update `src/api.js` if backend IP changes:

```javascript
const API_BASE_URL = 'http://10.0.0.234:5001';
```

All endpoints are relative to this base URL.
