// Dabba Delivery App Service Worker
const CACHE_NAME = 'dabba-delivery-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/config.js',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    return; // Pass API requests directly
  }
  event.respondWith(
    caches.match(event.request).then((res) => res || fetch(event.request)).catch(() => caches.match('/'))
  );
});

