from flask import Flask
from .config import Config
from .extensions import cors

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    from .api.health import bp as health_bp
    app.register_blueprint(health_bp, url_prefix="/api")

    return app
