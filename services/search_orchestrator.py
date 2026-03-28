"""Search orchestrator for aggregating novels from multiple sources."""
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from crawler.base_crawler import SearchNotFoundError
from .source_registry import SourceRegistry
from .metrics_service import metrics_store

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Execute and merge search results across enabled sources."""

    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def search(
        self,
        keyword: str,
        preferred_source: str = None,
        limit: int = 30,
        only_available: bool = False,
    ) -> Dict:
        adapters = self.registry.list_enabled()
        if preferred_source:
            adapters = [a for a in adapters if a.source_id == preferred_source]

        if not adapters:
            return {
                'success': False,
                'error': 'No enabled sources configured'
            }

        merged: List[Dict] = []
        seen_keys = set()
        source_stats = []
        with ThreadPoolExecutor(max_workers=min(8, len(adapters))) as pool:
            future_map = {
                pool.submit(self._search_one_source, adapter, keyword): adapter
                for adapter in adapters
            }

            for future in as_completed(future_map):
                adapter = future_map[future]
                result = future.result()

                source_stats.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'success': result['success'],
                    'count': len(result['results']),
                    'latency_ms': round(result['latency_ms'], 2),
                    'error': result.get('error'),
                })

                metrics_store.record_source_search(
                    adapter.source_id,
                    result['success'],
                    result['latency_ms'],
                    result.get('error')
                )

                if not result['success']:
                    errors.append(f"{adapter.source_id}: {result.get('error', 'unknown error')}")
                    continue

                for item in result['results']:
                    normalized_key = self._build_dedupe_key(
                        item.get('title', ''),
                        item.get('author', 'Unknown')
                    )
                    if normalized_key in seen_keys:
                        continue

                    seen_keys.add(normalized_key)
                    score = self._compute_score(item, keyword, adapter.weight)
                    merged.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'author': item.get('author', 'Unknown'),
                        'description': item.get('description', ''),
                        'source_id': adapter.source_id,
                        'source_name': adapter.display_name,
                        'source_weight': adapter.weight,
                        'score': score,
                    })

        if only_available:
            merged = [item for item in merged if item.get('url')]

        merged.sort(key=lambda item: (item.get('score', 0), item.get('source_weight', 0)), reverse=True)
        merged = merged[:max(1, min(limit, 100))]

        source_stats.sort(key=lambda item: item.get('source_id', ''))

        search_success = len(merged) > 0
        metrics_store.record_search(search_success)

        if not merged:
            if errors and len(errors) == len(adapters):
                return {
                    'success': False,
                    'error': f"All sources failed: {'; '.join(errors)}",
                    'sources': source_stats,
                    'partial_success': False,
                    'query': keyword,
                }
            return {
                'success': False,
                'error': f'No novels found for "{keyword}"',
                'sources': source_stats,
                'partial_success': False,
                'query': keyword,
            }

        failed_count = len([s for s in source_stats if not s.get('success')])
        partial_success = failed_count > 0

        response = {
            'success': True,
            'novels': merged,
            'sources': source_stats,
            'partial_success': partial_success,
            'query': keyword,
            'total': len(merged),
        }
        if partial_success:
            response['degraded_reason'] = f"{failed_count} source(s) failed"

        return response

    def _search_one_source(self, adapter, keyword: str) -> Dict:
        start = time.perf_counter()
        try:
            results = adapter.search_novel(keyword)
            return {
                'success': True,
                'results': results,
                'latency_ms': (time.perf_counter() - start) * 1000,
            }
        except SearchNotFoundError:
            return {
                'success': True,
                'results': [],
                'latency_ms': (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            logger.warning(f"Source search failed ({adapter.source_id}): {e}")
            return {
                'success': False,
                'results': [],
                'latency_ms': (time.perf_counter() - start) * 1000,
                'error': str(e),
            }

    def _compute_score(self, item: Dict, keyword: str, source_weight: int) -> int:
        title = self._normalize_text(item.get('title', ''))
        author = self._normalize_text(item.get('author', ''))
        query = self._normalize_text(keyword)

        score = int(source_weight)
        if query and query in title:
            score += 120
        if query and query in author:
            score += 40
        if item.get('description'):
            score += 5
        return score

    @staticmethod
    def _normalize_text(text: str) -> str:
        value = (text or '').strip().lower()
        value = re.sub(r'\s+', '', value)
        value = re.sub(r'[^\w\u4e00-\u9fff]', '', value)
        return value

    def _build_dedupe_key(self, title: str, author: str) -> Tuple[str, str]:
        return (self._normalize_text(title), self._normalize_text(author))
