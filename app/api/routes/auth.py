from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.config import config
from app.conect import login, createAccesToken, getTokenInfo
from app.schemas.response import LoginResponse, StandardResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get('/login')
async def start(token_info: dict = Depends(getTokenInfo)):
    if token_info:  # If the token exists, send the logged to redirect the user to the app
        return LoginResponse(ok=True, logged=True)
    else:
        url = login()
        return LoginResponse(ok=True, logged=False, auth_url=url)


@router.get('/callback')
async def callback(request: Request):
    params = dict(request.query_params)
    code = params.get("code")
    error = params.get("error")
    if error:
        return {"error": error}

    token_info = createAccesToken(code)
    request.session["token_info"] = token_info
    return RedirectResponse(f"http://127.0.0.1:{config.FRONTEND_PORT}/menu.html")


@router.get('/logout')
async def logout(request: Request, ):
    request.session.clear()
    return StandardResponse(ok=True)
