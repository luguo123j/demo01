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

# Multi-source configuration (Phase 1)
# Existing BASE_URL/SEARCH_URL are kept for backward compatibility.
SOURCES = {
	'bqg353': {
		'enabled': True,
		'adapter': 'bqg353_api',
		'display_name': '笔趣阁 353',
		'base_url': BASE_URL,
		'weight': 100,
		'timeout': TIMEOUT,
		'max_retries': MAX_RETRIES,
		'request_delay': REQUEST_DELAY,
	},
	'bqg356': {
		'enabled': True,
		'adapter': 'bqg353_api',
		'display_name': '笔趣阁 356',
		'base_url': 'https://www.bqg356.cc',
		'weight': 90,
		'timeout': TIMEOUT,
		'max_retries': MAX_RETRIES,
		'request_delay': REQUEST_DELAY,
	}
}

# File paths
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'app.log')
HISTORY_FILE = os.path.join(BASE_DIR, 'download_history.json')
DYNAMIC_SOURCES_FILE = os.path.join(BASE_DIR, 'dynamic_sources.json')
SOURCE_REVIEW_FILE = os.path.join(BASE_DIR, 'source_review_queue.json')

# Seed URLs for semi-automatic source discovery.
DISCOVERY_SEED_URLS = [
	'https://www.bqg353.xyz',
	'https://www.bqg356.cc',
	'https://www.bqg128.com',
	'https://www.bqg789.com',
]

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
