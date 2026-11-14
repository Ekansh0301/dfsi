/*
 * Offline support for Circuit Coach. The in-browser engine needs no network, so once the app
 * has been opened it keeps working with no signal: pages come from the network when it is
 * there and from this cache when it is not. Calls to the engine service (another origin) are
 * never cached; the app falls back to its in-browser engine for those.
 */
const CACHE = "circuit-coach-v1";
const SHELL = ["./", "./index.html", "./icon.svg", "./manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

// On the first visit the page loads its scripts and styles before this worker takes over, so
// the page sends their addresses here once it is ready, and they are cached for offline use.
self.addEventListener("message", (event) => {
  const urls = (event.data && event.data.cache) || [];
  const same = urls.filter((u) => {
    try {
      return new URL(u).origin === self.location.origin;
    } catch {
      return false;
    }
  });
  event.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(same))
      .catch(() => undefined),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    // Pages: the newest version when online, the cached app when offline.
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("./index.html", copy));
          return res;
        })
        .catch(() => caches.match("./index.html")),
    );
    return;
  }

  // Scripts, styles, fonts and images: answer from the cache, refresh it in the background.
  event.respondWith(
    caches.match(req).then((cached) => {
      const fresh = fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fresh;
    }),
  );
});
