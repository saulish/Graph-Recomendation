from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.conect import getTokenInfo, getPlaylist

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get('')
async def getPlaylists(token_info: dict = Depends(getTokenInfo)):

    playlists = getPlaylist(token_info)
    return JSONResponse({"ok": True, "playlists": playlists}, status_code=200)
