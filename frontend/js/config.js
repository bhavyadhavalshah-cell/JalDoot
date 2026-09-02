// JalDoot Frontend Configuration
const CONFIG = {
  API_BASE_URL: window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
    ? window.location.origin + "/api"
    : "/api",
  DEFAULT_LAT: 21.63, // Porbandar / Gujarat coastal baseline
  DEFAULT_LON: 69.60,
  GPS_POLL_INTERVAL_MS: 15000, // 15s
  ADMIN_POLL_INTERVAL_MS: 5000, // 5s
  MAP_TILE_LAYER: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  MAP_ATTRIBUTION: "JalDoot Marine Safety"
};
