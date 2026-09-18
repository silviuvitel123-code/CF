// Deliberately does NOT cache anything: this app deploys with
// Cache-Control: no-cache on every route (see vercel.json) specifically so
// a build-version bump always reaches users immediately. A caching service
// worker would silently defeat that and leave people stuck on an old build.
// Its only job is to exist with a fetch handler, which is what Chrome/Edge
// require before they'll offer "Install app" on desktop.
self.addEventListener("install", function (e) {
  self.skipWaiting();
});
self.addEventListener("activate", function (e) {
  e.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", function (e) {
  e.respondWith(fetch(e.request));
});
