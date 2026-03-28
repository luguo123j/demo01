"""Source registry for multi-source adapters."""
import logging
from typing import Dict, List
import config
from crawler.adapters import BQG353SourceAdapter, BaseSourceAdapter

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Build and manage enabled source adapters from configuration."""

    def __init__(self):
        self._adapters: List[BaseSourceAdapter] = []
        self._build_from_config()

    def _build_from_config(self):
        sources: Dict[str, Dict] = getattr(config, 'SOURCES', {}) or {}

        for source_id, source_cfg in sources.items():
            if not source_cfg.get('enabled', True):
                continue

            adapter_name = source_cfg.get('adapter', 'bqg353_api')
            display_name = source_cfg.get('display_name', source_id)
            weight = int(source_cfg.get('weight', 0))

            if adapter_name == 'bqg353_api':
                adapter = BQG353SourceAdapter(
                    source_id=source_id,
                    display_name=display_name,
                    base_url=source_cfg.get('base_url', config.BASE_URL),
                    weight=weight,
                    timeout=int(source_cfg.get('timeout', config.TIMEOUT)),
                    max_retries=int(source_cfg.get('max_retries', config.MAX_RETRIES)),
                    request_delay=float(source_cfg.get('request_delay', config.REQUEST_DELAY)),
                )
                self._adapters.append(adapter)
            else:
                logger.warning(f"Unknown adapter type: {adapter_name} (source={source_id})")

        # Higher weight means higher priority.
        self._adapters.sort(key=lambda adapter: adapter.weight, reverse=True)

    def list_enabled(self) -> List[BaseSourceAdapter]:
        return self._adapters

    def get_by_id(self, source_id: str):
        for adapter in self._adapters:
            if adapter.source_id == source_id:
                return adapter
        return None

    def list_with_preferred_first(self, source_id: str) -> List[BaseSourceAdapter]:
        if not source_id:
            return self._adapters

        preferred = self.get_by_id(source_id)
        if not preferred:
            return self._adapters

        return [preferred] + [adapter for adapter in self._adapters if adapter.source_id != source_id]

    def close_all(self):
        for adapter in self._adapters:
            try:
                adapter.close()
            except Exception as e:
                logger.warning(f"Failed to close adapter {adapter.source_id}: {e}")
