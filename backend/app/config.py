import os

class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
