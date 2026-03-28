"""Configuration file for novel crawler application"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Website configuration
BASE_URL = "https://www.bqg353.xyz"
SEARCH_URL = f"{BASE_URL}/api/search"
TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY = 1  # seconds between requests

# File paths
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
HISTORY_FILE = os.path.join(BASE_DIR, 'download_history.json')

# Flask configuration
FLASK_HOST = '0.0.0.0'
FL_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = 'novel-crawler-secret-key-2024'

# Download configuration
CHUNK_SIZE = 1024
MAX_CONCURRENT_DOWNLOADS = 3

# Ensure directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
