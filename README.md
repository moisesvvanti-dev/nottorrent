# NotTorrent - Stremio Addon

A Stremio addon that provides torrent-based streaming for movies and series using public torrent search APIs and TMDB for metadata.

## Features

- **Movie Catalog**: Browse trending movies and search by title
- **Series Catalog**: Browse trending TV shows and search by title  
- **Torrent Streams**: Search and stream torrents directly in Stremio
- **TMDB Integration**: Rich metadata from The Movie Database
- **Episode Support**: Find specific episodes for TV series

## Installation

### Option 1: Deploy to Heroku (Recommended)

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Or manually:
```bash
heroku create nottorrent-addon
heroku push main master
heroku open
```

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/moisesvvanti/nottorrent.git
cd nottorrent

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

The server will start on `http://localhost:3000`

### Option 3: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repo
3. Deploy automatically

### Option 4: Deploy to Render

1. Go to [render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repo
4. Set start command: `gunicorn server:app`

## Adding to Stremio

1. Open Stremio
2. Go to **Addons** → **Install from URL**
3. Enter your addon URL (e.g., `https://your-addon.herokuapp.com/manifest.json`)
4. Click **Install**

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /manifest.json` | Addon manifest |
| `GET /catalog/<type>` | List movies or series (type: movie/series) |
| `GET /meta/<type>/<id>` | Get details for a specific item |
| `GET /stream/<type>/<id>` | Get torrent streams |

### Query Parameters for Catalog
- `search` - Search query
- `skip` - Pagination offset
- `genre` - Filter by genre

### Query Parameters for Stream
- `season` - Season number (for series)
- `episode` - Episode number (for series)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TMDB_API_KEY` | TMDB API key for metadata | Built-in demo key |
| `PORT` | Server port | 3000 |

## Free TMDB API Key

The addon includes a demo TMDB API key. For production, get your own free key at:
https://www.themoviedb.org/settings/api

## Technical Details

- **Framework**: Flask
- **Metadata**: TMDB API v3
- **Torrent Search**: TorrentAPI (torrentapi.org)
- **Streaming**: Magnet links with WebTorrent integration in Stremio

## Disclaimer

This addon is for educational purposes. Make sure you have the right to download/access the content before using this addon. The authors do not host any content and are not responsible for how the addon is used.

## License

MIT License