from pydantic import BaseModel
from typing import Optional, List


# Basic response, ok if the request was successful, error if there was an error
class StandardResponse(BaseModel):
    ok: bool
    error: Optional[str] = None


# Login response, extends StandardResponse and adds a `logged` flag
# if the user is not logged in, includes an `auth_url` for authentication
class LoginResponse(StandardResponse):
    logged: bool
    auth_url: Optional[str] = None


# Basic playlist item for the playlist response
class PlaylistItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    public: Optional[bool] = None
    collaborative: Optional[bool] = None
    images: Optional[List[dict]] = None
    tracks: Optional[dict] = None


# Playlists response, extends the standard and adds the list of playlists
class PlaylistsResponse(StandardResponse):
    playlists: Optional[List[PlaylistItem]] = None


# Analyze response, extends the standard and adds
# the list of songs and his info
class SongAnalysisItem(BaseModel):
    id: str
    x: Optional[float] = None
    y: Optional[float] = None
    song_name: str
    artists: List[str]
    album_name: str


# This is a list of analyzed songs, instead of being used in the response, is used in the creation of
# the payload
class SongAnalysisResponse(StandardResponse):
    songs: Optional[List[SongAnalysisItem]] = None
