// Admin / Disaster Management Dashboard Controller
const ADMIN = {
  pollInterval: null,
  qaInterval: null,
  activityInterval: null,
  sosInterval: null,
  activeSOSList: [],
  demoTriggered: false,
  currentSubView: "command-subview", // "command-subview" or "researcher-subview"
  simulatedActivities: [
    { type: "LOGIN", title: "ACCESS: coastal_unit_dwarka", desc: "Role: HARBOR_OPERATOR | Interface: Desktop", coord: "N/A" },
    { type: "NETWORK", title: "TELEMETRY: IND-GJ-0012 (Veraval)", desc: "ONLINE - GPS Telemetry sync active @ 8.2 kts", coord: "[20.750, 70.180]" },
    { type: "NETWORK", title: "TELEMETRY: IND-MH-0008 (Mumbai High)", desc: "ONLINE - Pelagic sensor telemetry verified", coord: "[19.250, 71.950]" },
    { type: "LOGIN", title: "ACCESS: mrcc_mumbai_cmd", desc: "Role: SEARCH_AND_RESCUE | Interface: Desktop", coord: "N/A" },
    { type: "NETWORK", title: "TELEMETRY: IND-GA-0004 (Panaji)", desc: "ONLINE - High-frequency AIS pulse received", coord: "[15.480, 73.520]" },
    { type: "NETWORK", title: "TELEMETRY: IND-GJ-0019 (Porbandar)", desc: "ONLINE - Navigation ping @ 7.5 kts (Heading 215°)", coord: "[21.520, 69.450]" },
    { type: "LOGIN", title: "ACCESS: coastguard_okha", desc: "Role: PATROL_COMMAND | Interface: Desktop", coord: "N/A" }
  ],
  simActIndex: 0,

  async init() {
    if (!AUTH.isAdmin()) return;

    this.setupSubNavTabs();

    // Trigger initial demo data automatically on admin load
    if (!this.demoTriggered) {
      this.demoTriggered = true;
      try {
        await fetch(`${CONFIG.API_BASE_URL}/admin/trigger-demo-data`, {
          method: "POST",
          headers: AUTH.getAuthHeaders()
        });
      } catch (e) {
        console.warn("Initial admin data trigger error:", e);
      }
    }

    await this.refreshAdminData();

    // Initialize embedded Researcher Mode (Dual charts)
    RESEARCHER.init();

    // Regular polling
    if (this.pollInterval) clearInterval(this.pollInterval);
    this.pollInterval = setInterval(() => {
      this.refreshAdminData();
    }, CONFIG.ADMIN_POLL_INTERVAL_MS);

    // Start live auto-simulation streams automatically for all admin sessions
    this.setupAutoLiveStreams();
  },

  /**
   * Continuous Live Generators for Admin Command:
   * - Recent operations & logins added every 10 seconds with live real-time timestamp
   * - Inquiries & AI advisories stream every 10 seconds with live real-time timestamp
   * - SOS distress checks/alerts every 5 minutes
   */
  setupAutoLiveStreams() {
    if (this.qaInterval) clearInterval(this.qaInterval);
    if (this.activityInterval) clearInterval(this.activityInterval);
    if (this.sosInterval) clearInterval(this.sosInterval);

    // 1. Live Fisherman Inquiries & AI Advisories Every 10 Seconds
    this.qaInterval = setInterval(async () => {
      try {
        await fetch(`${CONFIG.API_BASE_URL}/admin/trigger-demo-data`, {
          method: "POST",
          headers: AUTH.getAuthHeaders()
        });
        const msgsRes = await fetch(`${CONFIG.API_BASE_URL}/admin/last-messages`, {
          headers: AUTH.getAuthHeaders()
        });
        if (msgsRes.ok) {
          const msgs = await msgsRes.json();
          this.renderUnifiedMessages(msgs);
        }
      } catch (e) {
        console.warn("10s QA stream error:", e);
      }
    }, 10000);

    // 2. New Activity Added to Recent Operations & Logins Every 10 Seconds (with live real time)
    this.activityInterval = setInterval(async () => {
      try {
        const feedRes = await fetch(`${CONFIG.API_BASE_URL}/admin/recent-activity`, {
          headers: AUTH.getAuthHeaders()
        });
        let feed = [];
        if (feedRes.ok) {
          feed = await feedRes.json();
        }

        // Add a live real-time event to top of feed every 10 seconds
        const sim = this.simulatedActivities[this.simActIndex % this.simulatedActivities.length];
        this.simActIndex++;

        const now = new Date();
        const liveRealTime = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST';

        feed.unshift({
          type: sim.type,
          title: sim.title,
          description: sim.desc,
          coordinates: sim.coord,
          status: "ACTIVE",
          real_time: liveRealTime,
          timestamp: now.toISOString()
        });

        this.renderActivityFeed(feed);
      } catch (e) {
        console.warn("10s activity stream error:", e);
      }
    }, 10000);

    // 3. SOS Alerts Refresh Every 5 Minutes
    this.sosInterval = setInterval(async () => {
      try {
        const sosRes = await fetch(`${CONFIG.API_BASE_URL}/sos/active`, {
          headers: AUTH.getAuthHeaders()
        });
        if (sosRes.ok) {
          this.activeSOSList = await sosRes.json();
          this.renderSOSAlerts(this.activeSOSList);
        }
      } catch (e) {
        console.warn("5min SOS stream error:", e);
      }
    }, 300000);
  },

  // In-place sub-view tab switcher
  setupSubNavTabs() {
    const btnCommand = document.getElementById("admin-tab-command");
    const btnResearch = document.getElementById("admin-tab-research");
    const viewCommand = document.getElementById("admin-command-subview");
    const viewResearch = document.getElementById("admin-research-subview");

    if (btnCommand && btnResearch && viewCommand && viewResearch) {
      btnCommand.addEventListener("click", () => {
        this.currentSubView = "command-subview";
        btnCommand.classList.add("active");
        btnResearch.classList.remove("active");
        viewCommand.style.display = "block";
        viewResearch.style.display = "none";
      });

      btnResearch.addEventListener("click", () => {
        this.currentSubView = "researcher-subview";
        btnResearch.classList.add("active");
        btnCommand.classList.remove("active");
        viewCommand.style.display = "none";
        viewResearch.style.display = "block";
        RESEARCHER.init();
      });
    }
  },

  async refreshAdminData() {
    try {
      // 1. Fetch Stats
      const statsRes = await fetch(`${CONFIG.API_BASE_URL}/admin/dashboard-stats`, {
        headers: AUTH.getAuthHeaders()
      });
      if (statsRes.ok) {
        const stats = await statsRes.json();
        this.renderStats(stats);
      }

      // 2. Fetch Active Vessels
      const vesselsRes = await fetch(`${CONFIG.API_BASE_URL}/admin/active-vessels`, {
        headers: AUTH.getAuthHeaders()
      });
      if (vesselsRes.ok) {
        const vessels = await vesselsRes.json();
        MARINE_MAP.updateAdminVessels(vessels);
        this.renderVesselsTable(vessels);
      }

      // 3. Render ALL constant Sea PFZ zones on Admin Command Map across Gujarat, Maharashtra, and Goa
      const pfzRes = await fetch(`${CONFIG.API_BASE_URL}/pfz/all?lat=20.00&lon=71.00`);
      if (pfzRes.ok) {
        const pfzData = await pfzRes.json();
        MARINE_MAP.renderPFZCircles(pfzData);
      }

      // 4. Fetch Recent Activity Feed
      const feedRes = await fetch(`${CONFIG.API_BASE_URL}/admin/recent-activity`, {
        headers: AUTH.getAuthHeaders()
      });
      if (feedRes.ok) {
        const feed = await feedRes.json();
        this.renderActivityFeed(feed);
      }

      // 5. Fetch Unified Q&A Stream
      const msgsRes = await fetch(`${CONFIG.API_BASE_URL}/admin/last-messages`, {
        headers: AUTH.getAuthHeaders()
      });
      if (msgsRes.ok) {
        const msgs = await msgsRes.json();
        this.renderUnifiedMessages(msgs);
      }

      // 6. Fetch Active SOS Alerts
      const sosRes = await fetch(`${CONFIG.API_BASE_URL}/sos/active`, {
        headers: AUTH.getAuthHeaders()
      });
      if (sosRes.ok) {
        this.activeSOSList = await sosRes.json();
        this.renderSOSAlerts(this.activeSOSList);
      }
    } catch (e) {
      console.warn("Admin polling refresh error:", e);
    }
  },

  renderStats(stats) {
    const elReg = document.getElementById("stat-total-vessels");
    const elLive = document.getElementById("stat-live-vessels");
    const elSos = document.getElementById("stat-active-sos");
    const elHazards = document.getElementById("stat-active-hazards");

    if (elReg) elReg.textContent = stats.total_registered_vessels;
    if (elLive) elLive.textContent = stats.live_active_vessels;
    if (elSos) elSos.textContent = stats.active_sos_alerts;
    if (elHazards) elHazards.textContent = stats.active_hazard_zones;
  },

  renderVesselsTable(vesselList) {
    const tbody = document.getElementById("admin-vessels-tbody");
    if (!tbody) return;

    if (!vesselList || vesselList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No vessels transmitting telemetry.</td></tr>`;
      return;
    }

    tbody.innerHTML = vesselList.slice(0, 50).map(v => {
      let statusBadge = "";
      if (v.has_active_sos || v.status === "SOS") {
        statusBadge = `<span style="background:#FEE2E2; color:#D9383A; font-weight:800; padding:2px 7px; border-radius:3px; font-size:11px; border:1px solid #FECACA;">🚨 DISTRESS (SOS)</span>`;
      } else if (v.is_active || v.status === "ACTIVE") {
        statusBadge = `<span style="background:#DDF7EC; color:#0F7A6A; font-weight:800; padding:2px 7px; border-radius:3px; font-size:11px; border:1px solid #A7F3D0;">🟢 ACTIVE (${v.speed_knots || 7.5} kts)</span>`;
      } else {
        statusBadge = `<span style="background:#F1F5F9; color:#64748B; font-weight:700; padding:2px 7px; border-radius:3px; font-size:11px; border:1px solid #E2E8F0;">⚪ INACTIVE (Port/Anchored)</span>`;
      }

      const rowStyle = (v.has_active_sos || v.status === "SOS") ? `style="background: rgba(254, 226, 226, 0.25);"` : "";

      return `
        <tr ${rowStyle}>
          <td><b>${v.vessel_number}</b></td>
          <td>${v.username}</td>
          <td>${v.latitude.toFixed(3)}, ${v.longitude.toFixed(3)}</td>
          <td>${statusBadge}</td>
          <td><small style="font-weight:700; color:var(--text-primary);">${v.last_seen || (new Date().toLocaleTimeString('en-IN') + ' IST')}</small></td>
        </tr>
      `;
    }).join("");
  },

  renderActivityFeed(feed) {
    const container = document.getElementById("admin-activity-feed");
    if (!container) return;

    if (!feed || feed.length === 0) {
      container.innerHTML = `<p style="font-size:0.8rem; color:var(--text-muted);">No recent logs recorded.</p>`;
      return;
    }

    container.innerHTML = feed.slice(0, 25).map(item => {
      let feedClass = "feed-item";
      if (item.type === "SOS") feedClass += " feed-sos";

      const timeDisplay = item.real_time || new Date(item.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST';

      return `
        <div class="${feedClass}">
          <div style="display:flex; justify-content:space-between; font-weight:700;">
            <span>${item.title}</span>
            <span style="font-size:0.7rem; color:var(--text-muted);">${timeDisplay}</span>
          </div>
          <div style="margin-top:2px;">${item.description}</div>
          <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Coord: ${item.coordinates}</div>
        </div>
      `;
    }).join("");
  },

  renderUnifiedMessages(unifiedList) {
    const container = document.getElementById("admin-last-messages");
    if (!container) return;

    if (!unifiedList || unifiedList.length === 0) {
      container.innerHTML = `<p style="font-size:0.8rem; color:var(--text-muted);">No queries recorded.</p>`;
      return;
    }

    container.innerHTML = unifiedList.map(item => {
      const timeDisplay = new Date(item.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' IST';
      return `
        <div class="unified-qa-card">
          <div class="unified-qa-header">
            <span>${item.fisherman_name} (${item.vessel_number})</span>
            <span>${timeDisplay}</span>
          </div>
          <div class="unified-qa-query">
            <b>Query:</b> "${item.question}"
          </div>
          <div class="unified-qa-answer">
            <b>JalDoot Advisory:</b> ${item.answer}
          </div>
        </div>
      `;
    }).join("");
  },

  renderSOSAlerts(alerts) {
    const container = document.getElementById("admin-sos-list");
    if (!container) return;

    const activeList = (alerts || []).filter(a => a.status === "ACTIVE");
    if (activeList.length === 0) {
      container.innerHTML = `<p style="font-size:0.82rem; color:var(--teal-accent-dark); font-weight:bold;">All distress beacons resolved. No active distress signals.</p>`;
      return;
    }

    container.innerHTML = activeList.map(a => {
      let dispatchDetails = "";
      if (a.notified_vessels_json) {
        try {
          const dInfo = JSON.parse(a.notified_vessels_json);
          dispatchDetails = `
            <div style="font-size:0.74rem; color:var(--text-muted); margin-top:4px;">
              <b>Broadcast Mode:</b> ${dInfo.dispatch_mode} (${dInfo.count || 0} ships notified)
            </div>
          `;
        } catch (e) {
          // Ignore json parse error
        }
      }

      return `
        <div class="card" id="sos-alert-card-${a.id}" style="border-left: 4px solid var(--marker-red); margin-bottom: 8px; padding: 10px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <h4 style="color:var(--marker-red); font-size:0.88rem; font-weight:800;">
                DISTRESS: ${a.vessel_number} — ${a.fisherman_name}
              </h4>
              <p style="font-size:0.78rem; margin-top:3px;"><b>Nature of Emergency:</b> ${a.details || a.emergency_type}</p>
              <p style="font-size:0.74rem; color:var(--text-muted); margin-top:2px;">
                <b>Coordinates:</b> [${a.latitude.toFixed(4)}, ${a.longitude.toFixed(4)}] | 
                <b>Received:</b> ${new Date(a.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} IST
              </p>
              ${dispatchDetails}
            </div>
            <div>
              <button onclick="ADMIN.resolveSOS(${a.id})" class="btn-danger" style="padding:4px 8px; font-size:0.74rem; cursor:pointer;">
                Resolve Beacon
              </button>
            </div>
          </div>
        </div>
      `;
    }).join("");
  },

  async resolveSOS(alertId) {
    // 1. Immediately remove from local list and UI for instant response
    this.activeSOSList = this.activeSOSList.filter(a => a.id !== alertId);
    this.renderSOSAlerts(this.activeSOSList);

    // Update SOS count stat badge
    const elSos = document.getElementById("stat-active-sos");
    if (elSos) elSos.textContent = this.activeSOSList.length;

    // 2. Transmit resolve action to backend
    try {
      await fetch(`${CONFIG.API_BASE_URL}/sos/${alertId}/resolve`, {
        method: "PUT",
        headers: AUTH.getAuthHeaders()
      });
      // 3. Refresh vessel markers on map to turn red dot back to green
      const vesselsRes = await fetch(`${CONFIG.API_BASE_URL}/admin/active-vessels`, {
        headers: AUTH.getAuthHeaders()
      });
      if (vesselsRes.ok) {
        const vessels = await vesselsRes.json();
        MARINE_MAP.updateAdminVessels(vessels);
      }
    } catch (e) {
      console.warn("Resolve SOS error:", e);
    }
  },

  async resolveSOSFromMap(vesselNumber) {
    const alert = this.activeSOSList.find(a => a.vessel_number === vesselNumber && a.status === "ACTIVE");
    if (alert) {
      await this.resolveSOS(alert.id);
    }
  }
};
