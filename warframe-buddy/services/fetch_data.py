import requests
from bs4 import BeautifulSoup
from config import FETCH_URL, HTML_FILE
from pathlib import Path


def fetch_data():
    """Fetch latest Warframe drop data"""
    print(f'Fetching data from {FETCH_URL}...')

    response = requests.get(FETCH_URL)
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'html.parser')
    
    Path(HTML_FILE).parent.mkdir(parents=True, exist_ok=True)

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print(f'✓ Data saved to {HTML_FILE}')
    
    return True
