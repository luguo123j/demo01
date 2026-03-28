"""Base crawler with HTTP request handling and retry mechanism"""
import requests
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CrawlerError(Exception):
    """Base exception for crawler errors"""
    pass


class SearchNotFoundError(CrawlerError):
    """Exception raised when novel search returns no results"""
    pass


class NetworkError(CrawlerError):
    """Exception raised for network-related errors"""
    pass


class ParseError(CrawlerError):
    """Exception raised for HTML parsing errors"""
    pass


class SaveError(CrawlerError):
    """Exception raised for file saving errors"""
    pass


class BaseCrawler:
    """Base crawler class with HTTP request capabilities"""

    def __init__(self, timeout: int = 30, max_retries: int = 3, delay: float = 1.0):
        """
        Initialize base crawler

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay: Delay between requests in seconds
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        # Do not inherit system proxy settings to avoid invalid local proxy errors.
        self.session = requests.Session()
        self.session.trust_env = False

    def request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """
        Make HTTP request with retry mechanism

        Args:
            url: Target URL
            method: HTTP method (GET/POST)
            **kwargs: Additional arguments for requests.request

        Returns:
            Response object

        Raises:
            NetworkError: If request fails after retries
        """
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('headers', {})
        kwargs.setdefault('verify', False)  # Disable SSL verification
        kwargs.setdefault('stream', False)

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Requesting {url} (attempt {attempt + 1}/{self.max_retries})")

                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))  # Exponential backoff
                else:
                    raise NetworkError(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")

        raise NetworkError(f"Failed to fetch {url}")

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request"""
        return self.request(url, 'GET', **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request"""
        return self.request(url, 'POST', **kwargs)

    def close(self):
        """Close HTTP session"""
        self.session.close()
