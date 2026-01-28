import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set to True for development (uses cached data, no web fetching)
# Set to False for production (fetches new data from web)
DEVELOPMENT_MODE = True

# File paths
FETCH_URL = 'https://www.warframe.com/droptables'
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
HTML_FILE = DATA_DIR / 'warframe_drops.html'
PARSED_DATA_FILE = DATA_DIR / 'parsed_drops.json'
INDEXED_DATA_FILE = DATA_DIR / 'search_indexes.json'
COMMON_SEARCH_DATA_FILE = DATA_DIR / 'most_common_searches.json'

# Set update time and health check time for service manager
DAILY_UPDATE_TIME = '03:00'
HEALTH_CHECK_TIME = '04:00'

# Set Discord bot token and command prefix
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '?'
