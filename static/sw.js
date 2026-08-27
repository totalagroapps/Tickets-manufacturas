self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Install');
});

self.addEventListener('fetch', (event) => {
    // Just a dummy pass-through fetch handler required for PWA installability
    event.respondWith(fetch(event.request));
});
