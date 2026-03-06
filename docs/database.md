# Database Documentation

## Schema Overview

The database schema is optimized for caching Spotify/Deezer data and storing embeddings with **pgvector** for efficient similarity computations.

**Table relationships**:
- `songs_data` → `albums` (each song belongs to one album)
- `albums` ↔ `genres` (many-to-many via `album_genres` junction table)
- All tables use pgvector for 128D embeddings (songs and genres)

---

## Tables

### songs_data

Cached songs with Spotify metadata, Deezer enrichment, and **128D embeddings**.

```sql
CREATE TABLE songs_data (
    spotify_id TEXT PRIMARY KEY,
    deezer_id TEXT NOT NULL,
    name TEXT NOT NULL,
    duration INTEGER,
    explicit BOOLEAN,
    popularity INTEGER,
    rank INTEGER,
    album_id TEXT NOT NULL,
    artist_id TEXT,
    embedding vector(128),      -- pgvector: 128D song embedding
    embedding_ver INTEGER,      -- Model version for cache invalidation
    FOREIGN KEY (album_id) REFERENCES albums(id)
);
```

**Key columns**:
- `embedding`: Pre-computed 128D vector from PyTorch autoencoder
- `embedding_ver`: Tracks model version (invalidates cache on model updates)
- `rank`, `popularity`, `duration`: Used as input features for embeddings

**Indexes**:
```sql
CREATE INDEX idx_songs_album ON songs_data(album_id);
CREATE INDEX idx_songs_embedding_ver ON songs_data(embedding_ver);
```

---

### albums

Cached albums with Deezer enrichment and genre references.

```sql
CREATE TABLE albums (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,              -- "album", "single", "compilation"
    total_tracks INTEGER,
    release_date DATE,
    bpm FLOAT,              -- Deezer: beats per minute
    gain FLOAT,             -- Deezer: audio gain/loudness
    genres_id JSONB         -- Array of genre IDs (legacy, use album_genres)
);
```

**Key columns**:
- `bpm`, `gain`: Audio features from Deezer
- `genres_id`: JSONB array (e.g., `[12, 152, 465]`) for backward compatibility
- `type`: Encoded as feature for song embeddings

**Indexes**:
```sql
CREATE INDEX idx_albums_genres ON albums USING gin(genres_id);
```

---

### genres

Genre catalog with **128-dimensional embeddings** for semantic similarity.

```sql
CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    embedding vector(128)    -- pgvector: 128D genre embedding
);
```

**Key columns**:
- `embedding`: Pre-trained 128D vector (semantic representation)
- Used to compute album similarity via cosine similarity

**Indexes**:
```sql
-- IVFFlat index for approximate nearest neighbor search (optional, for large datasets)
CREATE INDEX idx_genres_embedding ON genres 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

---

### album_genres

**Many-to-many** relationship between albums and genres.

```sql
CREATE TABLE album_genres (
    album_id TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (album_id, genre_id),
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);
```

**Benefits**:
- Efficient joins for queries like "all albums in genre X"
- Supports cosine similarity computation across multiple genres per album
- Replaces need to parse `albums.genres_id` JSONB array

**Indexes**:
```sql
CREATE INDEX idx_album_genres_album ON album_genres(album_id);
CREATE INDEX idx_album_genres_genre ON album_genres(genre_id);
```

---

### artists

Artist metadata (present in schema but not actively used yet).

```sql
CREATE TABLE artists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
```

**Future use cases**:
- Artist embeddings
- Collaborative filtering (users who liked artist X also liked artist Y)
- Artist similarity graphs

---

## pgvector Extension

### Installation

PostgreSQL 16+ with pgvector extension is required.

**Linux/Mac**:
```bash
# Install via package manager or compile from source
# https://github.com/pgvector/pgvector
```

**Windows**:
Download pre-compiled binaries or use Docker with pgvector image.

**Enable extension**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

### Vector Operations

**Cosine distance operator** (`<=>`):
```sql
SELECT 1 - (embedding1 <=> embedding2) AS cosine_similarity
FROM songs_data;
```

**Example query** (find similar songs):
```sql
SELECT 
    s2.name,
    1 - (s1.embedding <=> s2.embedding) AS similarity
FROM songs_data s1
CROSS JOIN songs_data s2
WHERE s1.spotify_id = 'target_song_id'
  AND s2.spotify_id != 'target_song_id'
ORDER BY s1.embedding <=> s2.embedding
LIMIT 10;
```

---

### Indexing Strategies

**IVFFlat** (approximate nearest neighbor):
```sql
CREATE INDEX ON songs_data 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

