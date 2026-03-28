"""Semi-automatic source discovery service."""
import re
from typing import Dict, List
import config
from .source_config_store import SourceConfigStore
from .source_probe_service import probe_source


def discover_candidates(keyword: str = '武动', limit: int = 10) -> Dict:
    """Discover candidates from seed pool and probe compatibility."""
    store = SourceConfigStore()
    dynamic = store.list_all()

    configured_urls = set()
    for source_cfg in config.SOURCES.values():
        configured_urls.add(_normalize_url(source_cfg.get('base_url', '')))
    for source_cfg in dynamic.values():
        configured_urls.add(_normalize_url(source_cfg.get('base_url', '')))

    candidates: List[Dict] = []
    for url in config.DISCOVERY_SEED_URLS:
        normalized = _normalize_url(url)
        if not normalized or normalized in configured_urls:
            continue

        probe = probe_source(normalized, keyword=keyword, max_chapter_probe=1)
        source_id = _build_source_id(normalized)
        candidates.append({
            'source_id': source_id,
            'base_url': normalized,
            'display_name': f'候选来源 {source_id}',
            'probe': probe,
        })

        if len(candidates) >= max(1, min(limit, 50)):
            break

    return {
        'success': True,
        'keyword': keyword,
        'total': len(candidates),
        'candidates': candidates,
    }


def _normalize_url(url: str) -> str:
    value = (url or '').strip().rstrip('/')
    if not value:
        return ''
    if not value.startswith('http://') and not value.startswith('https://'):
        value = f'https://{value}'
    return value.rstrip('/')


def _build_source_id(base_url: str) -> str:
    domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '_', domain).strip('_').lower()
    return cleaned or 'candidate_source'
