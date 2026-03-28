"""Review and activation flow for discovered sources."""
from typing import Dict, Optional
from .source_config_store import SourceConfigStore, SourceReviewStore
from .source_probe_service import probe_source


class SourceReviewService:
    """Manage candidate review -> approve -> dynamic enable flow."""

    def __init__(self):
        self.review_store = SourceReviewStore()
        self.source_store = SourceConfigStore()

    def submit_candidate(self, base_url: str, display_name: str, source_id: str, keyword: str = '武动') -> Dict:
        probe = probe_source(base_url, keyword=keyword, max_chapter_probe=1)
        item = self.review_store.create({
            'status': 'submitted',
            'base_url': base_url,
            'display_name': display_name,
            'source_id': source_id,
            'adapter': 'bqg353_api',
            'probe': probe,
        })
        return {'success': True, 'item': item}

    def list_candidates(self, status: Optional[str] = None) -> Dict:
        items = self.review_store.list_all()
        if status:
            items = [item for item in items if item.get('status') == status]
        return {'success': True, 'items': items}

    def approve(self, item_id: int, keyword: str = '武动') -> Dict:
        items = self.review_store.list_all()
        target = None
        for item in items:
            if int(item.get('id', 0)) == int(item_id):
                target = item
                break

        if not target:
            return {'success': False, 'error': 'Review item not found'}

        latest_probe = probe_source(target.get('base_url', ''), keyword=keyword, max_chapter_probe=1)
        if not latest_probe.get('recommend_enable'):
            self.review_store.update(item_id, {
                'status': 'rejected',
                'probe': latest_probe,
                'reason': 'Probe failed before activation',
            })
            return {
                'success': False,
                'error': 'Probe failed before activation',
                'probe': latest_probe,
            }

        source_cfg = {
            'enabled': True,
            'adapter': target.get('adapter', 'bqg353_api'),
            'display_name': target.get('display_name') or target.get('source_id'),
            'base_url': target.get('base_url'),
            'weight': 80,
        }
        self.source_store.upsert(target.get('source_id'), source_cfg)

        self.review_store.update(item_id, {
            'status': 'approved',
            'probe': latest_probe,
            'enabled_source': source_cfg,
        })

        return {
            'success': True,
            'source_id': target.get('source_id'),
            'enabled_source': source_cfg,
            'probe': latest_probe,
        }

    def reject(self, item_id: int, reason: str = 'Manually rejected') -> Dict:
        updated = self.review_store.update(item_id, {
            'status': 'rejected',
            'reason': reason,
        })
        if not updated:
            return {'success': False, 'error': 'Review item not found'}
        return {'success': True, 'item': updated}
