"""Utility functions for crawler"""
import random
import time
import logging
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class AntiSpider:
    """Anti-detection utilities for web scraping"""

    def __init__(self):
        self.ua = UserAgent()

    def get_random_user_agent(self) -> str:
        """
        Get random user agent string

        Returns:
            Random User-Agent string
        """
        try:
            return self.ua.random
        except Exception as e:
            logger.warning(f"Failed to get random UA: {e}, using fallback")
            return self._get_fallback_ua()

    def _get_fallback_ua(self) -> str:
        """Fallback user agent strings"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]
        return random.choice(user_agents)

    def get_headers(self, referer: str = None) -> dict:
        """
        Get request headers with random User-Agent

        Args:
            referer: Optional referer URL

        Returns:
            Dictionary of headers
        """
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        if referer:
            headers['Referer'] = referer
        return headers


def delay(seconds: float = None, min_delay: float = 0.5, max_delay: float = 2.0):
    """
    Add delay between requests to avoid detection

    Args:
        seconds: Exact delay time (overrides random delay)
        min_delay: Minimum random delay
        max_delay: Maximum random delay
    """
    if seconds is not None:
        wait_time = seconds
    else:
        wait_time = random.uniform(min_delay, max_delay)
    logger.debug(f"Delaying for {wait_time:.2f} seconds")
    time.sleep(wait_time)


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters

    Args:
        filename: Original filename

    Returns:
        Cleaned filename
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    cleaned = filename
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '')
    return cleaned.strip()
