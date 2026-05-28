"""
Configuration settings loaded from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError("BOT_TOKEN must be set in environment variables")

# Server Configuration
SERVER_DOMAIN = os.getenv("SERVER_DOMAIN", "http://localhost:8000")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "./bot_data.db")

# Token Configuration
TOKEN_EXPIRATION = int(os.getenv("TOKEN_EXPIRATION", "3600"))  # 1 hour default
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AD_PAGE_DIST = os.path.join(BASE_DIR, "ad-page", "dist")
