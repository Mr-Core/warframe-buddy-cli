# services/warframe_api.py
import aiohttp
import time
import logging


logger = logging.getLogger(__name__)


class WarframeAPI:
    """Async client for WarframeStat.us API with caching"""

    BASE_URL = "https://api.warframestat.us"
    PLATFORM = "pc"  # Could make configurable

    def __init__(self, cache_ttl: int = 60):
        self.cache = {}
        self.cache_ttl = cache_ttl  # seconds
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session

    async def _cached_get(self, endpoint: str) -> dict:
        """Get data with simple TTL caching"""
        now = time.time()

        if endpoint in self.cache:
            data, timestamp = self.cache[endpoint]
            if now - timestamp < self.cache_ttl:
                return data

        session = await self._get_session()
        try:
            url = f"{self.BASE_URL}/{self.PLATFORM}/{endpoint}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.cache[endpoint] = (data, now)
                    return data
                else:
                    logger.error(f"API Error {response.status} for {endpoint}")
                    return {}
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {}

    async def get_fissures(self) -> dict:
        """Get active void fissures"""
        return await self._cached_get("fissures")

    async def get_sortie(self) -> dict:
        """Get current sortie data"""
        return await self._cached_get("sortie")

    async def get_alerts(self) -> dict:
        """Get active alerts"""
        return await self._cached_get("alerts")

    async def get_nightwave(self) -> dict:
        """Get Nightwave challenges"""
        return await self._cached_get("nightwave")

    async def get_invasions(self) -> dict:
        """Get active invasions"""
        return await self._cached_get("invasions")

    async def close(self) -> None:
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
