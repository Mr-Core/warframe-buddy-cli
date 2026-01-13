"""
Configuration file - change these values as needed
"""

# Set to True for development (uses cached data, no web fetching)
# Set to False for production (fetches new data from web)
DEVELOPMENT_MODE = False

# File paths
FETCH_URL = 'https://www.warframe.com/droptables'
HTML_FILE = 'warframe-buddy/data/Warframe_PC_Drops.html'
PARSED_DATA_FILE = 'warframe-buddy/data/warframe_drops_parsed.json'
INDEXED_DATA_FILE = 'warframe-buddy/data/warframe_drops_indexed.json'

# Set update time and health check time for service manager
DAILY_UPDATE_TIME = '03:00'
HEALTH_CHECK_TIME = '04:00'
