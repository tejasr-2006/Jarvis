const CACHE = "jarvis-mobile-shell-v1";
const SHELL = ["/mobile", "/mobile/manifest.webmanifest", "/mobile/icon.svg"];
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  // Never cache API traffic, authentication, or personal responses.
  if (url.origin !== self.location.origin || !["GET", "HEAD"].includes(event.request.method)) return;
  if (url.pathname.startsWith("/tasks") || url.pathname.startsWith("/memory") ||
      url.pathname.startsWith("/briefing") || url.pathname.startsWith("/notifications") ||
      url.pathname.startsWith("/calendar") || url.pathname.startsWith("/command") ||
      url.pathname.startsWith("/operations")) return;
  if (SHELL.includes(url.pathname)) {
    event.respondWith(fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put(event.request, copy));
      return response;
    }).catch(() => caches.match(event.request)));
  }
});
