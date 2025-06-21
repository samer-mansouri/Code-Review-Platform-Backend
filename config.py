import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 2592000
    JWT_REFRESH_TOKEN_EXPIRES = 2592000
    MONGODB_SETTINGS = {
        'db': os.getenv("MONGO_DB"),
        'host': os.getenv("MONGO_URI")
    }
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    UPLOAD_FOLDER = 'app/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}