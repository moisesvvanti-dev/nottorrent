"""
NotTorrent - Stremio Addon
Torrent-based streaming addon for movies and series
"""

import os
import json
import re
import requests
from flask import Flask, jsonify, request, Response
from functools import wraps

app = Flask(__name__)

# TMDB API configuration
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', 'b53b0d0e4af7a2c49c9c6b96e60e9d9f')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Torrent search configuration
TORRENT_API_URL = 'https://torrentapi.org/pubapi.php'

# User agents for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9'
}

# In-memory cache
cache = {}
CACHE_TTL = 300  # 5 minutes


def get_tmdb_image_url(path, size='w500'):
    """Construct TMDB image URL"""
    if path:
        return f"https://image.tmdb.org/t/p/{size}{path}"
    return None


def search_torrents(query, category=None):
    """
    Search torrents using TorrentAPI
    Returns list of torrent results
    """
    try:
        # Get token first
        token_url = 'https://torrentapi.org/pubapi.php?get_token=get_token'
        token_response = requests.get(token_url, headers=HEADERS, timeout=10)
        if token_response.status_code != 200:
            return []
        
        token_data = token_response.json()
        token = token_data.get('token')
        if not token:
            return []
        
        # Search with token
        search_params = {
            'mode': 'search',
            'search_string': query,
            'token': token,
            'format': 'json',
            'limit': 20
        }
        
        if category == 'movie':
            search_params['category'] = 'movies'
        elif category == 'series':
            search_params['category'] = 'tv'
        
        response = requests.get(TORRENT_API_URL, params=search_params, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('torrent_results', [])
        return []
    except Exception as e:
        print(f"Torrent search error: {e}")
        return []


def get_tmdb_trending(media_type='movie', page=1):
    """Get trending movies or series from TMDB"""
    cache_key = f"trending_{media_type}_{page}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        url = f"{TMDB_BASE_URL}/trending/{media_type}/week"
        params = {
            'api_key': TMDB_API_KEY,
            'page': page
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            cache[cache_key] = result
            return result
    except Exception as e:
        print(f"TMDB trending error: {e}")
    return {'results': []}


def get_tmdb_search(media_type, query, page=1):
    """Search TMDB for movies or series"""
    cache_key = f"search_{media_type}_{query}_{page}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        url = f"{TMDB_BASE_URL}/search/{media_type}"
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'page': page
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            cache[cache_key] = result
            return result
    except Exception as e:
        print(f"TMDB search error: {e}")
    return {'results': []}


def get_tmdb_details(media_type, tmdb_id):
    """Get details for a specific movie or series"""
    cache_key = f"details_{media_type}_{tmdb_id}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}"
        params = {'api_key': TMDB_API_KEY}
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            cache[cache_key] = result
            return result
    except Exception as e:
        print(f"TMDB details error: {e}")
    return {}


def get_tmdb_season(series_id, season_number):
    """Get season details for a series"""
    cache_key = f"season_{series_id}_{season_number}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        url = f"{TMDB_BASE_URL}/tv/{series_id}/season/{season_number}"
        params = {'api_key': TMDB_API_KEY}
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            result = response.json()
            cache[cache_key] = result
            return result
    except Exception as e:
        print(f"TMDB season error: {e}")
    return {}


def build_torrent_stream(torrent, media_type, imdb_id=None):
    """Build a torrent stream URL from search result"""
    info = torrent.get('info', {})
    title = info.get('title', 'Unknown')
    
    # Use magnet link directly
    magnet = torrent.get('download')
    if not magnet or not magnet.startswith('magnet:'):
        return None
    
    # Construct stream URL - using info hash for better compatibility
    seeds = torrent.get('seeds', 0)
    peers = torrent.get('peers', 0)
    
    # Create a descriptive title
    size = torrent.get('size', 'Unknown')
    if isinstance(size, int):
        size_str = f"{size / (1024*1024*1024):.2f} GB" if size > 1024*1024*1024 else f"{size / (1024*1024):.2f} MB"
    else:
        size_str = size
    
    stream_title = f"{title} | Seeds: {seeds} | {size_str}"
    
    return {
        "name": "NotTorrent",
        "title": stream_title,
        "url": magnet,
        "type": "torrent",
        "behaviorHints": {
            "fileHash": info.get('hash'),
            "name": title,
            "seeders": seeds,
            "peers": peers
        }
    }


def convert_imdb_to_tmdb(imdb_id):
    """Convert IMDB ID to TMDB ID using TMDB API"""
    if not imdb_id:
        return None
    
    try:
        url = f"{TMDB_BASE_URL}/find/{imdb_id}"
        params = {'api_key': TMDB_API_KEY, 'external_source': 'imdb_id'}
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'movie_results' in data and data['movie_results']:
                return ('movie', data['movie_results'][0]['id'])
            if 'tv_results' in data and data['tv_results']:
                return ('series', data['tv_results'][0]['id'])
    except Exception as e:
        print(f"IMDB to TMDB conversion error: {e}")
    return None


def build_meta_item(tmdb_item, media_type):
    """Build a Stremio meta item from TMDB data"""
    tmdb_id = tmdb_item.get('id')
    
    # Generate IMDB ID if not present
    imdb_id = tmdb_item.get('imdb_id')
    if not imdb_id:
        imdb_id = f"tt{tmdb_id}"  # Fallback
    
    # Handle series name vs movie title
    name = tmdb_item.get('title') or tmdb_item.get('name', 'Unknown')
    year = tmdb_item.get('release_date', '')[:4] or (tmdb_item.get('first_air_date', '')[:4] if media_type == 'series' else '')
    
    genres = []
    for g in tmdb_item.get('genres', []):
        if isinstance(g, dict):
            genres.append(g.get('name', ''))
        else:
            genres.append(str(g))
    
    poster = get_tmdb_image_url(tmdb_item.get('poster_path'))
    background = get_tmdb_image_url(tmdb_item.get('backdrop_path'), size='w1280')
    
    item = {
        "id": f"tmdb_{tmdb_id}" if not imdb_id else imdb_id,
        "name": name,
        "type": media_type,
        "poster": poster,
        "background": background,
        "year": int(year) if year.isdigit() else None,
        "genres": genres,
        "imdbId": imdb_id,
        "tmdbId": str(tmdb_id)
    }
    
    # Add rating if available
    if tmdb_item.get('vote_average'):
        item["rating"] = round(tmdb_item['vote_average'] / 2, 1)  # Convert to 10-star scale
    
    # Add description
    if tmdb_item.get('overview'):
        item["description"] = tmdb_item['overview']
    
    return item


@app.route('/manifest.json', methods=['GET'])
def get_manifest():
    """Serve the addon manifest"""
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    return jsonify(manifest)


@app.route('/catalog/<type_>', methods=['GET'])
@app.route('/catalog/<type_>/<catalog_id>', methods=['GET'])
def get_catalog(type_, catalog_id=None):
    """Serve catalog of movies or series"""
    if type_ not in ['movie', 'series']:
        return jsonify({'metas': []})
    
    # Get query parameters
    search = request.args.get('search', '')
    skip = int(request.args.get('skip', 0))
    page = (skip // 20) + 1
    
    # Search or trending
    if search:
        tmdb_results = get_tmdb_search(type_, search, page)
    else:
        tmdb_results = get_tmdb_trending(type_, page)
    
    metas = []
    for item in tmdb_results.get('results', []):
        if item.get('media_type') == 'person':
            continue
        media_type = type_ if not item.get('media_type') else item['media_type']
        if media_type not in ['movie', 'tv']:
            continue
        meta = build_meta_item(item, 'movie' if media_type == 'movie' else 'series')
        if meta:
            metas.append(meta)
    
    return jsonify({'metas': metas})


@app.route('/meta/<type_>/<id>', methods=['GET'])
def get_meta(type_, id_):
    """Serve metadata for a specific movie or series"""
    if type_ not in ['movie', 'series']:
        return jsonify({'meta': None})
    
    # Check if it's TMDB or IMDB ID
    is_tmdb = id_.startswith('tmdb_')
    is_imdb = id_.startswith('tt')
    
    tmdb_id = None
    media_type = type_
    
    if is_tmdb:
        tmdb_id = id_.replace('tmdb_', '')
    elif is_imdb:
        result = convert_imdb_to_tmdb(id_)
        if result:
            media_type, tmdb_id = result
    else:
        # Assume it's just a number (TMDB ID)
        tmdb_id = id_
    
    if not tmdb_id:
        return jsonify({'meta': None})
    
    # Get details
    tmdb_type = 'movie' if media_type == 'movie' else 'tv'
    details = get_tmdb_details(tmdb_type, tmdb_id)
    
    if not details:
        return jsonify({'meta': None})
    
    meta = build_meta_item(details, media_type)
    
    # For series, add episodes info
    if media_type == 'series':
        meta["genres"] = meta.get("genres", [])
        meta["runtime"] = details.get('episode_run_time', [60])[0] if details.get('episode_run_time') else 60
        meta["status"] = details.get('status', 'Continuing')
        meta["numberOfSeasons"] = details.get('number_of_seasons', 0)
        
        # Include seasons info for easy navigation
        seasons = []
        for s in details.get('seasons', []):
            if s.get('season_number', 0) > 0:  # Skip special episodes season
                seasons.append({
                    "id": f"tmdb_{tmdb_id}_season_{s['season_number']}",
                    "name": s.get('name', f"Season {s['season_number']}"),
                    "season": s.get('season_number')
                })
        meta["seasons"] = seasons
    
    return jsonify({'meta': meta})


@app.route('/stream/<type_>/<id>', methods=['GET'])
def get_stream(type_, id_):
    """Serve torrent streams for a movie or series"""
    if type_ not in ['movie', 'series']:
        return jsonify({'streams': []})
    
    # Check if it's TMDB or IMDB ID
    is_tmdb = id_.startswith('tmdb_')
    is_imdb = id_.startswith('tt')
    
    tmdb_id = None
    media_type = type_
    
    if is_tmdb:
        tmdb_id = id_.replace('tmdb_', '')
    elif is_imdb:
        result = convert_imdb_to_tmdb(id_)
        if result:
            media_type, tmdb_id = result
    else:
        tmdb_id = id_
    
    # Get episode info if specified (for series)
    season_num = request.args.get('season', type=int)
    episode_num = request.args.get('episode', type=int)
    
    streams = []
    
    if tmdb_id:
        # Get title for search
        tmdb_type = 'movie' if media_type == 'movie' else 'tv'
        details = get_tmdb_details(tmdb_type, tmdb_id)
        
        if details:
            title = details.get('title') or details.get('name', '')
            year = (details.get('release_date') or details.get('first_air_date') or '')[:4]
            
            # Build search query
            search_query = f"{title} {year}" if year else title
            
            if season_num and episode_num:
                search_query = f"{title} S{season_num:02d}E{episode_num:02d}"
            elif season_num:
                search_query = f"{title} Season {season_num}"
            
            # Search torrents
            torrents = search_torrents(search_query, media_type)
            
            for torrent in torrents:
                stream = build_torrent_stream(torrent, media_type)
                if stream:
                    streams.append(stream)
    
    # If no streams found, do a broader search
    if not streams and tmdb_id:
        tmdb_type = 'movie' if media_type == 'movie' else 'tv'
        details = get_tmdb_details(tmdb_type, tmdb_id)
        if details:
            title = details.get('title') or details.get('name', 'Unknown')
            torrents = search_torrents(title, media_type)
            for torrent in torrents:
                stream = build_torrent_stream(torrent, media_type)
                if stream:
                    streams.append(stream)
    
    # Limit to top 10 streams
    return jsonify({'streams': streams[:10]})


@app.route('/', methods=['GET'])
def index():
    """Index page"""
    return jsonify({
        'name': 'NotTorrent Addon',
        'version': '1.0.0',
        'endpoints': [
            '/manifest.json',
            '/catalog/<type>',
            '/meta/<type>/<id>',
            '/stream/<type>/<id>'
        ]
    })


@app.after_request
def add_cors(response):
    """Add CORS headers"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)