# NotTorrent - Stremio Addon

> Buscador de torrents para películas y series. 100% estático, hospedado en GitHub Pages.

## Instalar en Stremio

1. Abrir Stremio → **Addons** → **Install Addon**
2. Introducir la URL:

```
https://moisesvvanti-dev.github.io/nottorrent/manifest.json
```

## Estructura de archivos

```
nottorrent/
├── manifest.json                    ← Stremio lee daqui
├── catalog/
│   ├── movie/nottorrent_movies.json
│   └── series/nottorrent_series.json
├── meta/
│   ├── movie/nottorrent_*.json      ← 10 películas
│   └── series/nottorrent_*.json      ← 10 series
├── stream/
│   ├── movie/nottorrent_*.json      ← streams por película
│   └── series/nottorrent_*.json      ← streams por serie
└── README.md
```

## Cómo funciona

El addon es **100% JSON estático**. Stremio solicita:

| Recurso | URL |
|---------|-----|
| Manifiesto | `/manifest.json` |
| Catálogo | `/catalog/{type}/{id}.json` |
| Metadata | `/meta/{type}/{id}.json` |
| Streams | `/stream/{type}/{id}.json` |

Cada stream tiene `infoHash` de torrent (para clientes BitTorrent) y `behaviorHints.open_in_webbrowser: true`.

## Añadir más películas/series

1. Editar `catalog/movie/nottorrent_movies.json` o `catalog/series/nottorrent_series.json`
2. Crear `meta/{type}/nottorrent_{id}.json` con datos de TMDB
3. Crear `stream/{type}/nottorrent_{id}.json` con los enlaces torrent

## Desplegar

Los cambios en `main` se publican automáticamente en GitHub Pages.

---

Inspirado en Dontorrent/Stremio. Disclaimer: solo búsqueda de enlaces.