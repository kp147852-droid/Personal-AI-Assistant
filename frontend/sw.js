self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request).catch(
      () =>
        new Response("Offline", {
          status: 503,
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        })
    )
  );
});
