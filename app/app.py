from fastapi import FastAPI
from app.config import configApp
from app.api.routes import auth, playlist, analysis


class App:
    def __call__(self):
        app = FastAPI()
        configApp(app)
        self.define_routes(app)
        return app

    def define_routes(self, app: FastAPI):
        @app.get("/")
        async def saludo():
            return {"message": f'Alive and running'}

        app.include_router(auth.router)
        app.include_router(playlist.router)
        app.include_router(analysis.router)
