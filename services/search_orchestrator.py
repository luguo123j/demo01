"""Search orchestrator for aggregating novels from multiple sources."""
import logging
import re
from typing import Dict, List, Tuple
from crawler.base_crawler import SearchNotFoundError
from .source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Execute and merge search results across enabled sources."""

    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def search(self, keyword: str) -> Dict:
        adapters = self.registry.list_enabled()
        if not adapters:
            return {
                'success': False,
                'error': 'No enabled sources configured'
            }

        merged: List[Dict] = []
        seen_keys = set()
        source_stats = []
        errors = []

        for adapter in adapters:
            try:
                results = adapter.search_novel(keyword)
                source_stats.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'success': True,
                    'count': len(results)
                })

                for item in results:
                    normalized_key = self._build_dedupe_key(
                        item.get('title', ''),
                        item.get('author', 'Unknown')
                    )
                    if normalized_key in seen_keys:
                        continue

                    seen_keys.add(normalized_key)
                    merged.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'author': item.get('author', 'Unknown'),
                        'description': item.get('description', ''),
                        'source_id': adapter.source_id,
                        'source_name': adapter.display_name,
                        'source_weight': adapter.weight,
                    })

            except SearchNotFoundError:
                source_stats.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'success': True,
                    'count': 0
                })
            except Exception as e:
                logger.warning(f"Source search failed ({adapter.source_id}): {e}")
                source_stats.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'success': False,
                    'count': 0,
                    'error': str(e)
                })
                errors.append(f"{adapter.source_id}: {e}")

        merged.sort(key=lambda item: item.get('source_weight', 0), reverse=True)

        if not merged:
            if errors and len(errors) == len(adapters):
                return {
                    'success': False,
                    'error': f"All sources failed: {'; '.join(errors)}",
                    'sources': source_stats,
                    'partial_success': False,
                }
            return {
                'success': False,
                'error': f'No novels found for "{keyword}"',
                'sources': source_stats,
                'partial_success': False,
            }

        failed_count = len([s for s in source_stats if not s.get('success')])
        partial_success = failed_count > 0

        response = {
            'success': True,
            'novels': merged,
            'sources': source_stats,
            'partial_success': partial_success,
        }
        if partial_success:
            response['degraded_reason'] = f"{failed_count} source(s) failed"

        return response

    @staticmethod
    def _normalize_text(text: str) -> str:
        value = (text or '').strip().lower()
        value = re.sub(r'\s+', '', value)
        value = re.sub(r'[^\w\u4e00-\u9fff]', '', value)
        return value

    def _build_dedupe_key(self, title: str, author: str) -> Tuple[str, str]:
        return (self._normalize_text(title), self._normalize_text(author))
