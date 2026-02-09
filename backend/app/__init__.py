from flask import Flask
from .config import Config
from .extensions import cors
from .models import db, bcrypt

from .api.health import bp as health_bp
from app.api.auth import auth_bp
from app.api.end_user.routes import end_user_bp
from app.api.cleaner.routes import cleaner_bp
from app.api.admin.routes import admin_bp
from app.api.profile import profile_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    bcrypt.init_app(app)

    # Health
    app.register_blueprint(health_bp, url_prefix="/api")

    # Authentication
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # Dashboard 
    app.register_blueprint(end_user_bp, url_prefix="/api/end-user")
    app.register_blueprint(cleaner_bp, url_prefix="/api/cleaner")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    
    # View / Update profile
    app.register_blueprint(profile_bp, url_prefix="/api")

    return app