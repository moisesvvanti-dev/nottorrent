# NotTorrent - Stremio Addon

Buscador de torrents para películas y series integrado con Stremio.

## Características

- 🔍 Búsqueda de torrents en múltiples fuentes (1337x, torrentapi)
- 🎬 Soporte para películas y series
- 🌐 Información de TMDB (título, póster, descripción)
- 🌍 Clasificación por idioma (CAST, LAT, VO, VOS, VOSE)
- 🔗 Enlaces magnet y URLs de torrent
- 📺 Streams compatibles con Stremio

## Instalación

### Opción 1: Instalar como addon en Stremio

1. Abrir Stremio
2. Ir a **Addons** > **Install Addon**
3. Introducir la URL del addon:
   ```
   https://tu-servidor.com/manifest.json
   ```

### Opción 2: Ejecutar localmente

```bash
git clone https://github.com/moisesvvanti/nottorrent.git
cd nottorrent
pip install -r requirements.txt
# Configurar TMDB_API_KEY como variable de entorno (opcional)
export TMDB_API_KEY="tu_key_de_tmdb"
python server.py
```

### Opción 3: Deploy en Railway / Render / Heroku

1. Subir este repo a GitHub
2. Conectar en Railway/Render
3. Establecer variable `TMDB_API_KEY` (opcional)
4. Deploy automático

## Configuración

### Variables de entorno

| Variable | Descripción | Opcional |
|----------|-------------|----------|
| `TMDB_API_KEY` | API Key de TheMovieDB para información extra | Sí |
| `PORT` | Puerto del servidor (default: 7000) | Sí |
| `FLASK_DEBUG` | Modo debug (default: false) | Sí |

### Obtener TMDB API Key

1. Ir a [themoviedb.org](https://www.themoviedb.org/)
2. Crear cuenta y solicitar API Key
3. Usar la API Key v3 en la variable de entorno

## Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `GET /manifest.json` | Manifiesto del addon |
| `GET /catalog/{type}/{id}.json` | Catálogo de películas/series |
| `GET /meta/{type}/{id}.json` | Metadata de una película/serie |
| `GET /stream/{type}/{id}.json` | Enlaces de torrent/stream |

## Estructura del proyecto

```
nottorrent/
├── manifest.json    # Manifiesto Stremio
├── server.py       # Servidor Flask
├── requirements.txt # Dependencias
└── README.md       # Este archivo
```

## Limitaciones

- Sin TMDB API Key: funcionalidad limitada a búsqueda básica
- Los torrents requieren cliente BitTorrent externo
- Algunos proveedores pueden requerir cookies para acceso

## Disclaimer

Este addon es solo para búsqueda de enlaces. El usuario es responsable del uso que haga de los enlaces encontrados.

---

Hecho con ❤️ para la comunidad Stremio