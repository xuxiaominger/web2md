"""
搜索引擎模块 - 使用多种可靠的搜索API
"""

import requests
from typing import List, Dict
import urllib.parse
import json


def search_duckduckgo_instant(keyword: str, limit: int = 50) -> List[Dict]:
    """DuckDuckGo Instant Answer API"""
    results = []
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(keyword)}&format=json&no_html=1"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()

        # 获取相关搜索结果
        for item in data.get('RelatedTopics', [])[:limit]:
            if 'Text' in item and 'FirstURL' in item:
                results.append({
                    'title': item['Text'][:200],
                    'url': item['FirstURL'],
                    'snippet': '',
                    'engine': 'duckduckgo'
                })

    except Exception as e:
        print(f"DuckDuckGo API 失败: {e}")

    return results


def search_ddg_html(keyword: str, limit: int = 50) -> List[Dict]:
    """DuckDuckGo HTML 页面解析"""
    results = []
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(keyword)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)

        # 简单解析
        import re
        # 匹配搜索结果
        pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, resp.text)

        for url, title in matches[:limit]:
            title = title.strip()
            if title and url:
                results.append({
                    'title': title[:200],
                    'url': url,
                    'snippet': '',
                    'engine': 'duckduckgo'
                })

    except Exception as e:
        print(f"DuckDuckGo HTML 失败: {e}")

    return results


def search_serpapi(keyword: str, limit: int = 50) -> List[Dict]:
    """使用 SerpAPI (需要免费API key) 或模拟"""
    results = []

    # 尝试使用 Bing 的简单搜索
    url = "https://www.bing.com/search"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    }

    params = {
        'q': keyword,
        'count': limit,
        'form': 'QBLH'
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)

        # 解析 Bing 结果
        import re
        # 匹配标题和链接
        pattern = r'<li class="b_algo"><h2><a href="([^"]+)"[^>]*>([^<]+)</a></h2>'
        matches = re.findall(pattern, resp.text)

        for url, title in matches[:limit]:
            title = re.sub(r'<[^>]+>', '', title).strip()
            if title and url:
                results.append({
                    'title': title[:200],
                    'url': url,
                    'snippet': '',
                    'engine': 'bing'
                })

    except Exception as e:
        print(f"Bing 搜索失败: {e}")

    return results


def search_startpage(keyword: str, limit: int = 50) -> List[Dict]:
    """Startpage 搜索"""
    results = []
    url = f"https://www.startpage.com/do/search?query={urllib.parse.quote(keyword)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)

        import re
        pattern = r'<a class="w-gl__result-title" href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, resp.text)

        for url, title in matches[:limit]:
            title = title.strip()
            if title and url:
                results.append({
                    'title': title[:200],
                    'url': url,
                    'snippet': '',
                    'engine': 'startpage'
                })

    except Exception as e:
        print(f"Startpage 失败: {e}")

    return results


def search_yahoo(keyword: str, limit: int = 50) -> List[Dict]:
    """Yahoo 搜索"""
    results = []
    url = f"https://search.yahoo.com/search?p={urllib.parse.quote(keyword)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)

        import re
        pattern = r'<li class="algo"><h3><a href="([^"]+)"[^>]*>([^<]+)</a></h3>'
        matches = re.findall(pattern, resp.text)

        for url, title in matches[:limit]:
            title = title.strip()
            if title and url:
                results.append({
                    'title': title[:200],
                    'url': url,
                    'snippet': '',
                    'engine': 'yahoo'
                })

    except Exception as e:
        print(f"Yahoo 失败: {e}")

    return results


def search(keyword: str, engine: str = 'ddg', limit: int = 50) -> List[Dict]:
    """主搜索函数 - 尝试多个引擎"""
    if not keyword:
        return []

    # 尝试 DuckDuckGo Instant API
    results = search_duckduckgo_instant(keyword, limit)
    if results:
        return results

    # 尝试 DuckDuckGo HTML
    results = search_ddg_html(keyword, limit)
    if results:
        return results

    # 尝试 Yahoo
    results = search_yahoo(keyword, limit)
    if results:
        return results

    # 尝试 Bing
    results = search_serpapi(keyword, limit)

    return results
