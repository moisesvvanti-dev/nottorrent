"""
NotTorrent - Stremio Addon
Buscador de torrents para películas y series.
"""
import os
import re
import json
import hashlib
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# ─── CONFIG ─────────────────────────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
# Si no tiene key, usa cache en memoria (limitado a búsquedas recientes)
tmdb_cache = {}

# Torrents válidos para streaming
GOOD_SEEDERS = 3
GOOD_SIZE_GB = 15  # máximo para evitar fakes grandes

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def safe_get(url, params=None, headers=None, timeout=10):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception:
        return None

def make_imdb_id(title, year=""):
    raw = f"{title}{year}".encode()
    return "tt" + hashlib.md5(raw).hexdigest()[:7]

def parse_size(size_str):
    """Convierte '1.45 GB' o '1450 MB' a GB"""
    if not size_str:
        return 0
    size_str = size_str.upper().strip()
    m = re.match(r"([\d.]+)\s*(GB|MB|TB)", size_str)
    if not m:
        return 0
    val = float(m.group(1))
    return val if "GB" in size_str else val / 1024

def get_tmdb_config():
    return {
        "imageBase": "https://image.tmdb.org/t/p/",
        "posterSizes": ["w92","w154","w185","w342","w500","w780","original"],
        "backdropSizes": ["w300","w780","w1280","original"],
    }

# ─── TMDB ─────────────────────────────────────────────────────────────────────
def tmdb_search(query, media_type="movie", year=""):
    if not TMDB_API_KEY:
        return tmdb_search_offline(query, media_type, year)
    
    base = "https://api.themoviedb.org/3"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "es-ES"}
    if year:
        params["primary_release_year"] = year
    
    url = f"{base}/search/{media_type}"
    r = safe_get(url, params=params)
    if not r:
        return []
    data = r.json()
    return data.get("results", [])[:10]

def tmdb_meta(tmdb_id, media_type):
    if not TMDB_API_KEY:
        return None
    base = "https://api.themoviedb.org/3"
    url = f"{base}/{media_type}/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "es-ES"}
    r = safe_get(url, params=params)
    if r:
        return r.json()
    return None

def tmdb_meta_local(title, year):
    key = f"{title}|{year}"
    if key in tmdb_cache:
        return tmdb_cache[key]
    return None

