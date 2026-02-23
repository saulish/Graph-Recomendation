from .config import configApp
from fastapi import FastAPI
from app.api.routes import auth, playlist, analysis


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

        app.include_router(auth.router)
        app.include_router(playlist.router)
        app.include_router(analysis.router)
