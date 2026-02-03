import requests
from bs4 import BeautifulSoup
from config import FETCH_URL, HTML_FILE
from pathlib import Path


def fetch_data() -> tuple[bool, str | None]:
    """Fetch latest Warframe drop data"""
    try:
        response = requests.get(FETCH_URL)
        response.raise_for_status()
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        Path(HTML_FILE).parent.mkdir(parents=True, exist_ok=True)

        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

        return True, None
    
    except Exception as e:
        return False, str(e)
