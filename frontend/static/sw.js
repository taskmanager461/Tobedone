const CACHE_NAME = "task-manager-v2";
const ASSETS_TO_CACHE = [
  "/",
  "/manifest.json",
  "/icon-192.png",
  "/icon-512.png",
  "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap"
];

// Install Event
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Caching app shell");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[Service Worker] Removing old cache", key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch Event
self.addEventListener("fetch", (event) => {
  // Only cache GET requests
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        // Cache new requests if they are from our origin or fonts
        if (
          networkResponse.ok &&
          (event.request.url.startsWith(self.location.origin) || 
           event.request.url.startsWith("https://fonts.googleapis.com"))
        ) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Fallback for offline (optional: return a custom offline page)
        return caches.match("/");
      });
    })
  );
});
