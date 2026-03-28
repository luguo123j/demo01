"""Probe service to validate candidate sources before enablement."""
import re
import time
from typing import Dict
from crawler.novel_crawler import NovelCrawler


def probe_source(base_url: str, keyword: str = '武动', max_chapter_probe: int = 1) -> Dict:
    """Run search/book/chapter probes and return compatibility score."""
    crawler = NovelCrawler(
        base_url=base_url,
        timeout=8,
        max_retries=1,
        request_delay=0.2,
        source_id='probe',
    )
    started = time.perf_counter()

    try:
        search_results = crawler.search_novel(keyword)
        if not search_results:
            return _failed('search_probe_failed', base_url, started)

        first = search_results[0]
        novel_info = crawler.get_novel_info(first.get('url', ''))
        chapters = novel_info.get('chapters', [])
        if not chapters:
            return _failed('catalog_probe_failed', base_url, started)

        chapter_texts = []
        for chapter in chapters[:max(1, max_chapter_probe)]:
            content = crawler.get_chapter_content(chapter)
            chapter_texts.append(content or '')

        readable_count = sum(1 for text in chapter_texts if _is_readable(text))
        readable_rate = round((readable_count / max(1, len(chapter_texts))) * 100, 2)

        score = 0
        score += 35  # search passed
        score += 35  # catalog passed
        score += int(readable_rate * 0.3)

        return {
            'success': True,
            'base_url': base_url,
            'adapter': 'bqg353_api',
            'score': min(100, score),
            'search_count': len(search_results),
            'chapter_probe_count': len(chapter_texts),
            'readable_rate': readable_rate,
            'elapsed_ms': round((time.perf_counter() - started) * 1000, 2),
            'recommend_enable': score >= 70,
            'sample_title': first.get('title', ''),
            'sample_url': first.get('url', ''),
        }
    except Exception as e:
        return {
            'success': False,
            'base_url': base_url,
            'adapter': 'bqg353_api',
            'score': 0,
            'error': str(e),
            'elapsed_ms': round((time.perf_counter() - started) * 1000, 2),
            'recommend_enable': False,
        }
    finally:
        crawler.close()


def _failed(reason: str, base_url: str, started: float) -> Dict:
    return {
        'success': False,
        'base_url': base_url,
        'adapter': 'bqg353_api',
        'score': 0,
        'error': reason,
        'elapsed_ms': round((time.perf_counter() - started) * 1000, 2),
        'recommend_enable': False,
    }


def _is_readable(text: str) -> bool:
    cleaned = (text or '').strip()
    if len(cleaned) < 80:
        return False
    # Heuristic: ensure there are enough CJK or word chars.
    cjk_or_word = re.findall(r'[\u4e00-\u9fff\w]', cleaned)
    return len(cjk_or_word) >= 80
