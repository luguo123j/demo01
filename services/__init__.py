"""Services module for business logic"""
from .search_service import search_novel
from .download_service import download_novel
from .file_service import save_to_txt, DownloadHistory

__all__ = ['search_novel', 'download_novel', 'save_to_txt', 'DownloadHistory']
