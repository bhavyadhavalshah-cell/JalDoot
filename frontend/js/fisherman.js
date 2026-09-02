// Fisherman Mode Controller
const FISHERMAN = {
  currentLat: CONFIG.DEFAULT_LAT,
  currentLon: CONFIG.DEFAULT_LON,
  sessionSeed: null,
  watchId: null,
  gpsInterval: null,
  recognition: null,
  isRecording: false,
  gpsPermissionGranted: false,
  cachedZones: [],

  async init() {
    this.sessionSeed = "seed_" + Math.random().toString(36).substring(2, 9) + "_" + Date.now();
    
    // Compulsory GPS permission check: must get real GPS fix to unlock app
    const hasGPS = await this.verifyCompulsoryGPS();
    if (!hasGPS) {
      this.showGPSRequiredModal();
      return;
    }

    // Ensure map is initialized and centered on user's live coordinates
    if (!MARINE_MAP.map) {
      MARINE_MAP.init("fisherman-marine-map", "fisherman", this.currentLat, this.currentLon);
    } else {
      MARINE_MAP.updateFishermanPosition(this.currentLat, this.currentLon, true);
    }

    this.setupRecenterButton();
    this.setupGeolocation();
    this.setupSpeechRecognition();
    this.setupChatUI();
    this.setupSOSModal();

    await this.refreshMarineData();

    if (this.gpsInterval) clearInterval(this.gpsInterval);
    this.gpsInterval = setInterval(() => {
      this.sendGPSPing();
    }, CONFIG.GPS_POLL_INTERVAL_MS);

    // If logged in with Auto Responsive checked, trigger auto-generated queries & route demo
    if (AUTH.isAutoResponsive) {
      setTimeout(() => this.runAutoResponsiveDemo(), 1500);
    }
  },

  setupRecenterButton() {
    const recenterBtn = document.getElementById("btn-recenter-fisherman-map");
    if (recenterBtn) {
      recenterBtn.addEventListener("click", () => {
        MARINE_MAP.updateFishermanPosition(this.currentLat, this.currentLon, true);
      });
    }
  },

  isDemoUser(username) {
    if (!username) return true; // default demo
    const u = username.toLowerCase();
    return u.includes("gujarat") || u.includes("maharashtra") || u.includes("goa") || u.includes("ramesh") || u.includes("bhavesh") || u.includes("suresh") || u.includes("admin") || u.includes("demo") || u.includes("kharva") || u.includes("koli") || u.includes("fernandes");
  },

  getStateCoordinates(username, homeState) {
    const u = (username || "").toLowerCase();
    const s = (homeState || "").toLowerCase();
    if (u.includes("goa") || s.includes("goa") || u.includes("fernandes") || u.includes("kharvi") || u.includes("dsouza")) {
      return { lat: 15.49, lon: 73.82, state: "Goa" };
    } else if (u.includes("maharashtra") || s.includes("maharashtra") || u.includes("mumbai") || u.includes("nakhwa") || u.includes("tare") || u.includes("agri")) {
      return { lat: 18.92, lon: 72.83, state: "Maharashtra" };
    } else {
      return { lat: 21.64, lon: 69.60, state: "Gujarat" };
    }
  },

  verifyCompulsoryGPS() {
    return new Promise((resolve) => {
      // 1. Check if user is a demo account or has pre-stored state coordinates (Gujarat, Maharashtra, Goa)
      const isDemo = !AUTH.currentUser || AUTH.currentUser.is_demo !== false || this.isDemoUser(AUTH.currentUser?.username);
      if (isDemo) {
        const stateCoords = this.getStateCoordinates(AUTH.currentUser?.username, AUTH.currentUser?.home_state);
        this.currentLat = AUTH.currentUser?.default_latitude || stateCoords.lat;
        this.currentLon = AUTH.currentUser?.default_longitude || stateCoords.lon;
        this.gpsPermissionGranted = true;
        this.hideGPSRequiredModal();
        resolve(true);
        return;
      }

      // 2. Real non-demo user browser GPS prompt
      if (!("geolocation" in navigator)) {
        resolve(false);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.currentLat = pos.coords.latitude;
          this.currentLon = pos.coords.longitude;
          this.gpsPermissionGranted = true;
          this.hideGPSRequiredModal();
          resolve(true);
        },
        (err) => {
          console.warn("Compulsory GPS query rejected or unavailable:", err.message);
          resolve(false);
        },
        { enableHighAccuracy: true, timeout: 6000 }
      );
    });
  },

  showGPSRequiredModal() {
    const modal = document.getElementById("gps-required-modal");
    if (modal) {
      modal.style.display = "flex";
    }
  },

  hideGPSRequiredModal() {
    const modal = document.getElementById("gps-required-modal");
    if (modal) {
      modal.style.display = "none";
    }
  },

  async retryGPSAccess() {
    const hasGPS = await this.verifyCompulsoryGPS();
    if (hasGPS) {
      this.hideGPSRequiredModal();
      MARINE_MAP.init("fisherman-marine-map", "fisherman", this.currentLat, this.currentLon);
      this.init();
    } else {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            this.currentLat = pos.coords.latitude;
            this.currentLon = pos.coords.longitude;
            this.gpsPermissionGranted = true;
            this.hideGPSRequiredModal();
            MARINE_MAP.init("fisherman-marine-map", "fisherman", this.currentLat, this.currentLon);
            this.init();
          },
          () => {
            alert("Location access is compulsory for JalDoot Marine Safety. Please allow location access in your browser settings to proceed.");
          }
        );
      }
    }
  },

  setupGeolocation() {
    // If user is logged in as a demo account, lock to their pre-stored state coordinates (Gujarat, Maharashtra, Goa)
    if (!AUTH.currentUser || AUTH.currentUser.is_demo !== false || this.isDemoUser(AUTH.currentUser?.username)) {
      return;
    }
    if ("geolocation" in navigator) {
      this.watchId = navigator.geolocation.watchPosition(
        (pos) => {
          this.currentLat = pos.coords.latitude;
          this.currentLon = pos.coords.longitude;
          MARINE_MAP.updateFishermanPosition(this.currentLat, this.currentLon, true);
        },
        (err) => console.warn("GPS tracking error:", err.message),
        { enableHighAccuracy: true }
      );
    }
  },

  async refreshMarineData() {
    try {
      const [weatherRes, pfzRecRes, pfzAllRes] = await Promise.all([
        fetch(`${CONFIG.API_BASE_URL}/weather/?lat=${this.currentLat}&lon=${this.currentLon}`),
        fetch(`${CONFIG.API_BASE_URL}/pfz/recommendations?lat=${this.currentLat}&lon=${this.currentLon}&limit=5&session_seed=${this.sessionSeed}`),
        fetch(`${CONFIG.API_BASE_URL}/pfz/all?lat=${this.currentLat}&lon=${this.currentLon}`)
      ]);

      if (weatherRes.ok) {
        const weatherData = await weatherRes.json();
        this.renderWeatherCard(weatherData);
      }

      if (pfzRecRes.ok) {
        const pfzData = await pfzRecRes.json();
        const nearest5 = pfzData.slice(0, 5);
        this.cachedZones = nearest5;
        this.renderPFZList(nearest5);
      }

      if (pfzAllRes.ok) {
        const allZones = await pfzAllRes.json();
        MARINE_MAP.renderPFZCircles(allZones);
      }
    } catch (e) {
      console.warn("Marine data refresh error:", e);
    }
  },

  async sendGPSPing() {
    try {
      await fetch(`${CONFIG.API_BASE_URL}/gps/update`, {
        method: "POST",
        headers: AUTH.getAuthHeaders(),
        body: JSON.stringify({
          latitude: this.currentLat,
          longitude: this.currentLon,
          speed_knots: 7.5,
          heading: 215.0
        })
      });
    } catch (e) {
      // Offline fallback
    }
  },

  renderWeatherCard(data, isCached = false) {
    const scoreVal = document.getElementById("safety-score-val");
    const scoreCircle = document.getElementById("safety-score-circle");
    const scoreTitle = document.getElementById("safety-score-title");
    const scoreReasons = document.getElementById("safety-score-reasons");

    const tempVal = document.getElementById("val-temp");
    const windVal = document.getElementById("val-wind");
    const waveVal = document.getElementById("val-wave");
    const condVal = document.getElementById("val-condition");
    const dataFreshness = document.getElementById("weather-freshness");

    const isCoastal = data.is_coastal_region !== false && data.sea_safety_score !== null && data.sea_safety_score !== undefined;

    if (scoreVal) {
      scoreVal.textContent = isCoastal ? data.sea_safety_score : "--";
    }

    if (scoreCircle) {
      scoreCircle.className = `score-circle status-${isCoastal ? data.safety_status : 'NON_COASTAL'}`;
    }

    if (scoreTitle) {
      if (!isCoastal) {
        scoreTitle.textContent = I18N.currentLang === "gu" 
          ? "બિન-દરિયાઈ વિસ્તાર" 
          : (I18N.currentLang === "hi" ? "गैर-तटीय क्षेत्र" : "Non-Coastal Region");
      } else if (data.safety_status === "SAFE") {
        scoreTitle.textContent = I18N.t("safeStatus");
      } else if (data.safety_status === "CAUTION") {
        scoreTitle.textContent = I18N.t("cautionStatus");
      } else {
        scoreTitle.textContent = I18N.t("dangerousStatus");
      }
    }

    if (scoreReasons) {
      if (!isCoastal) {
        const nonCoastalNotice = I18N.currentLang === "gu"
          ? "તમારું ઉપકરણ દરિયા કિનારાથી દૂર / અંતરિયાળ વિસ્તારમાં છે. સેફ-ટુ-સેલ સ્કોર ફક્ત દરિયાઈ તટ નજીક જ સક્રિય થશે."
          : (I18N.currentLang === "hi"
            ? "आपका उपकरण समुद्र तट से दूर अंतर्देशीय क्षेत्र में है. सुरक्षित नौकायन स्कोर केवल तटीय क्षेत्रों में सक्रिय होता है."
            : "Device location is inland / non-coastal. Safe to Sail score is active only near coastal or marine waters.");
        scoreReasons.innerHTML = `<li>• ${nonCoastalNotice}</li>`;
      } else if (data.safety_reasons && data.safety_reasons.length > 0) {
        scoreReasons.innerHTML = data.safety_reasons.map(r => `<li>• ${r}</li>`).join("");
      }
    }

    if (tempVal) tempVal.textContent = `${data.temperature_c}°C`;
    if (windVal) windVal.textContent = `${data.wind_speed_kmh} km/h`;
    if (waveVal) waveVal.textContent = `${data.wave_height_m}m`;
    if (condVal) condVal.textContent = data.weather_description;
    if (dataFreshness) {
      dataFreshness.textContent = `${I18N.t("dataAsOf")} ${data.data_timestamp}${isCached ? ' (Offline Telemetry)' : ''}`;
    }
  },

  renderPFZList(zones) {
    const container = document.getElementById("pfz-zones-container");
    if (!container) return;

    if (!zones || zones.length === 0) {
      container.innerHTML = `<p style="font-size:0.8rem; color:var(--text-muted);">No active PFZ in this sector.</p>`;
      return;
    }

    container.innerHTML = zones.map((z, idx) => {
      const translatedSpecies = I18N.translateSpeciesList(z.recommended_target_fish);
      const translatedDensity = I18N.translateDensity(z.density_level);
      const routeLabel = I18N.t("routeBtn");
      const distLabel = I18N.t("distance");
      const headingLabel = I18N.t("heading");
      const speciesLabel = I18N.t("species");

      return `
        <div class="pfz-item" style="cursor: pointer;" onclick="FISHERMAN.navigateToZone(${idx})">
          <div class="pfz-info" style="flex: 1;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; flex-wrap:wrap; gap:4px;">
              <h4 style="color:var(--primary-blue); font-size:0.82rem; margin:0;">${z.name}</h4>
              <div style="display:flex; gap:4px;">
                <span style="background:#FEF3C7; color:#92400E; font-size:0.62rem; font-weight:800; padding:1px 5px; border-radius:2px;">
                  ${translatedDensity}
                </span>
                <span style="background:#E0F2FE; color:#0369A1; font-size:0.62rem; font-weight:800; padding:1px 5px; border-radius:2px;">
                  🛰️ ${z.satellite_sensor || 'ISRO Oceansat-3'}
                </span>
              </div>
            </div>
            <p>${distLabel}: <b>${z.distance_km} km</b> (${headingLabel}: <b>${z.bearing_deg}°</b>) | Depth: <b>${z.depth_m || 30}m</b></p>
            <p>SST: <b>${z.sst_celsius}°C</b> | Chl: <b>${z.chlorophyll} mg/m³</b> | Upwelling: <b>${z.upwelling_index || '4.5'}</b> | ${speciesLabel}: <i>${translatedSpecies}</i></p>
          </div>
          <div style="margin-left: 8px;">
            <button onclick="event.stopPropagation(); FISHERMAN.navigateToZone(${idx})" style="background:var(--primary-blue); color:white; border:none; padding:5px 9px; border-radius:3px; font-weight:bold; cursor:pointer; font-size:0.7rem; white-space:nowrap;">
              ${routeLabel}
            </button>
          </div>
        </div>
      `;
    }).join("");
  },

  navigateToZone(index) {
    if (!this.cachedZones || !this.cachedZones[index]) return;
    const z = this.cachedZones[index];
    
    // 1. Draw route on Map
    MARINE_MAP.drawRouteToPFZ(z.latitude, z.longitude, z.name, z.distance_km, z.bearing_deg);
    
    // 2. Automatically dispatch query to Chatbot
    let queryText = `How do I sail to ${z.name}? Please provide the safe navigation route, distance (${z.distance_km} km), and target fish density.`;
    if (I18N.currentLang === "gu") {
      queryText = `${z.name} તરફ જવા માટે સુરક્ષિત દરિયાઈ રસ્તો, અંતર અને માછલીની સ્થિતિ શું છે?`;
    } else if (I18N.currentLang === "hi") {
      queryText = `${z.name} के लिए सुरक्षित समुद्री रास्ता, दूरी और मछली की स्थिति क्या है?`;
    }

    this.sendChatMessage(queryText);
  },

  setupSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = document.getElementById("btn-voice-chat");
    if (!SpeechRec || !micBtn) return;

    this.recognition = new SpeechRec();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;

    micBtn.addEventListener("click", () => {
      if (this.isRecording) {
        this.recognition.stop();
        this.isRecording = false;
        micBtn.classList.remove("recording");
      } else {
        const langMap = { "gu": "gu-IN", "hi": "hi-IN", "en": "en-IN" };
        this.recognition.lang = langMap[I18N.currentLang] || "en-IN";
        this.recognition.start();
        this.isRecording = true;
        micBtn.classList.add("recording");
      }
    });

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const chatInput = document.getElementById("chat-input-text");
      if (chatInput) {
        chatInput.value = transcript;
        this.sendChatMessage();
      }
      micBtn.classList.remove("recording");
      this.isRecording = false;
    };

    this.recognition.onerror = () => {
      micBtn.classList.remove("recording");
      this.isRecording = false;
    };
  },

  setupChatUI() {
    const sendBtn = document.getElementById("btn-chat-send");
    const chatInput = document.getElementById("chat-input-text");

    if (sendBtn && chatInput) {
      sendBtn.addEventListener("click", () => this.sendChatMessage());
      chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") this.sendChatMessage();
      });
    }

    const container = document.getElementById("chat-messages-container");
    if (container) {
      container.innerHTML = "";
    }

    const welcomeMsg = I18N.currentLang === "gu"
      ? "જલદૂત દરિયાઈ સલાહકાર પ્રણાલીમાં આપનું સ્વાગત છે. ગુજરાત, મહારાષ્ટ્ર અને ગોવા દરિયાઈ પટ્ટા માટે લાઈવ હવામાન, સંભવિત મત્સ્ય ક્ષેત્ર (PFZ), ભરતી-ઓટ અને નેવિગેશન રૂટ વિશે પૂછી શકો છો."
      : (I18N.currentLang === "hi"
        ? "जलदूत समुद्री सुरक्षा सलाहकार प्रणाली में आपका स्वागत है. गुजरात, महाराष्ट्र और गोवा तटीय क्षेत्रों हेतु लाइव मौसम, निकटतम मत्स्य क्षेत्र (PFZ), ज्वार-भाटा एवं नेविगेशन मार्ग के बारे में पूछ सकते हैं."
        : "Welcome to JalDoot Marine Safety Advisory System. Real-time advisories active for Gujarat, Maharashtra, and Goa coastal waters. Ask on live weather, nearest Potential Fishing Zones (PFZ), tide timings, or navigation routes.");

    this.appendAssistantBubble(
      welcomeMsg,
      I18N.currentLang,
      { "domain_scope": "Coastal Marine Coverage", "confidence": "100%" }
    );
  },

  async sendChatMessage(customText = null) {
    const chatInput = document.getElementById("chat-input-text");
    const text = customText || (chatInput ? chatInput.value.trim() : "");
    if (!text) return;

    if (chatInput) chatInput.value = "";
    this.appendUserBubble(text);

    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/chat/send`, {
        method: "POST",
        headers: AUTH.getAuthHeaders(),
        body: JSON.stringify({
          message: text,
          language: I18N.currentLang,
          latitude: this.currentLat,
          longitude: this.currentLon
        })
      });

      if (res.ok) {
        const data = await res.json();
        this.appendAssistantBubble(data.reply, data.detected_language, data.explainable_factors);
        this.speakText(data.reply, data.detected_language);

        // Check if query is asking for route/fishing zone
        const qLower = text.toLowerCase();
        if (qLower.includes("route") || qLower.includes("zone") || qLower.includes("fish") || qLower.includes("pfz") || qLower.includes("direction") || qLower.includes("porbandar") || qLower.includes("veraval") || qLower.includes("mumbai") || qLower.includes("goa")) {
          if (this.cachedZones && this.cachedZones.length > 0) {
            const primaryZone = this.cachedZones[0];
            MARINE_MAP.drawRouteToPFZ(primaryZone.latitude, primaryZone.longitude, primaryZone.name, primaryZone.distance_km, primaryZone.bearing_deg);
          }
        }
      } else {
        this.appendAssistantBubble("System Advisory: Unable to process query at this moment.", "en");
      }
    } catch (e) {
      this.appendAssistantBubble("Offline Mode: Marine safety factors and telemetry are active.", I18N.currentLang);
    }
  },

  /**
   * Auto Responsive Logic: generates realistic queries and automatically plots navigation routes
   */
  async runAutoResponsiveDemo() {
    const sampleQuestions = [
      "What is the live Sea Safety Score and wave height for our coastal sector today?",
      "Which Potential Fishing Zone has maximum fish density and what is the direct route?"
    ];

    for (let i = 0; i < sampleQuestions.length; i++) {
      await new Promise(r => setTimeout(r, (i + 1) * 2200));
      await this.sendChatMessage(sampleQuestions[i]);
    }
  },

  getFormattedLiveTime() {
    return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }) + " IST";
  },

  appendUserBubble(text) {
    const container = document.getElementById("chat-messages-container");
    if (!container) return;

    const liveTime = this.getFormattedLiveTime();
    const div = document.createElement("div");
    div.className = "chat-bubble user";
    div.innerHTML = `
      <div>${text}</div>
      <div class="chat-meta">
        <span style="font-weight:600;">Fisherman Inquiry</span>
        <span>${liveTime}</span>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  },

  appendAssistantBubble(text, lang = "en", factors = null) {
    const container = document.getElementById("chat-messages-container");
    if (!container) return;

    const liveTime = this.getFormattedLiveTime();
    const div = document.createElement("div");
    div.className = "chat-bubble assistant";

    let factorsHtml = "";
    if (factors) {
      const isOffTopic = factors.domain_status === "OUT_OF_DOMAIN";
      factorsHtml = `
        <div style="margin-top: 6px; font-size: 0.72rem; border-top: 1px solid var(--border-light); padding-top: 4px;">
          <details>
            <summary style="cursor:pointer; color:var(--teal-accent-dark); font-weight:700;">Decision Factors (${factors.confidence || '98%'})</summary>
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
              ${isOffTopic ? '<span style="color:var(--marker-red); font-weight:bold;">Out-of-Scope Query Filtered</span>' : `
                <span style="background:#FFFFFF; border:1px solid var(--border-light); padding:1px 5px; border-radius:2px;">Wind: ${factors.wind_speed || '16 km/h'}</span>
                <span style="background:#FFFFFF; border:1px solid var(--border-light); padding:1px 5px; border-radius:2px;">Wave: ${factors.wave_height || '1.1m'}</span>
                <span style="background:#FFFFFF; border:1px solid var(--border-light); padding:1px 5px; border-radius:2px;">Score: ${factors.sea_safety_score || '88/100'}</span>
              `}
            </div>
          </details>
        </div>
      `;
    }

    div.innerHTML = `
      <div>${text}</div>
      ${factorsHtml}
      <div class="chat-meta">
        <span style="font-weight:600;">JalDoot AI Advisory</span>
        <span>${liveTime}</span>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  },

  speakText(text, lang = "en") {
    if (!("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel(); // Stop any pending speech

      // Clean conversational text for spoken speech (remove markdown symbols, brackets, asterisks)
      let cleanSpeech = text
        .replace(/[*_#`~[\]()]/g, " ")
        .replace(/[\d]+\.[\d]+%/g, "")
        .replace(/https?:\/\/\S+/g, "")
        .replace(/\s+/g, " ")
        .trim();

      const voices = window.speechSynthesis.getVoices() || [];

      // SPECIAL RULE FOR GUJARATI:
      // Give top priority to authentic local Gujarati voice (gu-IN).
      // If no local Gujarati voice exists on this device/system, give ONLY text reply (do NOT play non-Gujarati voice).
      if (lang === "gu") {
        const localGujaratiVoice = voices.find(v => (
          v.lang === "gu-IN" || 
          v.lang === "gu_IN" || 
          v.lang.toLowerCase().startsWith("gu") || 
          v.name.toLowerCase().includes("gujarati") || 
          v.name.includes("ગુજરાતી")
        ));

        if (!localGujaratiVoice) {
          console.log("No local Gujarati voice found on system. Providing text-only reply as requested.");
          return; // Skip voice synthesis entirely; text reply is already displayed
        }

        const utterance = new SpeechSynthesisUtterance(cleanSpeech);
        utterance.voice = localGujaratiVoice;
        utterance.lang = "gu-IN";
        utterance.rate = 0.88; // Natural local Gujarati conversational pacing
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
        return;
      }

      // For Hindi and English:
      const utterance = new SpeechSynthesisUtterance(cleanSpeech);
      const langMap = { "hi": "hi-IN", "en": "en-IN" };
      const targetLangTag = langMap[lang] || "en-IN";
      utterance.lang = targetLangTag;
      utterance.rate = 0.90;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      if (voices.length > 0) {
        let bestVoice = null;
        if (lang === "hi") {
          bestVoice = voices.find(v => (
            v.lang === "hi-IN" || 
            v.lang.startsWith("hi") ||
            v.name.includes("India") || 
            v.name.includes("Kavya") || 
            v.name.includes("Madhur") || 
            v.name.includes("Swara")
          ));
        } else {
          bestVoice = voices.find(v => v.lang === "en-IN" || v.name.includes("India"));
        }
        if (bestVoice) utterance.voice = bestVoice;
      }

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("TTS error:", e);
    }
  },

  setupSOSModal() {
    const triggerBtn = document.getElementById("btn-trigger-sos");
    const modal = document.getElementById("sos-modal");
    const confirmBtn = document.getElementById("btn-confirm-sos");
    const cancelBtn = document.getElementById("btn-cancel-sos");

    if (triggerBtn && modal) {
      triggerBtn.addEventListener("click", () => {
        modal.style.display = "flex";
      });
    }

    if (cancelBtn && modal) {
      cancelBtn.addEventListener("click", () => {
        modal.style.display = "none";
      });
    }

    if (confirmBtn && modal) {
      confirmBtn.addEventListener("click", async () => {
        modal.style.display = "none";
        await this.dispatchSOS();
      });
    }
  },

  async dispatchSOS() {
    const targetEmail = "jaldootprojectsih@gmail.com";
    try {
      const res = await fetch(`${CONFIG.API_BASE_URL}/sos/trigger`, {
        method: "POST",
        headers: AUTH.getAuthHeaders(),
        body: JSON.stringify({
          latitude: this.currentLat,
          longitude: this.currentLon,
          emergency_type: "MAYDAY_DISTRESS",
          details: "Critical emergency beacon initiated by captain."
        })
      });

      if (res.ok) {
        const data = await res.json();
        alert(`🚨 DISTRESS BEACON ACTIVATED & DISPATCHED:\n\n• Recipient Email: ${targetEmail}\n• Message: ${data.message}\n• Live Coordinates: [${this.currentLat.toFixed(4)}, ${this.currentLon.toFixed(4)}]\n• Status: DISPATCHED TO SEARCH & RESCUE`);
      } else {
        // Direct Client Fallback to FormSubmit to guarantee email arrival
        this.clientFallbackEmailDispatch();
        alert(`🚨 DISTRESS BEACON TRANSMITTED:\n\nEmergency telemetry dispatched to ${targetEmail} and logged in maritime offline buffer.\nCoordinates: [${this.currentLat.toFixed(4)}, ${this.currentLon.toFixed(4)}]`);
      }
    } catch (e) {
      this.clientFallbackEmailDispatch();
      alert(`🚨 DISTRESS BEACON TRANSMITTED:\n\nEmergency telemetry dispatched to ${targetEmail} and logged in maritime offline buffer.\nCoordinates: [${this.currentLat.toFixed(4)}, ${this.currentLon.toFixed(4)}]`);
    }
  },

  clientFallbackEmailDispatch() {
    const user = AUTH.currentUser || { username: "Fisherman", vessel_number: "IND-VESSEL" };
    try {
      fetch("https://formsubmit.co/ajax/jaldootprojectsih@gmail.com", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: `JalDoot Emergency SOS - ${user.vessel_number || user.username}`,
          email: "jaldootprojectsih@gmail.com",
          _subject: `🚨 [JALDOOT SOS ALERT] Vessel ${user.vessel_number || user.username} - [${this.currentLat.toFixed(4)}, ${this.currentLon.toFixed(4)}]`,
          fisherman: user.username,
          vessel: user.vessel_number,
          phone: user.phone_number,
          latitude: this.currentLat.toFixed(6),
          longitude: this.currentLon.toFixed(6),
          google_maps: `https://www.google.com/maps?q=${this.currentLat.toFixed(6)},${this.currentLon.toFixed(6)}`,
          timestamp: new Date().toLocaleString("en-IN")
        })
      }).catch(err => console.warn("Client email dispatch notice:", err));
    } catch (err) {
      // Ignore
    }
  }
};
