"""Adapter for bqg353-style API sources."""
from typing import Dict, List
from crawler.novel_crawler import NovelCrawler
from .base_adapter import BaseSourceAdapter


class BQG353SourceAdapter(BaseSourceAdapter):
    """Source adapter backed by the existing NovelCrawler implementation."""

    def __init__(
        self,
        source_id: str,
        display_name: str,
        base_url: str,
        weight: int = 0,
        timeout: int = 30,
        max_retries: int = 3,
        request_delay: float = 1.0,
    ):
        super().__init__(source_id=source_id, display_name=display_name, weight=weight)
        self._crawler = NovelCrawler(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            request_delay=request_delay,
            source_id=source_id,
        )

    def search_novel(self, keyword: str) -> List[Dict[str, str]]:
        return self._crawler.search_novel(keyword)

    def get_novel_info(self, novel_url: str) -> Dict:
        return self._crawler.get_novel_info(novel_url)

    def get_chapter_content(self, chapter_info: Dict) -> str:
        return self._crawler.get_chapter_content(chapter_info)

    def close(self):
        self._crawler.close()
