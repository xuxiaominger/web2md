"""
搜索引擎模块
支持多种搜索引擎获取搜索结果
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse


class SearchEngine:
    """搜索引擎基类"""

    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        搜索关键词

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量

        Returns:
            搜索结果列表，每项包含 title, url, snippet
        """
        raise NotImplementedError


class BaiduSearch(SearchEngine):
    """百度搜索"""

    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        results = []
        url = f"https://www.baidu.com/s?wd={urllib.parse.quote(keyword)}&rn={limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')

            # 百度搜索结果容器
            for item in soup.select('.result, .c-container')[:limit]:
                try:
                    title_elem = item.select_one('h3 a, .t a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    # 百度URL需要跳转
                    if 'baidu.com' in url:
                        continue

                    snippet_elem = item.select_one('.c-abstract, .snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'engine': 'baidu'
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"百度搜索失败: {e}")

        return results


class BingSearch(SearchEngine):
    """必应搜索"""

    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        results = []
        url = f"https://www.bing.com/search?q={urllib.parse.quote(keyword)}&count={limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'lxml')

            for item in soup.select('.b_algo')[:limit]:
                try:
                    title_elem = item.select_one('h2 a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')

                    snippet_elem = item.select_one('.b_caption p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'engine': 'bing'
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Bing搜索失败: {e}")

        return results


class GoogleSearch(SearchEngine):
    """Google搜索（需要代理）"""

    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, str]]:
        results = []
        url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&num={limit}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'lxml')

            for item in soup.select('.g')[:limit]:
                try:
                    title_elem = item.select_one('h3')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link_elem = item.select_one('a')
                    url = link_elem.get('href', '') if link_elem else ''

                    if title and url and url.startswith('http'):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': '',
                            'engine': 'google'
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Google搜索失败: {e}")

        return results


def get_search_engine(name: str = 'baidu') -> SearchEngine:
    """
    获取搜索引擎实例

    Args:
        name: 搜索引擎名称 (baidu/bing/google)

    Returns:
        搜索引擎实例
    """
    engines = {
        'baidu': BaiduSearch,
        'bing': BingSearch,
        'google': GoogleSearch,
    }

    engine_class = engines.get(name.lower(), BaiduSearch)
    return engine_class()


def search(keyword: str, engine: str = 'baidu', limit: int = 10) -> List[Dict[str, str]]:
    """
    便捷搜索函数

    Args:
        keyword: 搜索关键词
        engine: 搜索引擎名称
        limit: 返回结果数量

    Returns:
        搜索结果列表
    """
    se = get_search_engine(engine)
    return se.search(keyword, limit)
