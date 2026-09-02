// IndexedDB & LocalStorage Offline Cache Manager
const STORAGE = {
  dbName: "JalDootOfflineDB",
  dbVersion: 1,
  db: null,

  async init() {
    return new Promise((resolve) => {
      if (!window.indexedDB) {
        console.warn("IndexedDB not supported in browser, fallback to localStorage");
        resolve(null);
        return;
      }
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains("marine_cache")) {
          db.createObjectStore("marine_cache", { keyPath: "key" });
        }
        if (!db.objectStoreNames.contains("offline_gps_queue")) {
          db.createObjectStore("offline_gps_queue", { autoIncrement: true });
        }
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        resolve(this.db);
      };

      request.onerror = () => {
        console.warn("IndexedDB open error, using localStorage fallback");
        resolve(null);
      };
    });
  },

  async setCache(key, data) {
    const payload = {
      key: key,
      data: data,
      timestamp: new Date().toISOString()
    };
    // Save to LocalStorage as instant backup
    localStorage.setItem(`jaldoot_cache_${key}`, JSON.stringify(payload));

    if (this.db) {
      try {
        const tx = this.db.transaction("marine_cache", "readwrite");
        const store = tx.objectStore("marine_cache");
        store.put(payload);
      } catch (e) {
        console.error("IndexedDB set error", e);
      }
    }
  },

  async getCache(key) {
    if (this.db) {
      try {
        return new Promise((resolve) => {
          const tx = this.db.transaction("marine_cache", "readonly");
          const store = tx.objectStore("marine_cache");
          const req = store.get(key);
          req.onsuccess = () => {
            if (req.result) {
              resolve(req.result);
            } else {
              // Try localStorage
              const raw = localStorage.getItem(`jaldoot_cache_${key}`);
              resolve(raw ? JSON.parse(raw) : null);
            }
          };
          req.onerror = () => {
            const raw = localStorage.getItem(`jaldoot_cache_${key}`);
            resolve(raw ? JSON.parse(raw) : null);
          };
        });
      } catch (e) {
        // Fallback
      }
    }
    const raw = localStorage.getItem(`jaldoot_cache_${key}`);
    return raw ? JSON.parse(raw) : null;
  }
};
