// JalDoot Service Worker for Offline PWA Support
const CACHE_NAME = "jaldoot-v1-offline-cache";
const ASSETS_TO_CACHE = [
  "/",
  "/static/css/styles.css",
  "/static/js/config.js",
  "/static/js/i18n.js",
  "/static/js/storage.js",
  "/static/js/auth.js",
  "/static/js/map.js",
  "/static/js/fisherman.js",
  "/static/js/researcher.js",
  "/static/js/admin.js",
  "/static/js/app.js",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  "https://cdn.jsdelivr.net/npm/chart.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("Caching core app assets for offline marine safety...");
      return cache.addAll(ASSETS_TO_CACHE).catch(err => console.warn("Partial cache failure:", err));
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Pass API requests to network, fall back to offline cache
  if (event.request.url.includes("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ offline: true, message: "Network unavailable. Operating in offline cached mode." }),
          { headers: { "Content-Type": "application/json" } }
        );
      })
    );
    return;
  }

  // Stale-while-revalidate for static shell assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