# ─── TORRENT SEARCH (usando 1337x) ─────────────────────────────────────────
def search_1337(query):
    """Busca en 1337x via proxy público."""
    proxies = [
        "https://1337x.unblocknation.com",
        "https://1337x.biturl.top",
    ]
    results = []
    for proxy in proxies:
        try:
            search_url = f"{proxy}/search/{query}/1/"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(search_url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            html = r.text
            # Parse resultados (simplificado)
            rows = re.findall(
                r'<a href="/torrent/([^"]+)">([^<]+)</a>.*?<td>([\d.]+ [A-Z]+)</td>.*?<td>([\d,]+)</td>',
                html, re.DOTALL
            )
            for row in rows[:10]:
                results.append({
                    "name": row[1],
                    "url": f"{proxy}/torrent/{row[0]}",
                    "size": row[2],
                    "seeders": int(row[3].replace(",","")) if row[3].isdigit() else 0,
                })
            break
        except Exception:
            continue
    return results

def search_torrent(query, media_type="movie"):
    """Busca torrents en múltiples fuentes."""
    all_results = []
    # 1337x
    for r in search_1337(query):
        all_results.append(r)
    # Fallback: torrentapi.org (sin key limita)
    try:
        url = f"https://torrentapi.org/pubapi.php?function=search&search={query}&category=movies"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("torrent_results", [])[:5]:
                all_results.append({
                    "name": item.get("title",""),
                    "url": item.get("download","") or item.get("magnet","") or "",
                    "size": item.get("size","Unknown"),
                    "seeders": item.get("seeders",0),
                })
    except Exception:
        pass
    return all_results

def best_torrent(torrents):
    """Filtra y ordena torrents por seeders y tamaño."""
    good = []
    for t in torrents:
        if t.get("seeders",0) >= GOOD_SEEDERS:
            size_gb = parse_size(t.get("size",""))
            if 0 < size_gb < GOOD_SIZE_GB:
                good.append((t["seeders"], size_gb, t))
    good.sort(key=lambda x: (-x[0], x[1]))
    return good[0][2] if good else torrents[0] if torrents else None

# ─── STREMIO ENDPOINTS ───────────────────────────────────────────────────────
@app.route("/manifest.json")
def manifest():
    with open("manifest.json", "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/catalog/<type_>/<catalog_id>.json")
def catalog(type_, catalog_id):
    return jsonify({"metas": []})

@app.route("/meta/<type_>/<id>.json")
def meta(type_, id_):
    # id formato: nottorrent_<tmdb_id>
    if not id_.startswith("nottorrent_"):
        return jsonify({"meta": {}})
    
    tmdb_id = id_.replace("nottorrent_","")
    
    # TMDB lookup
    if TMDB_API_KEY:
        data = tmdb_meta(tmdb_id, type_)
    else:
        data = tmdb_meta_local(id_, type_)
    
    if not data:
        return jsonify({"meta": {}})
    
    poster = ""
    if "poster_path" in data and data["poster_path"]:
        poster = f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    
    backdrop = ""
    if "backdrop_path" in data and data["backdrop_path"]:
        backdrop = f"https://image.tmdb.org/t/p/w1280{data['backdrop_path']}"
    
    name = data.get("title") or data.get("name","")
    overview = data.get("overview","")
    year = (data.get("release_date") or data.get("first_air_date","") or "")[:4]
    
    return jsonify({
        "meta": {
            "id": id_,
            "type": type_,
            "name": name,
            "poster": poster,
            "background": backdrop,
            "description": overview,
            "year": int(year) if year.isdigit() else None,
            "imdbId": make_imdb_id(name, year),
        }
    })

@app.route("/stream/<type_>/<id>.json")
def stream(type_, id_):
    # Extrae nombre de búsqueda del id o query param
    query = request.args.get("q","")
    search_query = request.args.get("search","")
    if not query and not search_query:
        return jsonify({"streams": []})
    
    q = query or search_query
    
    torrents = search_torrent(q, type_)
    best = best_torrent(torrents)
    
    streams = []
    if best:
        # Clasificar por idioma según nombre
        lang = "VOSE"
        name_lower = best["name"].lower()
        if "cast" in name_lower or "spanish" in name_lower or "espanol" in name_lower:
            lang = "CAST"
        elif "lat" in name_lower or "latino" in name_lower:
            lang = "LAT"
        elif "vos" in name_lower:
            lang = "VOS"
        elif "vo " in name_lower or name_lower.startswith("vo "):
            lang = "VO"
        
        info = f"[{lang}] 🌱 {best['seeders']} | {best['size']}"
        
        streams.append({
            "title": f"{lang} - {best['name'][:80]}",
            "infoHash": best.get("infoHash",""),
            "url": best.get("url",""),
            "availability": 1,
            "size": best.get("size",""),
            "seeds": best.get("seeders",0),
            "description": info,
            "icon": "https://i.postimg.cc/jLsFRmM9/dontorrent.png",
            "behaviorHints": {
                "filename": best["name"],
                "open_in_webbrowser": True,
            }
        })
    
    return jsonify({"streams": streams})

@app.route("/")
def index():
    return jsonify({
        "name": "NotTorrent",
        "version": "1.0.0",
        "description": "Stremio addon de torrents",
        "endpoints": ["/manifest.json", "/catalog/{type}/{id}.json", "/meta/{type}/{id}.json", "/stream/{type}/{id}.json"]
    })

# ─── RUN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7000))
    debug = os.getenv("FLASK_DEBUG","false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)