- **Pros**: Fast approximate search (O(log n))
- **Cons**: Requires tuning `lists` parameter
- **Use case**: Large datasets (10k+ songs)

**HNSW** (hierarchical navigable small world):
```sql
CREATE INDEX ON songs_data 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

- **Pros**: Better recall than IVFFlat
- **Cons**: Slower index build
- **Use case**: Production deployments with frequent similarity queries

---

## Cache Strategy

### Song Caching

**Query** (check cache before API calls):
```python
cached_data, cached_names, invalid_songs, embeddings = (
    conn.consult_cached_song([track['track']['id'] for track in all_tracks])
)
```

**Flow**:
1. Query `songs_data` by Spotify IDs
2. Return songs with matching `embedding_ver`
3. Return `embeddings` (128D) and `cached_names` for filtering
4. Uncached songs → API fetch + process + insert

**Benefits**:
- Avoids redundant Spotify/Deezer API calls (~100ms per song)
- Embeddings pre-computed (no autoencoder forward pass)
- UMAP training possible on first batch if sufficient cached songs

---

### Album Caching

**Duplicate detection**:
```python
# In apiSpotify.py
if album_id in [album[0] for album in album_ids]:
    repeated_albums[album_id] = {'song': [spotify_id]}
```

**Query**:
```python
data, cached_albums = conn.consult_cached_albums([album_id for album in album_ids])
```

**Benefits**:
- Avoids fetching same album multiple times in a playlist
- Genres shared across songs from same album
- Reduced Deezer API calls (~50ms per album)

---

### Cache Invalidation

**Model version tracking**:
```python
# config.py
SONG_EMBEDDING_VERSION = 0

# postgresConnection.py
def insert_song(song_data):
    embedding_ver = config.get_embedding_version()
    # INSERT with embedding_ver...
```

**When to invalidate**:
- Autoencoder model updated (architecture or weights changed)
- Genre embeddings updated
- Feature engineering changed (new input features added)

**Invalidation strategy**:
1. Increment `SONG_EMBEDDING_VERSION` in config
2. Cached songs with old version are ignored (re-processed via API)
3. New embeddings cached with updated version

---

## Performance Characteristics

### Query Performance

| Operation | Sample Size | Time | Notes |
|-----------|-------------|------|-------|
| Cache lookup | 100 songs | ~10-20ms | Simple PK lookup |
| Embedding retrieval | 100 songs | ~50-100ms | Includes vector data |
| Album cache check | 50 albums | ~20-30ms | JSONB array search |
| Cosine similarity | 1000 pairs | ~500ms | Without index |
| Cosine similarity (indexed) | 1000 pairs | ~50-100ms | IVFFlat index |

### Storage Requirements

| Data Type | Per Item | 100 Songs | 10,000 Songs |
|-----------|----------|-----------|--------------|
| Song metadata | ~500 bytes | ~50 KB | ~5 MB |
| 128D embedding | 512 bytes | ~51 KB | ~5 MB |
| Album metadata | ~300 bytes | ~15 KB | ~1.5 MB |
| Genre embedding | 512 bytes | N/A | ~150 KB (300 genres) |

**Total estimate**: ~200-300 MB for 10k songs with full metadata and embeddings.

---

## Database Configuration

### Connection Pooling

**Recommended settings** (for production):
```python
# postgresConnection.py
import psycopg2.pool

pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host=config.POSTGRES_HOST,
    port=config.POSTGRES_PORT,
    database=config.POSTGRES_DB,
    user=config.POSTGRES_USER,
    password=config.POSTGRES_PASSWORD
)
```

**Benefits**:
- Reduces connection overhead (~50ms per connection)
- Enables concurrent requests
- Prevents connection exhaustion

---

### PostgreSQL Tuning

**For embedding workloads**:
```sql
-- postgresql.conf
shared_buffers = 256MB          -- Cache frequently accessed data
effective_cache_size = 1GB      -- Help query planner
work_mem = 64MB                 -- Sort/hash operations
maintenance_work_mem = 128MB    -- Index creation
```

**For pgvector operations**:
```sql
-- Increase work_mem for large vector operations
SET work_mem = '256MB';
```

---

## Backup & Restore

**Backup** (with pgvector data):
```bash
pg_dump -Fc graph_recomendation > backup.dump
```

**Restore**:
```bash
# Create extension first
psql graph_recomendation -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Restore data
pg_restore -d graph_recomendation backup.dump
```

**Notes**:
- pgvector extension must be installed before restore
- Vector indexes may need rebuilding after large restores
