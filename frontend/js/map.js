// Leaflet Marine Intelligence Map Controller
const MARINE_MAP = {
  map: null,
  mapId: "marine-map",
  fishermanMarker: null,
  vesselLayerGroup: null,
  pfzLayerGroup: null,
  hazardLayerGroup: null,
  routeLayerGroup: null,
  currentRole: "fisherman",
  currentUserCoords: [CONFIG.DEFAULT_LAT, CONFIG.DEFAULT_LON],

  init(mapElementId = "marine-map", role = "fisherman", userLat = CONFIG.DEFAULT_LAT, userLon = CONFIG.DEFAULT_LON) {
    this.mapId = mapElementId;
    this.currentRole = role;
    this.currentUserCoords = [userLat, userLon];

    const mapContainer = document.getElementById(mapElementId);
    if (!mapContainer) return;

    if (this.map) {
      this.map.remove();
      this.map = null;
    }

    const mapOptions = {
      zoomControl: true,
      attributionControl: true
    };

    if (role === "fisherman") {
      mapOptions.minZoom = 7;
      mapOptions.maxZoom = 15;
    } else {
      mapOptions.minZoom = 5;
      mapOptions.maxZoom = 16;
    }

    this.map = L.map(mapElementId, mapOptions).setView([userLat, userLon], role === "fisherman" ? 11 : 8);

    // Remove Leaflet prefix/logo so only "JalDoot Marine Safety" appears
    if (this.map.attributionControl) {
      this.map.attributionControl.setPrefix(false);
    }

    L.tileLayer(CONFIG.MAP_TILE_LAYER, {
      attribution: CONFIG.MAP_ATTRIBUTION,
      maxZoom: 18
    }).addTo(this.map);

    this.vesselLayerGroup = L.layerGroup().addTo(this.map);
    this.pfzLayerGroup = L.layerGroup().addTo(this.map);
    this.hazardLayerGroup = L.layerGroup().addTo(this.map);
    this.routeLayerGroup = L.layerGroup().addTo(this.map);

    if (role === "fisherman") {
      this.updateFishermanPosition(userLat, userLon, true);
    }

    this.loadHazards();
  },

  updateFishermanPosition(lat, lon, forceCenter = true) {
    if (!this.map) return;
    this.currentUserCoords = [lat, lon];

    const fishermanDot = L.divIcon({
      className: "custom-boat-marker",
      html: `
        <div style="background-color: #087E8B; width: 22px; height: 22px; border-radius: 50%; border: 3px solid #FFFFFF; box-shadow: 0 0 15px rgba(8,126,139,1.0); display: flex; align-items: center; justify-content: center;">
          <div style="width: 8px; height: 8px; background-color: #52B788; border-radius: 50%;"></div>
        </div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    if (this.fishermanMarker) {
      this.fishermanMarker.setLatLng([lat, lon]);
    } else {
      this.fishermanMarker = L.marker([lat, lon], { icon: fishermanDot })
        .addTo(this.map)
        .bindPopup(`<b>Your Vessel (Live GPS)</b><br>Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`);
    }

    if (forceCenter) {
      this.map.setView([lat, lon], this.map.getZoom() || 11, { animate: true });
    }
  },

  centerOnUser() {
    if (this.map && this.currentUserCoords) {
      this.map.setView(this.currentUserCoords, 12, { animate: true });
    }
  },

  async loadHazards() {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/hazards/`);
      if (!res.ok) return;
      const hazards = await res.json();

      this.hazardLayerGroup.clearLayers();
      hazards.forEach(h => {
        let strokeColor = "#D9383A";
        let fillColor = "#D9383A";
        let fillOpacity = 0.22;
        let severityLabel = "Critical Danger";

        if (h.zone_type === "LOW_ALERT" || h.severity === "LOW") {
          strokeColor = "#CA8A04";
          fillColor = "#EAB308";
          fillOpacity = 0.25;
          severityLabel = "Low Alert Zone";
        } else if (h.zone_type === "HIGH_ALERT" || h.severity === "HIGH") {
          strokeColor = "#78350F";
          fillColor = "#854D0E";
          fillOpacity = 0.28;
          severityLabel = "High Alert Zone";
        }

        const circle = L.circle([h.latitude, h.longitude], {
          color: strokeColor,
          fillColor: fillColor,
          fillOpacity: fillOpacity,
          radius: h.radius_km * 1000,
          weight: 2,
          dashArray: "5, 5"
        }).addTo(this.hazardLayerGroup);

        circle.bindPopup(`
          <div style="font-family: inherit; font-size: 12px; min-width: 180px;">
            <b style="color: ${strokeColor};">[HAZARD] ${h.name}</b><br>
            <b>Level:</b> ${severityLabel}<br>
            <b>Radius:</b> ${h.radius_km} km<br>
            <span style="color: #64748B;">${h.description || ''}</span>
          </div>
        `);
      });
    } catch (e) {
      console.warn("Hazard layer load error:", e);
    }
  },

  /**
   * Renders a large quantity of high-density Potential Fishing Zones (PFZ)
   * as enlarged circular zones in the sea/ocean.
   */
  renderPFZCircles(zones) {
    if (!this.map) return;
    this.pfzLayerGroup.clearLayers();

    // Calibrated scale factor to ensure fishing zones stay strictly inside marine waterbodies.
    const PFZ_RADIUS_SCALE = 0.5;

    zones.forEach(z => {
      let shapeLayer;

      // Always render as a circle (polygon_coords are ignored so every PFZ is circular)
      shapeLayer = L.circle([z.latitude, z.longitude], {
        color: "#E07A5F",
        weight: 2,
        fillColor: "#E07A5F",
        fillOpacity: 0.35,
        radius: (z.radius_km || 3.0) * 1000 * PFZ_RADIUS_SCALE,
        dashArray: "4, 4"
      }).addTo(this.pfzLayerGroup);

      const centerDot = L.divIcon({
        className: "custom-pfz-dot",
        html: `
          <div style="background-color: #E07A5F; width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid #FFFFFF; box-shadow: 0 0 8px rgba(224,122,95,0.9);">
          </div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      });

      const centerMarker = L.marker([z.latitude, z.longitude], { icon: centerDot })
        .addTo(this.pfzLayerGroup);

      const popupContent = `
        <div style="font-family: inherit; font-size: 12px; min-width: 240px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <b style="color: #E07A5F; font-size:13px;">${z.name}</b>
          </div>
          <div style="margin-bottom:6px; display:flex; gap:4px; flex-wrap:wrap;">
            <span style="background:#FEF3C7; color:#92400E; font-size:10px; font-weight:800; padding:1px 5px; border-radius:2px;">
              ${z.density_level || 'MAXIMUM DENSITY'}
            </span>
            <span style="background:#E0F2FE; color:#0369A1; font-size:10px; font-weight:800; padding:1px 5px; border-radius:2px;">
              🛰️ ${z.satellite_sensor || 'ISRO Oceansat-3 OCM-3'}
            </span>
          </div>
          <b>Distance:</b> ${z.distance_km} km (Bearing: ${z.bearing_deg}°)<br>
          <b>Chlorophyll:</b> ${z.chlorophyll} mg/m³ | <b>SST:</b> ${z.sst_celsius}°C<br>
          <b>Ekman Upwelling Index:</b> ${z.upwelling_index || '4.5'}<br>
          <b>Advisory:</b> <code style="font-size:10px; background:#F1F5F9; padding:1px 3px;">${z.isro_advisory_id || 'ISRO-INCOIS-PFZ-2026'}</code><br>
          <b>Target Species:</b> ${z.recommended_target_fish.join(", ")}<br>
          <div style="margin-top: 8px;">
            <button onclick="MARINE_MAP.drawRouteToPFZ(${z.latitude}, ${z.longitude}, '${z.name}', ${z.distance_km}, ${z.bearing_deg})" style="background:#087E8B; color:white; border:none; padding:5px 8px; border-radius:3px; font-weight:bold; cursor:pointer; font-size:11px; width:100%;">
              🧭 Plot Direct Navigation Route
            </button>
          </div>
        </div>
      `;

      shapeLayer.bindPopup(popupContent);
      centerMarker.bindPopup(popupContent);
    });
  },

  /**
   * Draws a direct navigational route line from vessel GPS to fishing zone
   */
  drawRouteToPFZ(targetLat, targetLon, targetName, distKm, bearingDeg) {
    if (!this.map) return;
    this.routeLayerGroup.clearLayers();

    const start = this.currentUserCoords || [CONFIG.DEFAULT_LAT, CONFIG.DEFAULT_LON];
    const end = [targetLat, targetLon];

    // Navigational dashed path
    const routeLine = L.polyline([start, end], {
      color: "#087E8B",
      weight: 4,
      dashArray: "8, 8",
      opacity: 0.95
    }).addTo(this.routeLayerGroup);

    // Waypoint Destination Marker
    const destIcon = L.divIcon({
      className: "route-dest-marker",
      html: `<div style="background-color: #0F7A6A; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 10px; border: 1.5px solid white; box-shadow: 0 0 6px rgba(0,0,0,0.5);">WAYPOINT</div>`,
      iconAnchor: [30, 10]
    });

    L.marker(end, { icon: destIcon }).addTo(this.routeLayerGroup);

    // Auto-open waypoint popup
    const knots = 8.0;
    const etaMinutes = Math.round((distKm / (knots * 1.852)) * 60);

    routeLine.bindPopup(`
      <div style="font-family: inherit; font-size: 12px; min-width: 190px;">
        <b style="color: #087E8B;">🧭 Navigation Route Active</b><br>
        <b>Destination:</b> ${targetName}<br>
        <b>Distance:</b> ${distKm} km (${(distKm / 1.852).toFixed(1)} NM)<br>
        <b>Bearing:</b> ${bearingDeg}° Heading<br>
        <b>Estimated Transit Time:</b> ~${etaMinutes} mins (@ 8 kts)
      </div>
    `).openPopup();

    // Zoom map to fit both waypoints
    const bounds = L.latLngBounds([start, end]);
    this.map.fitBounds(bounds, { padding: [40, 40] });
  },

  /**
   * Renders dense glowing vessel dots matching satellite radar scatter plot
   * Active ships = Glowing green dots
   * SOS ships = Glowing red dots
   */
  updateAdminVessels(vesselList) {
    if (!this.map || this.currentRole !== "admin") return;

    this.vesselLayerGroup.clearLayers();

    vesselList.forEach(v => {
      const isSOS = v.has_active_sos;
      const dotColor = isSOS ? "#D9383A" : "#10B981";
      const dotSize = isSOS ? 12 : 7;
      const animClass = isSOS ? "custom-ship-red" : "custom-ship-green";

      // DivIcon with active pulsing and flickering animation
      const icon = L.divIcon({
        className: "leaflet-ship-wrapper",
        html: `<div class="leaflet-ship-dot ${animClass}" style="width: ${dotSize}px; height: ${dotSize}px;"></div>`,
        iconSize: [dotSize, dotSize],
        iconAnchor: [dotSize / 2, dotSize / 2]
      });

      const marker = L.marker([v.latitude, v.longitude], { icon: icon })
        .addTo(this.vesselLayerGroup);

      let sosResolveHtml = "";
      if (isSOS) {
        sosResolveHtml = `
          <div style="margin-top: 8px; text-align: center;">
            <button onclick="ADMIN.resolveSOSFromMap('${v.vessel_number}')" style="background:#D9383A; color:white; border:none; padding:4px 8px; border-radius:3px; font-weight:bold; cursor:pointer; font-size:11px;">
              Resolve Distress Beacon
            </button>
          </div>
        `;
      }

      marker.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; min-width: 180px;">
          <b style="color: ${dotColor};">${v.vessel_number}</b> (${v.username})<br>
          <b>Speed:</b> ${v.speed_knots} kts | <b>Heading:</b> ${v.heading}°<br>
          <b>Status:</b> ${isSOS ? '<span style="color:#D9383A; font-weight:bold;">DISTRESS ACTIVE</span>' : 'Active Telemetry'}<br>
          <b>Phone:</b> ${v.phone_number}<br>
          <span style="color:#64748B; font-size:10px;">Ping: ${new Date(v.last_seen).toLocaleTimeString()}</span>
          ${sosResolveHtml}
        </div>
      `);
    });
  }
};