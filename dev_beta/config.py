# config.py
"""
Configuration file - change these values as needed
"""

# Set to True for development (uses cached data, no web fetching)
# Set to False for production (fetches new data from web)
DEVELOPMENT_MODE = False

# File paths
FETCH_URL = 'https://www.warframe.com/droptables'
HTML_FILE = 'dev_beta/data/Warframe_PC_Drops.html'
PARSED_DATA_FILE = 'dev_beta/data/warframe_drops_parsed.json'
INDEXED_DATA_FILE = 'dev_beta/data/warframe_drops_indexed.json'
