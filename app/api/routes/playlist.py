from fastapi import APIRouter, Depends
from app.conect import get_all_playlists
from app.core.dependencies import get_current_user
from app.schemas.response import PlaylistsResponse

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get('')
async def getPlaylists(token_info: dict = Depends(get_current_user)):
    playlists = get_all_playlists(token_info)
    return PlaylistsResponse(ok=True, playlists=playlists)
