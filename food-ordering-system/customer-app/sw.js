// Dabba Service Worker for PWA installation and offline resilience
const CACHE_NAME = 'dabba-customer-v1';
const ASSETS = [
    '/',
    '/index.html',
    '/config.js',
    '/manifest.json'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.map((k) => { if (k !== CACHE_NAME) return caches.delete(k); })
        ))
    );
    self.clients.claim();
});

self.addEventListener('fetch', (e) => {
    // Only cache GET requests for same origin or static files; pass API through network
    if (e.request.url.includes('/api/')) {
        return;
    }
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});

