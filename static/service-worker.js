const CACHE_ESTATICO = "fincontrole-estatico-v1";
const ARQUIVOS_ESTATICOS = [
  "/static/css/style.css",
  "/static/js/main.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_ESTATICO).then((cache) => cache.addAll(ARQUIVOS_ESTATICOS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(
        chaves
          .filter((chave) => chave !== CACHE_ESTATICO)
          .map((chave) => caches.delete(chave))
      )
    )
  );
  self.clients.claim();
});

// Importante: nunca colocamos em cache páginas de despesas, cartões, dashboard
// etc. — são dados financeiros que mudam o tempo todo, e mostrar uma versão
// antiga guardada no celular poderia enganar o usuário. Só os arquivos
// estáticos (CSS, JS, ícones) usam cache; o resto sempre vai direto na rede.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const ehEstatico = ARQUIVOS_ESTATICOS.some((caminho) => url.pathname === caminho);

  if (ehEstatico) {
    event.respondWith(
      caches.match(event.request).then((resposta) => resposta || fetch(event.request))
    );
  }
  // Para tudo o resto (HTML com dados, POST de formulários), deixa passar
  // direto pra rede sem interceptar.
});
