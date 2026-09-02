// Main Application Bootstrap & UI Controller
const APP = {
  activeView: "login-view",
  clockTimer: null,
  interfaceMode: "desktop",

  async init() {
    // Requirement 2: Start continuous live real-time clock everywhere immediately
    this.startLiveClock();

    // Load stored interface mode
    this.loadInterfaceMode();

    // Initialize Storage, Translations, and Auth
    await STORAGE.init();
    I18N.init();
    AUTH.init();

    // Setup Event Listeners
    this.setupLanguageSelector();
    this.setupNetworkListeners();
    this.setupAuthForms();
    this.setupForgotPasswordModal();
    this.setupGPSModal();
    this.registerServiceWorker();

    // Check Initial Auth State
    if (AUTH.isAuthenticated()) {
      if (AUTH.isAdmin()) {
        this.switchView("admin-view");
      } else {
        this.switchView("fisherman-view");
      }
    } else {
      this.switchView("login-view");
    }
  },

  startLiveClock() {
    const clockEl = document.getElementById("live-clock-text");
    const updateClock = () => {
      const now = new Date();
      const options = { 
        day: "2-digit", 
        month: "short", 
        year: "numeric", 
        hour: "2-digit", 
        minute: "2-digit", 
        second: "2-digit",
        hour12: false
      };
      if (clockEl) {
        clockEl.textContent = now.toLocaleDateString("en-IN", options) + " IST";
      }
    };

    updateClock();
    if (this.clockTimer) clearInterval(this.clockTimer);
    this.clockTimer = setInterval(updateClock, 1000);
  },

  loadInterfaceMode() {
    const savedMode = localStorage.getItem("jaldoot_interface_mode") || "desktop";
    this.setInterfaceMode(savedMode);
  },

  setInterfaceMode(mode) {
    this.interfaceMode = mode;
    localStorage.setItem("jaldoot_interface_mode", mode);

    document.body.classList.remove("force-mobile-view", "force-desktop-view");
    if (mode === "mobile") {
      document.body.classList.add("force-mobile-view");
    } else if (mode === "desktop") {
      document.body.classList.add("force-desktop-view");
    }

    const radio = document.querySelector(`input[name="layout-mode"][value="${mode}"]`);
    if (radio) radio.checked = true;
  },

  setupLanguageSelector() {
    const langSelect = document.getElementById("lang-select");
    if (langSelect) {
      langSelect.addEventListener("change", (e) => {
        I18N.setLanguage(e.target.value);
        if (FISHERMAN && this.activeView === "fisherman-view") {
          FISHERMAN.refreshMarineData();
        }
      });
    }
  },

  setupNetworkListeners() {
    const netBanner = document.getElementById("network-banner");
    const netBannerText = document.getElementById("network-banner-text");

    const updateNetworkStatus = (isOnline) => {
      if (isOnline) {
        if (netBanner) netBanner.style.display = "none";
        if (AUTH.isAuthenticated()) {
          fetch(`${CONFIG.API_BASE_URL}/gps/network-event`, {
            method: "POST",
            headers: AUTH.getAuthHeaders(),
            body: JSON.stringify({ event_type: "ONLINE", details: "Network connection active." })
          }).catch(() => {});
        }
      } else {
        const cachedTime = new Date().toLocaleTimeString();
        if (netBanner && netBannerText) {
          netBanner.className = "network-banner";
          netBannerText.textContent = `Vessel leaving terrestrial network coverage — last telemetry cached at ${cachedTime}`;
          netBanner.style.display = "block";
        }
      }
    };

    window.addEventListener("online", () => updateNetworkStatus(true));
    window.addEventListener("offline", () => updateNetworkStatus(false));
    updateNetworkStatus(navigator.onLine);
  },

  setupAuthForms() {
    const tabLogin = document.getElementById("tab-login") || document.getElementById("tab-auth-login");
    const tabReg = document.getElementById("tab-register") || document.getElementById("tab-auth-register");
    const formLogin = document.getElementById("form-login");
    const formReg = document.getElementById("form-register");
    const authError = document.getElementById("auth-error-msg");

    document.querySelectorAll(`input[name="layout-mode"]`).forEach(radio => {
      radio.addEventListener("change", (e) => {
        this.setInterfaceMode(e.target.value);
      });
    });

    if (tabLogin && tabReg && formLogin && formReg) {
      tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabReg.classList.remove("active");
        formLogin.style.display = "block";
        formReg.style.display = "none";
        if (authError) authError.style.display = "none";
      });

      tabReg.addEventListener("click", () => {
        tabReg.classList.add("active");
        tabLogin.classList.remove("active");
        formLogin.style.display = "none";
        formReg.style.display = "block";
        if (authError) authError.style.display = "none";
      });
    }

    if (formLogin) {
      formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userInput = document.getElementById("login-username")?.value.trim();
        const passInput = document.getElementById("login-password")?.value.trim();
        
        const modeRadio = document.querySelector('input[name="layout-mode"]:checked');
        const selectedMode = modeRadio ? modeRadio.value : "desktop";

        if (!userInput || !passInput) return;

        try {
          if (authError) authError.style.display = "none";
          this.setInterfaceMode(selectedMode);
          const user = await AUTH.login(userInput, passInput, selectedMode, true);

          if (user.role === "admin") {
            this.switchView("admin-view");
          } else {
            this.switchView("fisherman-view");
          }
        } catch (err) {
          if (authError) {
            authError.textContent = err.message || "Invalid credentials.";
            authError.style.display = "block";
          }
        }
      });
    }

    if (formReg) {
      formReg.addEventListener("submit", async (e) => {
        e.preventDefault();
        const uname = document.getElementById("reg-username")?.value.trim();
        const pass = document.getElementById("reg-password")?.value.trim();
        const vesselNo = document.getElementById("reg-vessel-no")?.value.trim();
        const phone = document.getElementById("reg-phone")?.value.trim();
        const photoInput = document.getElementById("reg-photo");
        
        // Requirement 1: Frontend validation for exactly 10 numeric digits
        const cleanPhone = (phone || "").replace(/\D/g, "");
        if (cleanPhone.length !== 10) {
          if (authError) {
            authError.textContent = "Validation Error: Mobile number must contain exactly 10 numeric digits.";
            authError.style.display = "block";
          }
          return;
        }

        const modeRadio = document.querySelector('input[name="layout-mode"]:checked');
        const selectedMode = modeRadio ? modeRadio.value : "mobile";
        const isAutoResp = Boolean(document.getElementById("chk-auto-responsive")?.checked);

        const formData = new FormData();
        formData.append("username", uname);
        formData.append("password", pass);
        formData.append("vessel_number", vesselNo);
        formData.append("phone_number", cleanPhone);
        formData.append("preferred_language", I18N.currentLang);
        formData.append("interface_mode", selectedMode);
        formData.append("is_auto_responsive", isAutoResp);

        if (photoInput && photoInput.files.length > 0) {
          formData.append("vessel_photo", photoInput.files[0]);
        }

        try {
          if (authError) authError.style.display = "none";
          this.setInterfaceMode(selectedMode);
          const user = await AUTH.registerFisherman(formData);
          this.switchView("fisherman-view");
        } catch (err) {
          if (authError) {
            authError.textContent = err.message || "Registration failed.";
            authError.style.display = "block";
          }
        }
      });
    }

    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => AUTH.logout());
    }
  },

  setupForgotPasswordModal() {
    const linkForgot = document.getElementById("link-forgot-password");
    const modal = document.getElementById("forgot-password-modal");
    const btnCancel = document.getElementById("btn-cancel-reset");
    const formReset = document.getElementById("form-reset-password");
    const errEl = document.getElementById("reset-error-msg");
    const succEl = document.getElementById("reset-success-msg");

    if (linkForgot && modal) {
      linkForgot.addEventListener("click", (e) => {
        e.preventDefault();
        modal.style.display = "flex";
        if (errEl) errEl.style.display = "none";
        if (succEl) succEl.style.display = "none";
        if (formReset) formReset.reset();
      });
    }

    if (btnCancel && modal) {
      btnCancel.addEventListener("click", () => {
        modal.style.display = "none";
      });
    }

    if (formReset) {
      formReset.addEventListener("submit", async (e) => {
        e.preventDefault();
        const phone = document.getElementById("reset-phone")?.value.trim();
        const newPass = document.getElementById("reset-new-password")?.value.trim();
        const confPass = document.getElementById("reset-confirm-password")?.value.trim();

        if (errEl) errEl.style.display = "none";
        if (succEl) succEl.style.display = "none";

        if (newPass !== confPass) {
          if (errEl) {
            errEl.textContent = "New password and confirm password do not match.";
            errEl.style.display = "block";
          }
          return;
        }

        try {
          const res = await fetch(`${CONFIG.API_BASE_URL}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              phone_number: phone,
              new_password: newPass,
              confirm_password: confPass
            })
          });

          const data = await res.json();
          if (res.ok) {
            if (succEl) {
              succEl.textContent = data.message || "Password updated successfully!";
              succEl.style.display = "block";
            }
            setTimeout(() => {
              modal.style.display = "none";
              // Pre-fill username field in login form
              const loginUser = document.getElementById("login-username");
              if (loginUser && data.username) loginUser.value = data.username;
            }, 2000);
          } else {
            if (errEl) {
              errEl.textContent = data.detail || "Unable to reset password.";
              errEl.style.display = "block";
            }
          }
        } catch (err) {
          if (errEl) {
            errEl.textContent = "Network error while updating password.";
            errEl.style.display = "block";
          }
        }
      });
    }
  },

  setupGPSModal() {
    const retryBtn = document.getElementById("btn-retry-gps");
    if (retryBtn) {
      retryBtn.addEventListener("click", () => {
        if (FISHERMAN) {
          FISHERMAN.retryGPSAccess();
        }
      });
    }
  },

  switchView(viewId) {
    this.activeView = viewId;
    
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active-view"));

    const targetSection = document.getElementById(viewId);
    if (targetSection) {
      targetSection.classList.add("active-view");
    }

    const logoutBtn = document.getElementById("btn-logout");
    const userWidget = document.getElementById("user-profile-widget");
    const userDisplay = document.getElementById("user-profile-display");
    const roleNavBar = document.getElementById("role-nav-bar");

    if (viewId === "login-view") {
      if (logoutBtn) logoutBtn.style.display = "none";
      if (userWidget) userWidget.style.display = "none";
      if (roleNavBar) roleNavBar.style.display = "none";
    } else {
      if (logoutBtn) logoutBtn.style.display = "inline-block";
      if (userWidget && AUTH.currentUser) {
        userWidget.style.display = "flex";
        if (userDisplay) {
          userDisplay.textContent = AUTH.currentUser.username;
        }
      }

      if (roleNavBar) roleNavBar.style.display = "none";

      if (viewId === "fisherman-view") {
        setTimeout(() => {
          MARINE_MAP.init("fisherman-marine-map", "fisherman", FISHERMAN.currentLat, FISHERMAN.currentLon);
          FISHERMAN.init();
        }, 100);
      } else if (viewId === "admin-view") {
        setTimeout(() => {
          MARINE_MAP.init("admin-marine-map", "admin");
          ADMIN.init();
        }, 100);
      }
    }
  },

  registerServiceWorker() {
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/sw.js")
          .then(reg => console.log("JalDoot Telemetry Service Worker registered:", reg.scope))
          .catch(err => console.log("Service Worker registration notice:", err));
      });
    }
  }
};

document.addEventListener("DOMContentLoaded", () => APP.init());
