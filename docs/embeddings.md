# Embeddings Documentation

## Song Embeddings (PyTorch Autoencoder)

The system generates **128-dimensional embeddings per song** using a PyTorch-trained neural autoencoder, combining audio features with genre embeddings to capture multidimensional similarity.

### Model Architecture

**Input Layer**: 137 dimensions
- 9 numeric audio/metadata features
- 128 dimensions from genre embeddings (weighted average)

**Encoder Path**:
```
Input (137) 
  → Dense (256) + LeakyReLU + BatchNorm + Dropout
  → Dense (256) + LeakyReLU + BatchNorm + Dropout
  → Dense (128) + LeakyReLU + BatchNorm + Dropout  ← Final embedding
  → Dense (64) + LeakyReLU + BatchNorm + Dropout
```

**Decoder Path** (symmetric reconstruction):
```
Latent (64)
  → Dense (128) + LeakyReLU + BatchNorm + Dropout
  → Dense (256) + LeakyReLU + BatchNorm + Dropout
  → Dense (256) + LeakyReLU + BatchNorm + Dropout
  → Output (137)
```

### Input Features (9 dimensions)

| Feature | Source | Description |
|---------|--------|-------------|
| `rank` | Deezer | Song popularity/chart performance |
| `popularity` | Spotify | Global popularity score (0-100) |
| `duration` | Spotify | Track length in milliseconds |
| `bpm` | Deezer | Beats per minute (tempo) |
| `gain` | Deezer | Audio gain/loudness |
| `album_type` | Spotify | Single/Album/Compilation (encoded) |
| `number_songs` | Spotify | Total tracks in album |
| `explicit` | Spotify | Explicit content flag (0/1) |
| `release_year` | Spotify | Album release year |

### Genre Embeddings (128 dimensions)

Each song inherits embeddings from its album's genres:

1. **Lookup**: Query `genres` table for all genre IDs in `album.genres_id` (JSONB array)
2. **Averaging**: Compute mean vector across all genre embeddings
3. **Weighting**: Multiply by **2.0** for songs with genres, **0.1** for songs without genres

```python
# Pseudocode
if len(genres) > 0:
    genre_embedding = np.mean([genre_vectors[gid] for gid in genres], axis=0)
    weighted_embedding = genre_embedding * 2.0
else:
    weighted_embedding = np.zeros(128) * 0.1
```

### Preprocessing

**Normalization**:
- `StandardScaler` applied to all 9 numeric features
- Fitted on training dataset, applied consistently to new songs

**Imputation**:
- Missing `bpm` values filled with median BPM from training set
- Missing `gain` values filled with 0.0 (Deezer default)

**Differential weighting**:
- Songs **with genres**: `genre_embedding × 2.0` (emphasize genre information)
- Songs **without genres**: `genre_embedding × 0.1` (de-emphasize empty vector)

### Training Process

The autoencoder was trained on a dataset of ~10,000 songs with the following hyperparameters:

- **Loss function**: Mean Squared Error (MSE)
- **Optimizer**: Adam (lr=0.001)
- **Batch size**: 64
- **Epochs**: 100 with early stopping
- **Validation split**: 20%
- **Dropout**: 0.3 (regularization)
- **Activation**: LeakyReLU (alpha=0.01)

### Model Output

The **128-dimensional bottleneck layer** serves as the final song embedding:
- Captures compressed representation of audio + genre features
- Semantically meaningful: similar songs have closer embeddings (cosine similarity)
- Cached in `songs_data.embedding` column (PostgreSQL `vector(128)`)

### PostgreSQL Cache

**Storage**:
```sql
songs_data.embedding vector(128)  -- Pre-computed 128D embedding
songs_data.embedding_ver integer  -- Model version for cache invalidation
```

**Benefits**:
- Avoid recomputation for cached songs (~100ms for 100+ embeddings)
- Forward pass through autoencoder only needed once per song
- Model version tracking allows cache invalidation on model updates

---

## Genre Embeddings & pgvector

The system uses **128-dimensional genre embeddings** to compute semantic similarity between albums based on their musical genres.

### Database Schema

**genres table**:
```sql
CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    embedding vector(128)  -- pgvector extension
);
```

**album_genres table** (many-to-many):
```sql
CREATE TABLE album_genres (
    album_id TEXT NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (album_id, genre_id),
    FOREIGN KEY (album_id) REFERENCES albums(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
);
```

