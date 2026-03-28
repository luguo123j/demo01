"""Health checks for source availability."""
from typing import Dict, List
from .source_registry import SourceRegistry


def check_sources_health(probe_keyword: str = '武动') -> Dict:
    """Run lightweight source checks using search endpoint."""
    registry = SourceRegistry()
    details: List[Dict] = []
    healthy = 0

    try:
        adapters = registry.list_enabled()
        for adapter in adapters:
            try:
                results = adapter.search_novel(probe_keyword)
                details.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'healthy': True,
                    'result_count': len(results),
                })
                healthy += 1
            except Exception as e:
                details.append({
                    'source_id': adapter.source_id,
                    'source_name': adapter.display_name,
                    'healthy': False,
                    'result_count': 0,
                    'error': str(e),
                })

        return {
            'success': True,
            'healthy_sources': healthy,
            'total_sources': len(details),
            'sources': details,
        }
    finally:
        registry.close_all()
