"""
搜索引擎模块 - 使用 DuckDuckGo HTML 版本，更稳定
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
import re


def search_duckduckgo(keyword: str, limit: int = 50) -> List[Dict]:
    """DuckDuckGo HTML 搜索"""
    results = []
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(keyword)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'lxml')

        for item in soup.select('.result'):
            try:
                title_elem = item.select_one('.result__title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link_elem = title_elem.select_one('a')
                link = link_elem.get('href', '') if link_elem else ''

                if not title or not link:
                    continue

                # 获取描述
                desc_elem = item.select_one('.result__snippet')
                desc = desc_elem.get_text(strip=True) if desc_elem else ''

                results.append({
                    'title': title[:200],
                    'url': link,
                    'snippet': desc[:200],
                    'engine': 'duckduckgo'
                })

                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"DuckDuckGo搜索失败: {e}")

    return results


def search_bing(keyword: str, limit: int = 50) -> List[Dict]:
    """Bing 搜索"""
    results = []
    url = f"https://www.bing.com/search?q={urllib.parse.quote(keyword)}&count={limit}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, 'lxml')

        for item in soup.select('.b_algo'):
            try:
                title_elem = item.select_one('h2 a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')

                if not title or not link:
                    continue

                desc_elem = item.select_one('.b_caption p')
                desc = desc_elem.get_text(strip=True) if desc_elem else ''

                results.append({
                    'title': title[:200],
                    'url': link,
                    'snippet': desc[:200],
                    'engine': 'bing'
                })

                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"Bing搜索失败: {e}")

    return results


def search_baidu(keyword: str, limit: int = 50) -> List[Dict]:
    """百度搜索"""
    results = []
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}&rn={limit}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'lxml')

        for item in soup.select('.c-container, .result'):
            try:
                title_elem = item.select_one('h3 a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')

                if not title or not link:
                    continue

                # 跳过百度内部链接
                if 'baidu.com' in link and not link.startswith('http'):
                    continue

                desc_elem = item.select_one('.c-abstract')
                desc = desc_elem.get_text(strip=True) if desc_elem else ''

                results.append({
                    'title': title[:200],
                    'url': link,
                    'snippet': desc[:200],
                    'engine': 'baidu'
                })

                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"百度搜索失败: {e}")

    return results


def search(keyword: str, engine: str = 'duckduckgo', limit: int = 50) -> List[Dict]:
    """搜索主函数 - 尝试多个引擎"""
    if not keyword:
        return []

    # 尝试 DuckDuckGo (最稳定)
    results = search_duckduckgo(keyword, limit)
    if results:
        return results

    # 尝试 Bing
    results = search_bing(keyword, limit)
    if results:
        return results

    # 尝试百度
    results = search_baidu(keyword, limit)

    return results
