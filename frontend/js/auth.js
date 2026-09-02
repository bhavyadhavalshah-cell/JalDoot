// Authentication and Session Management
const AUTH = {
  currentUser: null,
  token: null,
  isAutoResponsiveSession: false,

  init() {
    this.token = localStorage.getItem("jaldoot_jwt_token");
    const userStr = localStorage.getItem("jaldoot_user");
    if (userStr) {
      try {
        this.currentUser = JSON.parse(userStr);
      } catch (e) {
        this.currentUser = null;
      }
    }
    this.isAutoResponsiveSession = localStorage.getItem("jaldoot_is_auto_responsive") === "true";
  },

  getAuthHeaders() {
    return {
      "Authorization": `Bearer ${this.token}`,
      "Content-Type": "application/json"
    };
  },

  isAuthenticated() {
    return !!this.token && !!this.currentUser;
  },

  isAdmin() {
    return this.currentUser && this.currentUser.role === "admin";
  },

  get isAutoResponsive() {
    return this.isAutoResponsiveSession;
  },

  async login(usernameOrEmail, password, interfaceMode = "desktop", isAutoResponsive = false) {
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username_or_email: usernameOrEmail,
          password: password,
          interface_mode: interfaceMode,
          is_auto_responsive: isAutoResponsive
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Login failed. Please check credentials.");
      }

      const data = await response.json();
      this.token = data.access_token;
      this.isAutoResponsiveSession = Boolean(data.is_auto_responsive);
      this.currentUser = {
        username: data.username,
        role: data.role,
        vessel_number: data.vessel_number,
        vessel_photo: data.vessel_photo,
        preferred_language: data.preferred_language,
        interface_mode: data.interface_mode,
        is_auto_responsive: this.isAutoResponsiveSession,
        default_latitude: data.default_latitude,
        default_longitude: data.default_longitude,
        home_state: data.home_state,
        is_demo: data.is_demo
      };

      localStorage.setItem("jaldoot_jwt_token", this.token);
      localStorage.setItem("jaldoot_user", JSON.stringify(this.currentUser));
      localStorage.setItem("jaldoot_is_auto_responsive", this.isAutoResponsiveSession.toString());

      if (data.preferred_language) {
        I18N.setLanguage(data.preferred_language);
      }

      return this.currentUser;
    } catch (e) {
      console.error("Login error:", e);
      throw e;
    }
  },

  async registerFisherman(formData) {
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/auth/register-fisherman`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Registration failed.");
      }

      const data = await response.json();
      this.token = data.access_token;
      this.isAutoResponsiveSession = Boolean(data.is_auto_responsive);
      this.currentUser = {
        username: data.username,
        role: data.role,
        vessel_number: data.vessel_number,
        vessel_photo: data.vessel_photo,
        preferred_language: data.preferred_language,
        interface_mode: data.interface_mode,
        is_auto_responsive: this.isAutoResponsiveSession
      };

      localStorage.setItem("jaldoot_jwt_token", this.token);
      localStorage.setItem("jaldoot_user", JSON.stringify(this.currentUser));
      localStorage.setItem("jaldoot_is_auto_responsive", this.isAutoResponsiveSession.toString());

      return this.currentUser;
    } catch (e) {
      console.error("Fisherman register error:", e);
      throw e;
    }
  },

  logout() {
    this.token = null;
    this.currentUser = null;
    this.isAutoResponsiveSession = false;
    localStorage.removeItem("jaldoot_jwt_token");
    localStorage.removeItem("jaldoot_user");
    localStorage.removeItem("jaldoot_is_auto_responsive");
    window.location.reload();
  }
};
