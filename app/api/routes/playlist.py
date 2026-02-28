from fastapi import APIRouter, Depends
from app.conect import getTokenInfo, getPlaylist
from app.schemas.response import PlaylistsResponse

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get('')
async def getPlaylists(token_info: dict = Depends(getTokenInfo)):
    playlists = getPlaylist(token_info)
    return PlaylistsResponse(ok=True, playlists=playlists)
