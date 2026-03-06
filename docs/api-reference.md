# API Reference

## Endpoints

### Authentication (`/auth`)

#### `GET /auth/login`

Initiates OAuth flow or confirms existing session.

**Parameters**: None (reads from request session)

**Response**: `LoginResponse`
```json
{
  "ok": true,
  "logged": false,
  "auth_url": "https://accounts.spotify.com/authorize?..."
}
```

**Status Codes**:
- `200`: Success (returns logged status and auth_url if needed)

---

#### `GET /auth/callback`

OAuth callback endpoint. Exchanges authorization code for access token and redirects to frontend.

**Query Parameters**:
- `code` (string, required): Authorization code from Spotify
- `error` (string, optional): Error from OAuth provider

**Response**: `RedirectResponse` to `http://127.0.0.1:{FRONTEND_PORT}/menu.html`

**Status Codes**:
- `302`: Redirect to frontend on success
- `500`: Callback error
- `401`: Invalid or expired token

**Side Effects**: Stores `token_info` in session

---

#### `DELETE /auth/logout`

Clears user session.

**Authentication**: Not required

**Response**: `StandardResponse`
```json
{
  "ok": true
}
```

**Status Codes**:
- `200`: Session cleared successfully

---

### Playlists (`/playlists`)

#### `GET /playlists`

Lists user's Spotify playlists.

**Authentication**: Required (via `get_current_user` dependency)

**Response**: `PlaylistsResponse`
```json
{
  "ok": true,
  "playlists": [
    {
      "id": "37i9dQZF1DXcBWIGoYBM5M",
      "name": "Today's Top Hits",
      "description": "Ed Sheeran is on top...",
      "public": true,
      "collaborative": false,
      "images": [
        {
          "url": "https://i.scdn.co/image/...",
          "height": 300,
          "width": 300
        }
      ],
      "tracks": {
        "href": "https://api.spotify.com/v1/playlists/...",
        "total": 50
      }
    }
  ]
}
```

**Status Codes**:
- `200`: Success
- `401`: Invalid or expired token

---

### Analysis (`/analysis`)

#### `GET /analysis/playlist/{playlist_id}`

Analyzes playlist songs with embeddings. Returns streaming NDJSON response with progressive batches.

**Authentication**: Required (via `get_current_user` dependency)

**Path Parameters**:
- `playlist_id` (string, required): Spotify playlist ID

**Response**: `StreamingResponse` (NDJSON)

Each line is a JSON array of `SongAnalysisItem` objects:

```json
[
  {
    "id": "11dFghVXANMlKmJXsNCbNl",
    "x": 0.245,
    "y": -0.832,
    "song_name": "Cut To The Feeling",
    "artists": ["Carly Rae Jepsen"],
    "album_name": "Cut To The Feeling"
  },
  {
    "id": "3n3Ppam7vgaVa1iaRUc9Lp",
    "x": null,
    "y": null,
    "song_name": "Mr. Brightside",
    "artists": ["The Killers"],
    "album_name": "Hot Fuss"
  }
]
```

**Final message**:
```json
{"done": true}
```

**Status Codes**:
- `200`: Streaming started successfully
- `401`: Invalid or expired token

**Notes**:
- Coordinates (`x`, `y`) are `null` until UMAP reduction is performed
- Batches arrive progressively as processing completes
- Frontend should parse line-by-line (NDJSON format)

---

### Health Check

#### `GET /`

Server health check.

**Authentication**: Not required

**Response**: Plain JSON
```json
{
  "message": "Alive and running"
}
```

**Status Codes**:
- `200`: Server is operational

---

## Pydantic Schemas

All API responses follow standardized Pydantic models for validation and consistency.

### StandardResponse

Base response model for all endpoints.

```python
class StandardResponse(BaseModel):
    ok: bool                    # Request success status
    error: Optional[str] = None # Error message if ok=False
```

**Example** (success):
```json
{"ok": true}
```

**Example** (error):
```json
{"ok": false, "error": "Database connection failed"}
```

---

### LoginResponse

Authentication response.

```python
class LoginResponse(StandardResponse):
    logged: bool                 # User authentication status
    auth_url: Optional[str] = None # OAuth URL if not logged
```

**Example** (not logged):
```json
{
  "ok": true,
  "logged": false,
  "auth_url": "https://accounts.spotify.com/authorize?..."
}
```

**Example** (already logged):
```json
{
  "ok": true,
  "logged": true
}
```

---

