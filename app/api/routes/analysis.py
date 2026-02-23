from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.conect import getTokenInfo, start_process
from app.embeddings.model_inference import model

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/playlist/{playlist_id}")
async def analizePlaylist(request: Request, playlist_id: str):
    try:
        token_info = getTokenInfo(request)
        if not token_info:
            return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)
        if not playlist_id:
            return JSONResponse({"ok": False, "error": "invalid playlist"}, status_code=401)

    except Exception as e:
        print(f"Error taking the token: {e}")
        return JSONResponse({"ok": False, "Error": f"{e}"}, status_code=401)

    generator = start_process(token_info, playlist_id, model)
    return StreamingResponse(generator, media_type="application/x-ndjson")
