"""Novel crawler for scraping novel content"""
import logging
import re
import json
from typing import List, Dict, Optional
import config
from .base_crawler import BaseCrawler, SearchNotFoundError, NetworkError, ParseError
from .parser import parse_search_results, parse_chapter_list, parse_chapter_content, parse_novel_title
from .utils import AntiSpider, delay

logger = logging.getLogger(__name__)


class NovelCrawler:
    """Main crawler class for novel website"""

    def __init__(
        self,
        base_url: str = None,
        timeout: int = None,
        max_retries: int = None,
        request_delay: float = None,
        source_id: str = 'default',
    ):
        """Initialize novel crawler"""
        self.base_url = base_url or config.BASE_URL
        self.search_url = f"{self.base_url}/api/search"
        self.source_id = source_id
        timeout = timeout if timeout is not None else config.TIMEOUT
        max_retries = max_retries if max_retries is not None else config.MAX_RETRIES
        request_delay = request_delay if request_delay is not None else config.REQUEST_DELAY
        self.crawler = BaseCrawler(
            timeout=timeout,
            max_retries=max_retries,
            delay=request_delay
        )
        self.anti_spider = AntiSpider()

    def search_novel(self, keyword: str) -> List[Dict[str, str]]:
        """
        Search for novels by keyword

        Args:
            keyword: Search keyword

        Returns:
            List of novels with title, url, author, description

        Raises:
            SearchNotFoundError: If no results found
            NetworkError: If request fails
        """
        try:
            logger.info(f"Searching for novel on source {self.source_id}: {keyword}")

            # Prepare search parameters
            params = {'q': keyword}

            # Make search request
            headers = self.anti_spider.get_headers()
            response = self.crawler.get(
                self.search_url,
                params=params,
                headers=headers
            )

            # Parse results
            novels = parse_search_results(response.text)

            if not novels:
                raise SearchNotFoundError(f"No novels found for keyword: {keyword}")

            logger.info(f"Found {len(novels)} novels")
            return novels

        except NetworkError:
            raise
        except Exception as e:
            logger.error(f"Error searching novel: {e}")
            raise

    def get_novel_info(self, novel_url: str) -> Dict[str, any]:
        """
        Get novel information and chapter list

        Args:
            novel_url: URL of the novel detail page (format: /#/book/{id})

        Returns:
            Dictionary with title, author, description, chapter_list

        Raises:
            NetworkError: If request fails
        """
        try:
            # Extract book ID from URL
            import re
            match = re.search(r'/book/(\d+)', novel_url)
            if not match:
                raise ParseError(f"Invalid novel URL format: {novel_url}")

            book_id = match.group(1)
            logger.info(f"Fetching novel info for book ID: {book_id}")

            # Use book API to get info
            book_url = f"{self.base_url}/api/book?id={book_id}"
            headers = self.anti_spider.get_headers()
            response = self.crawler.get(book_url, headers=headers)

            import json
            book_data = json.loads(response.text)
            title = book_data.get('title', 'Unknown Title')
            author = book_data.get('author', 'Unknown')
            intro = book_data.get('intro', '')

            logger.info(f"Got novel info: {title} by {author}")

            # Get chapter list
            chapters = self.get_chapter_list(novel_url)

            return {
                'title': title,
                'author': author,
                'intro': intro,
                'url': novel_url,
                'book_id': book_id,
                'chapters': chapters
            }

        except NetworkError:
            raise
        except Exception as e:
            logger.error(f"Error getting novel info: {e}")
            raise

    def get_chapter_list(self, novel_url: str) -> List[Dict[str, str]]:
        """
        Get chapter list for a novel

        Args:
            novel_url: URL of the novel detail page

        Returns:
            List of chapters with title and url

        Raises:
            NetworkError: If request fails
        """
        try:
            # Extract book ID from URL
            import re
            import json
            match = re.search(r'/book/(\d+)', novel_url)
            if not match:
                raise ParseError(f"Invalid novel URL format: {novel_url}")

            book_id = match.group(1)
            logger.info(f"Fetching chapter list for book ID: {book_id}")

            # Use booklist API
            booklist_url = f"{self.base_url}/api/booklist?id={book_id}"
            headers = self.anti_spider.get_headers()
            response = self.crawler.get(booklist_url, headers=headers)

            data = json.loads(response.text)
            chapter_list = data.get('list', [])

            # Parse chapters
            chapters = []
            for idx, chapter_name in enumerate(chapter_list):
                chapters.append({
                    'title': chapter_name,
                    'url': f"{book_id}",
                    'chapter_id': idx + 1  # Chapter IDs start from 1
                })

            logger.info(f"Got {len(chapters)} chapters")
            return chapters

        except NetworkError:
            raise
        except Exception as e:
            logger.error(f"Error getting chapter list: {e}")
            raise

    def get_chapter_content(self, chapter_info: dict) -> str:
        """
        Get content of a single chapter

        Args:
            chapter_info: Dictionary with 'url' (book_id) and 'chapter_id'

        Returns:
            Chapter content text

        Raises:
            NetworkError: If request fails
        """
        try:
            book_id = chapter_info.get('url', '')
            chapter_id = chapter_info.get('chapter_id', 1)

            # Use chapter API
            chapter_url = f"{self.base_url}/api/chapter?id={book_id}&chapterid={chapter_id}"
            headers = self.anti_spider.get_headers(referer=self.base_url)
            response = self.crawler.get(chapter_url, headers=headers)

            import json
            data = json.loads(response.text)
            content = data.get('txt', '')

            # Add delay to avoid detection
            delay()

            logger.debug(f"Got chapter {chapter_id} content, length: {len(content)}")
            return content

        except NetworkError:
            raise
        except Exception as e:
            logger.error(f"Error getting chapter content: {e}")
            raise

    def close(self):
        """Close crawler session"""
        self.crawler.close()
