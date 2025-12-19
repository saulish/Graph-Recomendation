from .conect import login, createAccesToken, getTokenInfo, getPlaylist, getData
from .config import config, configApp
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse



class App:
    def __call__(self):
        app = FastAPI()
        configApp(app)
        self.defineRoutes(app)
        return app

    def defineRoutes(self, app: FastAPI):
        @app.get("/")
        async def saludo():
            return {"message": f'Alive and running'}

        @app.get('/login')
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

        @app.get('/callback')
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

        @app.get('/playlists')
        async def getPlaylists(request: Request):

            token_info = getTokenInfo(request)
            if not token_info:
                return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)

            playlists = getPlaylist(token_info)
            return JSONResponse({"ok": True, "playlists": playlists}, status_code=200)

        @app.post('/logout')
        async def logout(request: Request):
            try:
                token_info = getTokenInfo(request)
                if token_info:
                    request.session.clear()
            except Exception as e:
                print(f"Error deleting the token: {e}")
                return JSONResponse({"ok": False}, status_code=401)

            return JSONResponse({"ok": True}, status_code=200)

        @app.get('/analizePlaylist')
        def analizePlaylist(request: Request, id: str | None = None):
            try:
                token_info = getTokenInfo(request)
                if not token_info:
                    return JSONResponse({"ok": False, "error": "invalid token"}, status_code=401)
                playlist_id = id or request.query_params.get("playlist_id")
                if not playlist_id:
                    return JSONResponse({"ok": False, "error": "invalid playlist"}, status_code=401)

            except Exception as e:
                print(f"Error taking the token: {e}")
                return JSONResponse({"ok": False, "Error": f"{e}"}, status_code=401)

            generator = getData(token_info, playlist_id)
            return StreamingResponse(generator, media_type="application/x-ndjson")
