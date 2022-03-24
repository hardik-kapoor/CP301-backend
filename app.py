from flask import Flask
from views.auth import auth
from views.bookexchange import bookExchange
from db import db

def createApp(config_file="settings.py"):
    app = Flask(__name__)

    app.config.from_pyfile(config_file)

    db.init_app(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                            'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    app.register_blueprint(auth)
    app.register_blueprint(bookExchange)

    return app
