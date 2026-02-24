from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from app.config import config
from app.conect import login, createAccesToken, getTokenInfo

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get('/login')
async def start(request: Request,
                token_info: dict = Depends(getTokenInfo)):
    if token_info:  # If the token exists, send the logged to redirect the user to the app
        return JSONResponse({"ok": True, "logged": True}, status_code=200)
    else:
        url = login()
        return {"ok": True, "logged": False, "auth_url": url}


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
async def logout(request: Request,
                 token_info: dict = Depends(getTokenInfo)):
    request.session.clear()

    return JSONResponse({"ok": True}, status_code=200)
