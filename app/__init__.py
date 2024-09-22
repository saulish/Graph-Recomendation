from flask import Flask
from app.routes import main


def getApp(app):
    app.register_blueprint(main)

    