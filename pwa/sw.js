/* NutriVision Service Worker - 让网页可安装、可离线启动 */
const CACHE = "nutrivision-v1";

self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Streamlit 内部接口（websocket / 健康检查）不拦截
  if (url.pathname.startsWith("/_stcore/")) return;
  // 网络优先；失败时回退缓存（静态资源缓存，HTML 不缓存）
  e.respondWith(
    fetch(req)
      .then((resp) => {
        const copy = resp.clone();
        if (resp.ok && url.origin === self.location.origin && !url.pathname.endsWith("/")) {
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return resp;
      })
      .catch(() => caches.match(req))
  );
});
