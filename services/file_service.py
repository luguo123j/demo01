"""File service for saving novels and managing download history"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict
import config
from crawler.base_crawler import SaveError
from crawler.utils import clean_filename

logger = logging.getLogger(__name__)


class DownloadHistory:
    """Manage download history records"""

    def __init__(self):
        self.history_file = config.HISTORY_FILE
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load download history: {e}")
        return []

    def _save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save download history: {e}")

    def add(
        self,
        novel_title: str,
        novel_url: str,
        file_path: str,
        chapter_count: int = 0,
        source_id: str = None,
        complete_ratio: float = 100.0,
        recovered_chapters: int = 0,
        missing_chapters: int = 0,
    ):
        """
        Add record to download history

        Args:
            novel_title: Title of the novel
            novel_url: URL of the novel
            file_path: Path to saved file
            chapter_count: Number of chapters downloaded
        """
        record = {
            'novel_title': novel_title,
            'novel_url': novel_url,
            'file_path': file_path,
            'chapter_count': chapter_count,
            'source_id': source_id,
            'complete_ratio': complete_ratio,
            'recovered_chapters': recovered_chapters,
            'missing_chapters': missing_chapters,
            'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.history.append(record)
        self._save_history()

    def get_all(self) -> List[Dict]:
        """Get all download history records"""
        return self.history

    def get_by_title(self, title: str) -> List[Dict]:
        """Get history records by novel title"""
        return [h for h in self.history if h['novel_title'] == title]


def save_to_txt(novel_title: str, chapters: List[Dict[str, str]], content_dict: Dict[str, str]) -> str:
    """
    Save novel content to TXT file

    Args:
        novel_title: Title of the novel
        chapters: List of chapter info (title, url)
        content_dict: Dictionary mapping chapter URLs to content

    Returns:
        Path to saved file

    Raises:
        SaveError: If saving fails
    """
    try:
        # Clean filename
        clean_title = clean_filename(novel_title)
        filename = f"{clean_title}.txt"
        filepath = os.path.join(config.DOWNLOAD_DIR, filename)

        # Check if file already exists
        if os.path.exists(filepath):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{clean_title}_{timestamp}.txt"
            filepath = os.path.join(config.DOWNLOAD_DIR, filename)

        # Build content
        content_lines = [f"{novel_title}\n", "=" * 50 + "\n\n"]

        for chapter in chapters:
            title = chapter['title']
            chapter_content = content_dict.get(title, '')

            content_lines.append(f"\n{title}\n")
            content_lines.append("-" * 40 + "\n")
            content_lines.append(chapter_content)
            content_lines.append("\n")

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)

        logger.info(f"Saved novel to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Failed to save novel: {e}")
        raise SaveError(f"Failed to save novel: {e}")
