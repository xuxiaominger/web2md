"""
综合解决方案 - 使用多种方式提取被保护网站的内容
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any


class AdvancedExtractor:
    """高级提取器 - 尝试多种方式提取被保护网站的内容"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    def extract(self, url: str) -> Dict[str, Any]:
        """尝试多种方式提取内容"""

        # 1. 尝试使用 textise dot iitty (通用)
        result = self._try_textise(url)
        if result:
            return result

        # 2. 尝试使用 textise dot iitty API
        result = self._try_textise_api(url)
        if result:
            return result

        # 3. 尝试使用 txtify.it
        result = self._try_txtify(url)
        if result:
            return result

        # 4. 返回友好提示
        return self._get_fallback_result(url)

    def _try_textise(self, url: str) -> Dict[str, Any]:
        """使用 textise dot iitty"""
        try:
            textise_url = f"https://r.jina.ai/{url}"
            response = self.session.get(textise_url, timeout=15)
            if response.status_code == 200:
                text = response.text
                if text and len(text) > 100 and "error" not in text.lower():
                    # 解析返回的内容
                    lines = text.split('\n')
                    title = ""
                    content_lines = []
                    for line in lines:
                        if line.startswith('Title:'):
                            title = line.replace('Title:', '').strip()
                        elif line.startswith('URL Source:'):
                            continue
                        elif line.startswith('Published Time:'):
                            continue
                        elif line.startswith('Warning:'):
                            continue
                        elif line.strip():
                            content_lines.append(line)

                    if title or content_lines:
                        return {
                            'title': title or '提取的文章',
                            'content': '\n'.join(content_lines),
                            'url': url
                        }
        except:
            pass
        return None

    def _try_textise_api(self, url: str) -> Dict[str, Any]:
        """使用 textise dot iitty API"""
        try:
            # 尝试使用 textise dot iitty 的其他格式
            textise_url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"
            response = self.session.get(textise_url, timeout=15)
            if response.status_code == 200 and len(response.text) > 100:
                return {
                    'title': '提取的文章',
                    'content': response.text,
                    'url': url
                }
        except:
            pass
        return None

    def _try_txtify(self, url: str) -> Dict[str, Any]:
        """尝试使用 txtify.it"""
        try:
            # txtify.it 可能不可用，跳过
            pass
        except:
            pass
        return None

    def _get_fallback_result(self, url: str) -> Dict[str, Any]:
        """返回备用结果 - 提供多种解决方案"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()

        # 判断网站类型并提供相应提示
        solutions = []

        if 'zhihu.com' in domain:
            solutions = [
                "1. 手动复制内容后粘贴到输入框",
                "2. 使用浏览器插件如 Web Clipper",
                "3. 使用桌面版 GUI（需要安装 Selenium）",
                "4. 登录知乎后使用cookie提取"
            ]
        elif 'weixin.qq.com' in domain or 'mp.weixin.qq.com' in domain:
            solutions = [
                "1. 手动复制内容",
                "2. 使用微信读书分享功能",
                "3. 截图后使用 OCR 识别",
                "4. 使用桌面版 GUI（需要安装 Selenium）"
            ]
        elif 'medium.com' in domain:
            solutions = [
                "1. 手动复制内容",
                "2. 使用 Medium 的 Export 功能",
                "3. 使用桌面版 GUI（需要安装 Selenium）"
            ]
        elif 'weibo.com' in domain or 'm.weibo.cn' in domain:
            solutions = [
                "1. 手动复制内容",
                "2. 使用微博备份工具",
                "3. 使用桌面版 GUI（需要安装 Selenium）"
            ]
        else:
            solutions = [
                "1. 手动复制内容后粘贴",
                "2. 尝试使用桌面版 GUI"
            ]

        return {
            'title': '无法自动提取的内容',
            'content': f'''该网站({domain})有反爬虫保护，无法自动提取内容。

可能的解决方案：
{chr(10).join(solutions)}

原文链接: {url}

---
提示：如需提取此类网站内容，建议使用桌面版程序配合 Selenium。''',
            'url': url
        }


def advanced_extract(url: str) -> Dict[str, Any]:
    """便捷函数 - 高级提取"""
    extractor = AdvancedExtractor()
    return extractor.extract(url)
