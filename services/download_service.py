"""Download service for downloading novels"""
import logging
import threading
import os
import time
from typing import Dict, Optional
from crawler.novel_crawler import NovelCrawler
from crawler.parser import parse_novel_title
from .file_service import save_to_txt, DownloadHistory

logger = logging.getLogger(__name__)


# Global download tasks storage
download_tasks = {}
task_lock = threading.Lock()


class DownloadTask:
    """Represents a download task with progress tracking"""

    def __init__(self, task_id: str, novel_url: str, start_chapter: int = 1, end_chapter: Optional[int] = None):
        self.task_id = task_id
        self.novel_url = novel_url
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.status = 'pending'
        self.progress = 0
        self.total_chapters = 0
        self.downloaded_chapters = 0
        self.error = None
        self.result = None
        self.novel_title = None
        self.filename = None
        self.paused = False
        self.stopped = False


def download_novel(novel_url: str, start_chapter: int = 1, end_chapter: Optional[int] = None) -> str:
    """
    Start a novel download task

    Args:
        novel_url: URL of the novel
        start_chapter: Starting chapter number (1-indexed)
        end_chapter: Ending chapter number (None for all chapters)

    Returns:
        Task ID for tracking download progress
    """
    import uuid

    task_id = str(uuid.uuid4())
    task = DownloadTask(task_id, novel_url, start_chapter, end_chapter)

    with task_lock:
        download_tasks[task_id] = task

    # Start download in background thread
    thread = threading.Thread(target=_download_worker, args=(task,))
    thread.daemon = True
    thread.start()

    return task_id


def _download_worker(task: DownloadTask):
    """
    Worker function to download novel

    Args:
        task: DownloadTask instance
    """
    try:
        task.status = 'downloading'
        logger.info(f"Starting download task: {task.task_id}")

        # Initialize crawler
        crawler = NovelCrawler()

        # Get novel info
        novel_info = crawler.get_novel_info(task.novel_url)
        task.novel_title = novel_info['title']

        # Get chapter list
        chapters = novel_info['chapters']
        task.total_chapters = len(chapters)

        # Apply chapter range
        if task.start_chapter > 1 or task.end_chapter is not None:
            end_idx = task.end_chapter if task.end_chapter else len(chapters)
            chapters = chapters[task.start_chapter - 1:min(end_idx, len(chapters))]

        logger.info(f"Downloading {len(chapters)} chapters of: {task.novel_title}")

        # Download chapters
        content_dict = {}
        for idx, chapter in enumerate(chapters):
            # Check if stopped
            if task.stopped:
                logger.info(f"Download stopped by user")
                break

            # Check if paused
            while task.paused:
                logger.info(f"Download paused, waiting...")
                time.sleep(1)

            try:
                content = crawler.get_chapter_content(chapter)
                content_dict[chapter['title']] = content
                task.downloaded_chapters += 1
                task.progress = int((task.downloaded_chapters / len(chapters)) * 100)
                logger.debug(f"Downloaded chapter {task.downloaded_chapters}/{len(chapters)}")
            except Exception as e:
                logger.error(f"Failed to download chapter {chapter['title']}: {e}")
                # Continue with next chapter

        # Only save if not stopped
        if not task.stopped:
            # Save to file
            filepath = save_to_txt(task.novel_title, chapters, content_dict)
            task.filename = os.path.basename(filepath)

            # Add to download history
            history = DownloadHistory()
            history.add(task.novel_title, task.novel_url, filepath, len(chapters))

            task.status = 'completed'
            task.progress = 100
            task.result = {
                'filename': task.filename,
                'filepath': filepath,
                'chapter_count': len(chapters)
            }
            logger.info(f"Download completed: {task.filename}")

        crawler.close()

    except Exception as e:
        logger.error(f"Download failed: {e}")
        task.status = 'error'
        task.error = str(e)


def pause_download(task_id: str):
    """
    Pause a download task

    Args:
        task_id: Task ID to pause
    """
    with task_lock:
        task = download_tasks.get(task_id)
        if task:
            task.paused = True
            logger.info(f"Download task paused: {task_id}")


def resume_download(task_id: str):
    """
    Resume a download task

    Args:
        task_id: Task ID to resume
    """
    with task_lock:
        task = download_tasks.get(task_id)
        if task:
            task.paused = False
            logger.info(f"Download task resumed: {task_id}")


def stop_download(task_id: str):
    """
    Stop a download task

    Args:
        task_id: Task ID to stop
    """
    with task_lock:
        task = download_tasks.get(task_id)
        if task:
            task.stopped = True
            task.paused = False
            logger.info(f"Download task stopped: {task_id}")


def get_download_status(task_id: str) -> Optional[Dict]:
    """
    Get download task status

    Args:
        task_id: Task ID

    Returns:
        Dictionary with task status information or None if task not found
    """
    with task_lock:
        task = download_tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.task_id,
            'status': task.status,
            'progress': task.progress,
            'total_chapters': task.total_chapters,
            'downloaded_chapters': task.downloaded_chapters,
            'novel_title': task.novel_title,
            'error': task.error,
            'result': task.result
        }


def get_download_history() -> Dict:
    """
    Get download history

    Returns:
        Dictionary with download history records
    """
    history = DownloadHistory()
    return {
        'success': True,
        'history': history.get_all()
    }
