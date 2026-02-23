from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from app.config import config
from app.conect import login, createAccesToken, getTokenInfo

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get('/login')
async def start(request: Request):
    try:
        token_info = getTokenInfo(request)
        if token_info:  # If the token exists, send the logged to redirect the user to the app
            return JSONResponse({"ok": True, "logged": True}, status_code=200)
        else:
            url = login()
            return {"ok": True, "logged": False, "auth_url": url}

    except Exception as e:
        print("Error in the token_info variable")
        return JSONResponse({"ok": False, "message": str(e)})


@router.get('/callback')
async def callback(request: Request):
    params = dict(request.query_params)
    # print(params)
    code = params.get("code")
    error = params.get("error")
    if error:
        return {"error": error}

    token_info = createAccesToken(code)
    request.session["token_info"] = token_info
    return RedirectResponse(f"http://127.0.0.1:{config.FRONTEND_PORT}/menu.html")


@router.get('/logout')
async def logout(request: Request):
    try:
        token_info = getTokenInfo(request)
        if token_info:
            request.session.clear()
    except Exception as e:
        print(f"Error deleting the token: {e}")
        return JSONResponse({"ok": False}, status_code=401)

    return JSONResponse({"ok": True}, status_code=200)