### PlaylistItem

Individual playlist metadata.

```python
class PlaylistItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    public: Optional[bool] = None
    collaborative: Optional[bool] = None
    images: Optional[List[dict]] = None
    tracks: Optional[dict] = None
```

---

### PlaylistsResponse

List of user playlists.

```python
class PlaylistsResponse(StandardResponse):
    playlists: Optional[List[PlaylistItem]] = None
```

**Example**:
```json
{
  "ok": true,
  "playlists": [
    {
      "id": "37i9dQZF1DXcBWIGoYBM5M",
      "name": "Today's Top Hits",
      "description": "Ed Sheeran is on top...",
      "public": true,
      "collaborative": false,
      "images": [...],
      "tracks": {"total": 50}
    }
  ]
}
```

---

### SongAnalysisItem

Individual song analysis result with 2D coordinates.

```python
class SongAnalysisItem(BaseModel):
    id: str                      # Spotify track ID
    x: Optional[float] = None    # UMAP 2D coordinate
    y: Optional[float] = None    # UMAP 2D coordinate
    song_name: str
    artists: List[str]
    album_name: str
```

**Example**:
```json
{
  "id": "11dFghVXANMlKmJXsNCbNl",
  "x": 0.245,
  "y": -0.832,
  "song_name": "Cut To The Feeling",
  "artists": ["Carly Rae Jepsen"],
  "album_name": "Cut To The Feeling"
}
```

**Notes**:
- `x` and `y` are `null` until UMAP reduction is performed
- Coordinates represent semantic similarity in 2D space
- Distance between points indicates song similarity

---

## Error Handling

The API follows a standardized error handling pattern across all endpoints.

### Authentication Errors (401)

**Trigger**: Missing or expired session token

**Response**:
```json
{
  "detail": "Invalid or expired token"
}
```

**Handled by**: `get_current_user` dependency injection

**Example**:
```bash
curl -X GET http://localhost:8000/playlists
# Response: 401 Unauthorized
{"detail": "Invalid or expired token"}
```

---

### Validation Errors (422)

**Trigger**: Pydantic validation failure (incorrect types, missing required fields)

**Response**: FastAPI automatic validation error format
```json
{
  "detail": [
    {
      "loc": ["body", "playlist_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Handled by**: FastAPI + Pydantic automatically

---

### Business Logic Errors

**Trigger**: Application-level errors (database failures, API errors, etc.)

**Response**: `StandardResponse` with `ok=False`
```json
{
  "ok": false,
  "error": "Playlist not found"
}
```

**Handled by**: Custom error handling in route handlers

---

### HTTP Exceptions (500, etc.)

**Trigger**: Critical errors (database connection, unhandled exceptions)

**Response**:
```json
{
  "detail": "Internal server error"
}
```

**Handled by**: FastAPI's `HTTPException`

**Example**:
```python
if not token_info:
    raise HTTPException(status_code=500, detail="Failed callback")
```

---

## OpenAPI/Swagger Documentation

FastAPI automatically generates interactive API documentation at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Benefits

1. **Interactive testing**: Try endpoints directly from browser
2. **Schema validation**: See request/response models
3. **Authentication testing**: Test with real OAuth tokens
4. **Auto-generated**: No manual documentation maintenance

### Tags

Endpoints are organized by tags for clarity:

- `authentication`: Login, callback, logout
- `playlists`: Playlist listing
- `analysis`: Song analysis and embeddings

---

## CORS Configuration

The API is configured to accept requests only from the frontend origin:

```python
# config.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security notes**:
- `allow_credentials=True` enables cookie-based sessions
- Origin restricted to localhost frontend (dev configuration)
- Production deployment should use HTTPS and proper domain

---

## Session Management

Sessions are managed via `SessionMiddleware` with cookie-based storage:

```python
# config.py
app.add_middleware(
    SessionMiddleware,
    secret_key="miau",           # TODO: Use environment variable in production
    session_cookie="session",
    same_site="lax",             # Only dev (should be "strict" in production)
    https_only=False             # Only dev (should be True in production)
)
```

**Session data**:
- `token_info`: Spotify access/refresh tokens and expiry
- Stored in encrypted cookie (client-side)
- Automatically refreshed when expired (via `get_token_info`)

**Security recommendations for production**:
- Use `secrets.token_urlsafe(32)` for `secret_key`
- Set `same_site="strict"` and `https_only=True`
- Consider Redis-backed sessions for multi-instance deployments
