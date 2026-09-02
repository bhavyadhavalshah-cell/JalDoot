// Researcher Mode Controller (Admin Dashboard Only)
const RESEARCHER = {
  trendsChartInstance: null,
  whatifChartInstance: null,

  async init() {
    this.setupRegionSelector();
    this.setupWhatIfSimulator();
    await this.loadTrendsChart("Porbandar Offshore");
    await this.runSimulation();
  },

  setupRegionSelector() {
    const selector = document.getElementById("research-region-select");
    if (selector) {
      selector.addEventListener("change", (e) => {
        this.loadTrendsChart(e.target.value);
      });
    }
  },

  async loadTrendsChart(regionName) {
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/researcher/historical-trends?region=${encodeURIComponent(regionName)}`, {
        headers: AUTH.getAuthHeaders()
      });
      if (!res.ok) return;
      const data = await res.json();
      this.renderTrendsChart(data.metrics, regionName);
    } catch (e) {
      console.warn("Failed to load historical trends:", e);
    }
  },

  renderTrendsChart(metrics, regionName) {
    const canvas = document.getElementById("ocean-trends-chart");
    if (!canvas || !window.Chart) return;

    const ctx = canvas.getContext("2d");
    if (this.trendsChartInstance) {
      this.trendsChartInstance.destroy();
    }

    this.trendsChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: metrics.labels,
        datasets: [
          {
            label: "Sea Surface Temp (°C)",
            data: metrics.sst,
            borderColor: "#E07A5F", // --marker-amber
            backgroundColor: "rgba(224, 122, 95, 0.1)",
            yAxisID: "y-sst",
            tension: 0.35,
            borderWidth: 2.5
          },
          {
            label: "Chlorophyll-a (mg/m³)",
            data: metrics.chlorophyll,
            borderColor: "#0F7A6A", // --teal-accent-dark
            backgroundColor: "rgba(15, 122, 106, 0.1)",
            yAxisID: "y-chl",
            tension: 0.35,
            borderWidth: 2.5
          },
          {
            label: "Historical Fish Yield Index",
            data: metrics.fish_productivity,
            borderColor: "#087E8B", // --primary-blue
            backgroundColor: "rgba(8, 126, 139, 0.1)",
            yAxisID: "y-prod",
            borderDash: [4, 4],
            tension: 0.2,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          "y-sst": {
            type: "linear",
            position: "left",
            title: { display: true, text: "SST (°C)" },
            min: 20,
            max: 34
          },
          "y-chl": {
            type: "linear",
            position: "right",
            title: { display: true, text: "Chlorophyll (mg/m³)" },
            grid: { drawOnChartArea: false },
            min: 0,
            max: 6
          },
          "y-prod": { display: false, min: 0, max: 100 }
        },
        plugins: {
          legend: {
            position: "top",
            labels: { font: { family: "-apple-system, BlinkMacSystemFont, sans-serif", weight: "bold" } }
          }
        }
      }
    });
  },

  renderWhatIfCurveChart(labels, curveData, activeSST) {
    const canvas = document.getElementById("whatif-dynamic-chart");
    if (!canvas || !window.Chart) return;

    const ctx = canvas.getContext("2d");
    if (this.whatifChartInstance) {
      this.whatifChartInstance.destroy();
    }

    const roundedSST = Math.round(activeSST * 10) / 10;
    const activeLabel = `${roundedSST.toFixed(1)}°C`;

    this.whatifChartInstance = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Simulated Fish Yield Curve (Across Thermal Gradient)",
            data: curveData,
            borderColor: "#087E8B",
            backgroundColor: "rgba(8, 126, 139, 0.18)",
            fill: true,
            tension: 0.35,
            borderWidth: 3,
            pointBackgroundColor: labels.map(l => (Math.abs(parseFloat(l) - roundedSST) < 0.3) ? "#D9383A" : "#087E8B"),
            pointBorderColor: labels.map(l => (Math.abs(parseFloat(l) - roundedSST) < 0.3) ? "#FFFFFF" : "#087E8B"),
            pointBorderWidth: labels.map(l => (Math.abs(parseFloat(l) - roundedSST) < 0.3) ? 2 : 1),
            pointRadius: labels.map(l => (Math.abs(parseFloat(l) - roundedSST) < 0.3) ? 8 : 2.5),
            pointHoverRadius: 9
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        scales: {
          y: {
            title: { display: true, text: "Estimated Productivity Index (0-100)" },
            min: 0,
            max: 100,
            grid: { color: "rgba(0,0,0,0.05)" }
          },
          x: {
            title: { display: true, text: "Hypothetical Sea Surface Temperature Range (°C)" },
            grid: { color: "rgba(0,0,0,0.03)" }
          }
        },
        plugins: {
          legend: {
            position: "top",
            labels: { font: { family: "-apple-system, BlinkMacSystemFont, sans-serif", weight: "bold" } }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Productivity: ${context.parsed.y}/100`;
              }
            }
          }
        }
      }
    });
  },

  setupWhatIfSimulator() {
    const sstSlider = document.getElementById("sim-sst-slider");
    const chlSlider = document.getElementById("sim-chl-slider");
    const windSlider = document.getElementById("sim-wind-slider");

    [sstSlider, chlSlider, windSlider].forEach(slider => {
      if (slider) {
        slider.addEventListener("input", () => this.runSimulation());
      }
    });
  },

  async runSimulation() {
    const sst = parseFloat(document.getElementById("sim-sst-slider")?.value || 26.5);
    const chl = parseFloat(document.getElementById("sim-chl-slider")?.value || 2.5);
    const wind = parseFloat(document.getElementById("sim-wind-slider")?.value || 15.0);

    const sstLbl = document.getElementById("sim-sst-val");
    const chlLbl = document.getElementById("sim-chl-val");
    const windLbl = document.getElementById("sim-wind-val");

    if (sstLbl) sstLbl.textContent = `${sst.toFixed(1)}°C`;
    if (chlLbl) chlLbl.textContent = `${chl.toFixed(1)} mg/m³`;
    if (windLbl) windLbl.textContent = `${wind.toFixed(0)} km/h`;

    // Local instant calculation for zero-latency interactive curve & score updating
    const optimal_sst = 26.5;
    const thermal_deviation = Math.abs(sst - optimal_sst);
    const localProductivity = Math.max(5.0, Math.min(100.0, Math.round((100.0 - (thermal_deviation * 16.0) + (Math.min(chl, 5.0) * 8.0) - (Math.max(0, wind - 20.0) * 0.8)) * 10) / 10));

    let localSpecies = ["Indian Mackerel", "Yellowfin Tuna", "Kingfish (Surmai)", "Squids"];
    let localAdvisory = "Optimal thermal window: High pelagic schooling activity around thermal front boundaries.";
    if (sst < 25.0) {
      localSpecies = ["Hilsa (Chakshi)", "Croaker (Ghol)", "Silver Pomfret"];
      localAdvisory = "Cold upwelling zone detected: High nutrient influx promoting benthic and demersal fish.";
    } else if (sst > 28.0) {
      localSpecies = ["Deep Water Snapper", "Barracuda", "Skipjack Tuna"];
      localAdvisory = "Thermal stress threshold: Fish migration towards deeper, cooler shelf waters.";
    }

    const scoreEl = document.getElementById("sim-result-score");
    const speciesEl = document.getElementById("sim-result-species");
    const densityEl = document.getElementById("sim-result-density");
    const advisoryEl = document.getElementById("sim-result-advisory");
    const modEl = document.getElementById("sim-result-mod");

    if (scoreEl) scoreEl.textContent = `${localProductivity}/100`;
    if (speciesEl) speciesEl.textContent = localSpecies.join(", ");
    if (densityEl) densityEl.textContent = `${Math.round(localProductivity * 18.2)} kg/km²`;
    if (advisoryEl) advisoryEl.textContent = localAdvisory;
    if (modEl) {
      const modVal = (localProductivity >= 75) ? 0.0 : ((localProductivity < 40) ? -15.0 : -6.0);
      modEl.textContent = `${modVal > 0 ? '+' : ''}${modVal.toFixed(1)} pts (Linked to Safe-to-Sail score)`;
    }

    // Dynamic curve dataset across thermal gradient
    const labels = [];
    const curveData = [];
    for (let t = 20.0; t <= 34.0; t += 1.0) {
      labels.push(`${t.toFixed(0)}°C`);
      const tDev = Math.abs(t - optimal_sst);
      const val = Math.max(5.0, Math.min(100.0, Math.round((100.0 - (tDev * 16.0) + (Math.min(chl, 5.0) * 8.0) - (Math.max(0, wind - 20.0) * 0.8)) * 10) / 10));
      curveData.push(val);
    }
    this.renderWhatIfCurveChart(labels, curveData, sst);

    // Background synchronization with backend API
    try {
      await fetch(`${CONFIG.API_BASE_URL}/researcher/what-if-simulation?sst=${sst}&chlorophyll=${chl}&wind_speed=${wind}`, {
        headers: AUTH.getAuthHeaders()
      });
    } catch (e) {
      // Offline fallback
    }
  }
};
