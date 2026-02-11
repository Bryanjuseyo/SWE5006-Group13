import os


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'postgresql://cleanmatch_user:securepassword123@localhost:5432/cleanmatch')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv("JWT_SECRE", "dev-jwt-secret")
    JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 24))
