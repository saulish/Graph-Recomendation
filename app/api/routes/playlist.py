from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.conect import getTokenInfo, getPlaylist

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get('/')
async def getPlaylists(request: Request):

    token_info = getTokenInfo(request)
    if not token_info:
        return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)

    playlists = getPlaylist(token_info)
    return JSONResponse({"ok": True, "playlists": playlists}, status_code=200)