### Cosine Similarity Computation

The system computes **average genre embedding** for each album and calculates cosine similarity:

```sql
-- Pseudocode SQL function
CREATE FUNCTION consult_cosine_similarity(album_id_1, album_id_2) RETURNS FLOAT AS $$
    -- Get average embedding for album 1
    SELECT AVG(g.embedding) INTO avg_emb_1
    FROM album_genres ag
    JOIN genres g ON ag.genre_id = g.id
    WHERE ag.album_id = album_id_1;
    
    -- Get average embedding for album 2
    SELECT AVG(g.embedding) INTO avg_emb_2
    FROM album_genres ag
    JOIN genres g ON ag.genre_id = g.id
    WHERE ag.album_id = album_id_2;
    
    -- Compute cosine similarity via pgvector operator
    RETURN 1 - (avg_emb_1 <=> avg_emb_2);  -- <=> is cosine distance operator
$$ LANGUAGE plpgsql;
```

### Benefits

1. **Semantic understanding**: "jazz" and "blues" are closer than "jazz" and "death metal"
2. **Efficient joins**: Many-to-many table allows fast queries for albums sharing genres
3. **Vector operations**: pgvector's `<=>` operator uses optimized SIMD instructions
4. **Recommendation quality**: Graph edge weights benefit from genre similarity

### pgvector Setup

**Requirements**:
- PostgreSQL 16+ (recommended for latest pgvector optimizations)
- pgvector extension compiled for your platform (Windows builds available)

**Installation**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Index creation** (optional but recommended for large datasets):
```sql
CREATE INDEX ON genres USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## UMAP Dimensionality Reduction (128D → 2D)

UMAP (Uniform Manifold Approximation and Projection) reduces 128D embeddings to 2D for interactive visualization.

### UMAP Configuration

```python
import umap

reducer = umap.UMAP(
    n_components=2,        # Output dimensionality
    n_neighbors=15,        # Balance local vs global structure
    min_dist=0.1,          # Minimum spacing between points
    metric="cosine",       # Distance metric (matches embedding training)
    random_state=42        # Reproducibility
)
```

### Parameter Tuning

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `n_components` | 2 | 2D visualization for frontend scatter plot |
| `n_neighbors` | 15 | Balances local clustering vs global structure |
| `min_dist` | 0.1 | Allows tight clusters without excessive overlap |
| `metric` | cosine | Matches autoencoder training objective |
| `random_state` | 42 | Ensures reproducibility across runs |

**Adaptive `n_neighbors`**:
```python
def set_reducer(self, n):
    n_neighbors = min(15, n - 1)  # UMAP requires n_neighbors < n
    self.umap_reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=0.1,
        metric="cosine",
        random_state=42
    )
```

### Edge Case Handling

UMAP requires **n ≥ 3** samples. The system handles edge cases:

```python
def reduct(self, embeddings, fit=False):
    n = len(embeddings)
    
    if n == 0:
        return np.empty((0, 2))  # Empty result
    
    if n == 1:
        return np.array([[0.0, 0.0]])  # Single point at origin
    
    if n == 2:
        return np.array([[-1.0, 0.0], [1.0, 0.0]])  # Horizontal line
    
    # n >= 3: Normal UMAP processing
    # ...
```

### Frontend Integration

**NDJSON streaming format**:
```json
[
  {
    "id": "spotify_track_id",
    "x": 0.245,
    "y": -0.832,
    "song_name": "Track A",
    "artists": ["Artist 1"],
    "album_name": "Album Name"
  }
]
```

**Visualization benefits**:
- **Distance = Similarity**: Nearby points represent similar songs
- **Clusters**: Groups of songs with similar audio/genre characteristics
- **Progressive rendering**: Frontend can display partial results as batches arrive
- **Interactive exploration**: Pan/zoom to explore song relationships

### Performance Characteristics

| Operation | Complexity | Time (100 songs) | Time (1000 songs) |
|-----------|------------|------------------|-------------------|
| `fit_transform()` | O(n²) | ~2-3s | ~20-30s |
| `transform()` | O(n) | ~0.1-0.2s | ~1-2s |

**Key insight**: `transform()` is **~10-50x faster** than `fit_transform()`, which is why the fit-once pattern provides dramatic performance improvements.
