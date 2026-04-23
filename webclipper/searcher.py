"""
搜索引擎模块 - 支持多种搜索引擎
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse
import re


class BaiduSearch:
    """百度搜索"""

    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, str]]:
        results = []
        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}&rn={limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')

            # 百度搜索结果
            for item in soup.select('.c-container, .result'):
                try:
                    title_elem = item.select_one('h3 a')
                    if not title_elem:
                        title_elem = item.select_one('.t a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')

                    if not title or not link:
                        continue

                    # 跳过百度内部链接
                    if 'baidu.com' in link and not link.startswith('http'):
                        continue

                    # 获取描述
                    desc_elem = item.select_one('.c-abstract, .content-right_8Zs40, .result-info')
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''

                    if title and link:
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

        return results[:limit]


class BingSearch:
    """必应搜索"""

    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, str]]:
        results = []
        url = f"https://www.bing.com/search?q={urllib.parse.quote(keyword)}&count={limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')

            for item in soup.select('.b_algo')[:limit]:
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
                except Exception:
                    continue
        except Exception as e:
            print(f"Bing搜索失败: {e}")

        return results[:limit]


class DuckDuckGoSearch:
    """DuckDuckGo搜索 - 不需要代理"""

    def search(self, keyword: str, limit: int = 50) -> List[Dict[str, str]]:
        results = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(keyword)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')

            for item in soup.select('.result')[:limit]:
                try:
                    title_elem = item.select_one('.result__title')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link_elem = title_elem.select_one('a')
                    link = link_elem.get('href', '') if link_elem else ''

                    desc_elem = item.select_one('.result__snippet')
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''

                    if title and link:
                        results.append({
                            'title': title[:200],
                            'url': link,
                            'snippet': desc[:200],
                            'engine': 'duckduckgo'
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {e}")

        return results[:limit]


def get_search_engine(name: str = 'baidu'):
    """获取搜索引擎实例"""
    engines = {
        'baidu': BaiduSearch,
        'bing': BingSearch,
        'duckduckgo': DuckDuckGoSearch,
    }
    engine_class = engines.get(name.lower(), BaiduSearch)
    return engine_class()


def search(keyword: str, engine: str = 'baidu', limit: int = 50) -> List[Dict[str, str]]:
    """便捷搜索函数"""
    if not keyword:
        return []

    # 尝试多个搜索引擎
    engines = ['baidu', 'bing', 'duckduckgo'] if engine == 'baidu' else [engine]

    for eng in engines:
        try:
            se = get_search_engine(eng)
            results = se.search(keyword, limit)
            if results:
                return results
        except Exception as e:
            print(f"搜索引擎 {eng} 失败: {e}")
            continue

    return []
