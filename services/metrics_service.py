"""In-memory metrics for search and download observability."""
import threading
import time
from collections import defaultdict
from typing import Dict


class MetricsStore:
    """Thread-safe in-memory metrics storage."""

    def __init__(self):
        self._lock = threading.Lock()
        self._search_total = 0
        self._search_success = 0
        self._search_failed = 0
        self._download_total = 0
        self._download_success = 0
        self._download_failed = 0
        self._source_stats = defaultdict(lambda: {
            'search_count': 0,
            'search_success': 0,
            'search_failed': 0,
            'search_total_latency_ms': 0.0,
            'last_error': None,
            'last_seen_ts': None,
        })

    def record_search(self, success: bool):
        with self._lock:
            self._search_total += 1
            if success:
                self._search_success += 1
            else:
                self._search_failed += 1

    def record_source_search(self, source_id: str, success: bool, latency_ms: float, error: str = None):
        with self._lock:
            stats = self._source_stats[source_id]
            stats['search_count'] += 1
            stats['search_total_latency_ms'] += float(latency_ms)
            stats['last_seen_ts'] = int(time.time())
            if success:
                stats['search_success'] += 1
            else:
                stats['search_failed'] += 1
                stats['last_error'] = error

    def record_download(self, success: bool):
        with self._lock:
            self._download_total += 1
            if success:
                self._download_success += 1
            else:
                self._download_failed += 1

    def snapshot(self) -> Dict:
        with self._lock:
            sources = {}
            for source_id, stats in self._source_stats.items():
                count = stats['search_count'] or 1
                success_rate = round((stats['search_success'] / count) * 100, 2)
                avg_latency = round(stats['search_total_latency_ms'] / count, 2)
                sources[source_id] = {
                    'search_count': stats['search_count'],
                    'search_success': stats['search_success'],
                    'search_failed': stats['search_failed'],
                    'search_success_rate': success_rate,
                    'avg_search_latency_ms': avg_latency,
                    'last_error': stats['last_error'],
                    'last_seen_ts': stats['last_seen_ts'],
                }

            search_success_rate = round((self._search_success / (self._search_total or 1)) * 100, 2)
            download_success_rate = round((self._download_success / (self._download_total or 1)) * 100, 2)

            return {
                'search': {
                    'total': self._search_total,
                    'success': self._search_success,
                    'failed': self._search_failed,
                    'success_rate': search_success_rate,
                },
                'download': {
                    'total': self._download_total,
                    'success': self._download_success,
                    'failed': self._download_failed,
                    'success_rate': download_success_rate,
                },
                'sources': sources,
            }


metrics_store = MetricsStore()
