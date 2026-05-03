import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://df65a16c44c5faa1650393aa13faf324@o4511162776813568.ingest.de.sentry.io/4511325958373456",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
)

from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .extensions import cors
from .models import db, bcrypt

from flask_cors import CORS

migrate = Migrate()

from .api.health import bp as health_bp
from app.api.auth import auth_bp
from app.api.end_user.routes import end_user_bp
from app.api.cleaner.routes import cleaner_bp
from app.api.admin.routes import admin_bp
from app.api.profile import profile_bp
from app.api.job_requests.routes import job_requests_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

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

    # Job Requests
    app.register_blueprint(job_requests_bp, url_prefix="/api/job-requests")

    return app