# Graph Recommendation - Spotify Playlist Analysis

**Backend API for analyzing Spotify playlists with song embeddings and similarity visualization**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)

## Features

- **Spotify OAuth Integration** - Secure user authentication with Spotipy
- **Song Embeddings** - 128D vectors via PyTorch autoencoder (audio + genre features)
- **2D Visualization** - UMAP dimensionality reduction for interactive frontend
- **Smart Caching** - PostgreSQL with pgvector for fast embedding lookups
- **Parallel Processing** - Producer-consumer architecture with asyncio.Queue
- **Streaming Responses** - NDJSON batches for progressive rendering
- **Deezer Enrichment** - BPM, gain, rank, and genre data

---

## Quick Start

### Prerequisites

- Python 3.10+ (3.11 recommended)
- PostgreSQL 16+ with [pgvector extension](https://github.com/pgvector/pgvector)
- Spotify Developer credentials ([Get them here](https://developer.spotify.com/dashboard))

### Installation

1. **Clone repository**:
```bash
git clone https://github.com/saulish/GR_back.git
cd GR_back
```

2. **Install dependencies**:
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

3. **Setup database**:
```bash
# Create database
createdb graph_recomendation

# Run schema
psql graph_recomendation < db/schema.sql
```

4. **Configure environment** (`app/.env`):
```env
SPOTIFY_API_KEY=your_client_id
SPOTIFY_API_SECRET=your_client_secret

FRONT_PORT=5500
BACK_PORT=8000

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=graph_recomendation
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

5. **Run server**:
```bash
python run.py
```

6. **Test**:
```bash
curl http://127.0.0.1:8000/
# Response: {"message":"Alive and running"}
```

---

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate OAuth or check session
- `GET /auth/callback` - OAuth callback (redirects to frontend)
- `DELETE /auth/logout` - Clear session

### Playlists
- `GET /playlists` - List user's Spotify playlists (requires auth)

### Analysis
- `GET /analysis/playlist/{id}` - Analyze playlist with embeddings (streaming NDJSON)

### Health
- `GET /` - Server status

> **Full API documentation**: See [docs/api-reference.md](docs/api-reference.md) for detailed schemas and examples

---

## How It Works

1. **User authenticates** with Spotify OAuth
2. **Backend fetches** playlist tracks from Spotify API
3. **Cache check**: Queries PostgreSQL for existing embeddings
4. **Enrichment** (uncached tracks): Concurrent Deezer API calls for BPM, gain, genres
5. **Embedding generation**: PyTorch autoencoder creates 128D vectors
6. **Dimensionality reduction**: UMAP reduces to 2D for visualization
7. **Streaming**: Progressive NDJSON batches sent to frontend

### Processing Flow

```
User Request → cache_producer (DB) ─┐
                                    ├─→ Queue → consumer_main → Frontend
               api_producer (APIs) ─┘
               
- cache_producer: Instant results from cached songs
- api_producer: Parallel Spotify/Deezer calls for uncached songs
- Both feed into shared queue for streaming response
```

> **Architecture details**: See [docs/architecture.md](docs/architecture.md)

---

## Song Embeddings

Each song is represented as a **128-dimensional vector** combining:

| Feature Type | Dimensions | Source |
|--------------|------------|--------|
| Audio features | 9 | BPM, gain, duration, popularity, etc. |
| Genre embeddings | 128 | Pre-trained genre vectors (weighted avg) |

**Autoencoder architecture**:
- Input: 137D (9 audio + 128 genre)
- Encoder: Dense layers → **128D bottleneck**
- Decoder: Symmetric reconstruction

**UMAP reduction** (128D → 2D):
- Enables interactive visualization
- Preserves local/global structure
- Optimized: Fit once, transform many (~10-50x faster)

> **Technical details**: See [docs/embeddings.md](docs/embeddings.md)

---

## Frontend

This backend is designed for interactive visualization. Frontend repository:

**https://github.com/saulish/Graph-Recomendation-Frontend**

**Response format** (NDJSON):
```json
[
  {
    "id": "spotify_track_id",
    "x": 0.25,
    "y": -0.83,
    "song_name": "Track Name",
    "artists": ["Artist 1"],
    "album_name": "Album Name"
  }
]
{"done": true}
```

---

## Configuration

### Performance Tuning

Edit `app/config.py` to adjust batch processing:

```python
BATCH_SIZE = 20              # Songs per API batch
MIN_UMAP_SIZE = 3            # UMAP execution frequency
MIN_UMAP_BATCH_SIZE = 60     # Min songs for UMAP
MIN_FIT_SONGS = 40           # Min cached songs to train UMAP
MAX_QUEUE_SIZE = 5           # Queue buffer size
```

**Recommendations**:
- Increase `BATCH_SIZE` for faster processing (watch for rate limits)
- Decrease `MIN_UMAP_SIZE` for more frequent frontend updates
- Adjust `MIN_FIT_SONGS` based on typical cache hit rate

---

## Database

The system uses PostgreSQL with **pgvector extension** for embedding storage and similarity queries.

### Key Tables

| Table | Purpose |
|-------|---------|
| `songs_data` | Cached songs with 128D embeddings |
| `albums` | Album metadata (BPM, gain, genres) |
| `genres` | Genre catalog with 128D embeddings |
| `album_genres` | Many-to-many album ↔ genres |

### pgvector Usage

```sql
-- Find similar songs via cosine similarity
SELECT name, 1 - (embedding <=> target_embedding) AS similarity
FROM songs_data
ORDER BY embedding <=> target_embedding
LIMIT 10;
```

> **Database details**: See [docs/database.md](docs/database.md) for schema and optimization

---

## Project Structure

```
app/
├── api/
│   └── routes/
│       ├── auth.py          # Authentication endpoints
│       ├── playlist.py      # Playlist management
│       └── analysis.py      # Song analysis
├── core/
│   └── dependencies.py      # Dependency injection (auth)
├── schemas/
│   └── response.py          # Pydantic response models
├── embeddings/
│   ├── model_architecture.py
│   └── model_inference.py   # PyTorch autoencoder + UMAP
├── models/
│   └── song_encoder.pth     # Trained model weights
├── app.py                   # Main FastAPI application
├── config.py                # Configuration & middleware
├── conect.py                # Spotify/Deezer API logic
├── apiSpotify.py            # Producer-consumer implementation
└── postgresConnection.py    # Database connection

db/
└── schema.sql               # PostgreSQL schema with pgvector

docs/
├── architecture.md          # Producer-consumer & UMAP optimization
├── embeddings.md            # Song/genre embeddings technical details
├── api-reference.md         # Complete API documentation
└── database.md              # PostgreSQL schema & pgvector usage
```

---

## Development

### Interactive API Docs

FastAPI provides auto-generated documentation:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Running Tests

```bash
# TODO: Add test suite (Phase 1 roadmap)
pytest tests/
```

### Code Quality

Recent refactoring improvements:
- Modular endpoints with APIRouter (auth, playlists, analysis)
- Pydantic schemas for validation and error handling
- Dependency injection for authentication
- Standardized error responses

---

## Roadmap

### Completed

- Spotify OAuth with session management
- Song embeddings (PyTorch autoencoder + UMAP)
- Genre embeddings with pgvector
- Producer-consumer parallel processing
- PostgreSQL caching with model versioning
- Endpoint refactoring (modular structure)
- Pydantic schemas & dependency injection

### In Progress

**Phase 1: Testing & Logging**
- [ ] Structured logging (JSON logs with request tracing)
- [ ] Test suite (unit, integration, endpoint tests)

**Phase 2: Scalability**
- [ ] Redis for session storage (multi-instance support)
- [ ] Connection pooling optimization
- [ ] Rate limiting for API endpoints

**Phase 3: Recommendations**
- [ ] Song recommendation system (cosine similarity)
- [ ] Similar songs endpoint
- [ ] Playlist generation based on seed songs

**Phase 4: Infrastructure**
- [ ] Docker containerization
- [ ] CI/CD pipeline (automated testing & deployment)
- [ ] Production-ready configuration

---

## Troubleshooting

### Common Issues

**"Invalid or expired token"**
- Check browser cookies
- Ensure frontend origin matches CORS settings in `config.py`
- Re-authenticate via `/auth/login`

**Database connection errors**
- Verify PostgreSQL is running
- Check `app/.env` credentials
- Ensure database exists: `createdb graph_recomendation`

**pgvector extension not found**
- Install extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Check PostgreSQL version (16+ recommended)

**Deezer API empty results**
- Some tracks may not exist in Deezer catalog
- System automatically skips and continues processing

---

## Performance

**Typical analysis times** (100-song playlist):

| Scenario | Time | Cache Hit Rate |
|----------|------|----------------|
| 100% cached | ~1-2s | 100% |
| 50% cached | ~15-20s | 50% |
| 0% cached | ~30-40s | 0% |

**Optimizations**:
- Producer-consumer: ~2-3x faster first batch
- UMAP fit-once: ~90% reduction in overhead
- PostgreSQL cache: ~100ms for 100+ embeddings

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Related Projects

- **Frontend**: https://github.com/saulish/Graph-Recomendation-Frontend
- **Documentation**: https://github.com/saulish/GR_back/tree/main/docs
- **pgvector**: https://github.com/pgvector/pgvector

---

## Support

For detailed documentation, see the `docs/` folder:

- [Architecture Documentation](docs/architecture.md)
- [Embeddings Technical Details](docs/embeddings.md)
- [API Reference](docs/api-reference.md)
- [Database Schema](docs/database.md)

Questions? Open an issue on GitHub!

---

*Built with FastAPI, PyTorch, PostgreSQL*

