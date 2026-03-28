"""Persistent store for dynamic sources and review queue."""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import config


def _read_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        return default
    return default


def _write_json(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class SourceConfigStore:
    """Store for dynamic source config entries."""

    def __init__(self):
        self.file_path = config.DYNAMIC_SOURCES_FILE

    def list_all(self) -> Dict[str, Dict]:
        return _read_json(self.file_path, {})

    def upsert(self, source_id: str, source_cfg: Dict):
        data = self.list_all()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        merged = dict(data.get(source_id, {}))
        merged.update(source_cfg)
        merged['updated_at'] = now
        if 'created_at' not in merged:
            merged['created_at'] = now
        data[source_id] = merged
        _write_json(self.file_path, data)

    def remove(self, source_id: str):
        data = self.list_all()
        if source_id in data:
            data.pop(source_id)
            _write_json(self.file_path, data)


class SourceReviewStore:
    """Store for review queue entries."""

    def __init__(self):
        self.file_path = config.SOURCE_REVIEW_FILE

    def list_all(self) -> List[Dict]:
        return _read_json(self.file_path, [])

    def create(self, item: Dict) -> Dict:
        records = self.list_all()
        item = dict(item)
        item['id'] = int(item.get('id') or (max([r.get('id', 0) for r in records] + [0]) + 1))
        item['created_at'] = item.get('created_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        records.append(item)
        _write_json(self.file_path, records)
        return item

    def update(self, item_id: int, patch: Dict) -> Optional[Dict]:
        records = self.list_all()
        updated = None
        for idx, item in enumerate(records):
            if int(item.get('id', 0)) == int(item_id):
                merged = dict(item)
                merged.update(patch)
                merged['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                records[idx] = merged
                updated = merged
                break

        if updated is not None:
            _write_json(self.file_path, records)
        return updated
