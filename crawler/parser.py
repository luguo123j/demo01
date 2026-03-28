"""HTML parser for novel website"""
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def parse_search_results(html: str) -> List[Dict[str, str]]:
    """
    Parse search results page

    Args:
        html: HTML content of search results page (or JSON string)

    Returns:
        List of novels with title, url, author, and description

    Raises:
        ParseError: If parsing fails
    """
    try:
        # First try to parse as JSON (API response)
        try:
            import json
            data = json.loads(html)
            if 'data' in data and isinstance(data['data'], list):
                novels = []
                for item in data['data'][:10]:  # Limit to 10 results
                    novels.append({
                        'title': item.get('title', ''),
                        'url': f"/#/book/{item.get('id', '')}",  # Construct URL from ID
                        'author': item.get('author', 'Unknown'),
                        'description': item.get('intro', '')
                    })
                logger.info(f"Parsed {len(novels)} novels from JSON API response")
                return novels
        except json.JSONDecodeError:
            pass  # Not JSON, fall through to HTML parsing

        # Try HTML parsing as fallback
        soup = BeautifulSoup(html, 'lxml')
        novels = []

        # Try to find search results container
        # Common patterns for search result items
        result_items = soup.select('.result-item, .book-list li, .search-result, .result')

        if not result_items:
            # Try alternative selectors
            result_items = soup.select('li.result, div.result, article, .book-item')

        if not result_items:
            # Try to find any links with book-like patterns
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/book/' in href or '/.novel/' in href:
                    title_elem = link.find(['h2', 'h3', 'h4', '.title', '.book-title'])
                    title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                    if title and len(title) > 1:
                        novels.append({
                            'title': title,
                            'url': href,
                            'author': 'Unknown',
                            'description': ''
                        })
                        if len(novels) >= 10:  # Limit results
                            break
        else:
            for item in result_items:
                # Extract title
                title_elem = item.select_one('h2 a, h3 a, .title a, .book-title a, a[href*="/book/"], a[href*="/novel/"]')
                if not title_elem:
                    title_elem = item.select_one('a')

                title = title_elem.get_text(strip=True) if title_elem else ''
                url = title_elem.get('href', '') if title_elem else ''

                # Extract author
                author_elem = item.select_one('.author, .book-author, span.author')
                author = author_elem.get_text(strip=True) if author_elem else 'Unknown'

                # Extract description
                desc_elem = item.select_one('.desc, .description, .intro, .book-desc')
                description = desc_elem.get_text(strip=True) if desc_elem else ''

                if title and url:
                    novels.append({
                        'title': title,
                        'url': url,
                        'author': author,
                        'description': description
                    })

        logger.info(f"Parsed {len(novels)} novels from search results")
        return novels

    except Exception as e:
        logger.error(f"Failed to parse search results: {e}")
        raise ParseError(f"Failed to parse search results: {e}")


def parse_chapter_list(html: str) -> List[Dict[str, str]]:
    """
    Parse chapter list page

    Args:
        html: HTML content of chapter list page

    Returns:
        List of chapters with title and url

    Raises:
        ParseError: If parsing fails
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        chapters = []

        # Try to find chapter list container
        chapter_lists = soup.select('.chapter-list, .chapter-lists, .catalog, .volume, .catalog-list')

        for chapter_list in chapter_lists:
            # Find all chapter links
            chapter_links = chapter_list.find_all('a', href=True)
            for link in chapter_links:
                title = link.get_text(strip=True)
                url = link.get('href', '')
                if title and url:
                    chapters.append({
                        'title': title,
                        'url': url
                    })

        # If no chapters found, try alternative selectors
        if not chapters:
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                # Look for chapter-like URLs
                if any(pattern in href for pattern in ['/chapter/', '/read/', '/shu/']):
                    title = link.get_text(strip=True)
                    if title:
                        chapters.append({
                            'title': title,
                            'url': href
                        })

        logger.info(f"Parsed {len(chapters)} chapters")
        return chapters

    except Exception as e:
        logger.error(f"Failed to parse chapter list: {e}")
        raise ParseError(f"Failed to parse chapter list: {e}")


def parse_chapter_content(html: str) -> str:
    """
    Parse chapter content page

    Args:
        html: HTML content of chapter page

    Returns:
        Cleaned chapter content text

    Raises:
        ParseError: If parsing fails
    """
    try:
        soup = BeautifulSoup(html, 'lxml')

        # Try to find content container
        content_elem = soup.select_one('.content, .chapter-content, .read-content, .article-content, #content')

        if content_elem:
            content = content_elem.get_text('\n')
        else:
            # Fallback: look for div or section with lots of text
            all_divs = soup.find_all(['div', 'section', 'article'])
            for div in all_divs:
                text = div.get_text()
                if len(text) > 200:  # Likely content
                    content = text
                    break
            else:
                content = ''

        # Clean content
        cleaned_content = _clean_content(content)

        return cleaned_content

    except Exception as e:
        logger.error(f"Failed to parse chapter content: {e}")
        raise ParseError(f"Failed to parse chapter content: {e}")


def _clean_content(text: str) -> str:
    """
    Clean text content by removing ads and formatting issues

    Args:
        text: Raw text content

    Returns:
        Cleaned text
    """
    # Remove common ad patterns
    ad_patterns = [
        r'本章完',
        r'请关注.*公众号',
        r'关注.*获取更多',
        r'微信.*搜索',
        r'QQ.*群',
        r'求打赏',
        r'推荐票',
        r'感谢.*投',
        r'更多.*请访问',
        r'百度搜索',
    ]

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line and len(line) > 1:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def parse_novel_title(html: str) -> Optional[str]:
    """
    Parse novel title from detail page

    Args:
        html: HTML content

    Returns:
        Novel title or None if not found
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        title_elem = soup.select_one('h1, .title, .book-title, .bookname')
        if title_elem:
            return title_elem.get_text(strip=True)
        return None
    except Exception:
        return None
