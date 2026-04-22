"""
特殊网站处理模块
自动识别并使用定制规则处理微信公众号、知乎、Medium等特殊网站
"""

import re
import json
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from bs4 import BeautifulSoup


class SpecialSiteHandler:
    """特殊网站处理器"""

    # 特殊网站配置
    SPECIAL_SITES = {
        'weixin.qq.com': {
            'name': '微信公众号',
            'method': 'wechat',
            'need_js': True
        },
        'zhihu.com': {
            'name': '知乎',
            'method': 'zhihu',
            'need_js': True
        },
        'medium.com': {
            'name': 'Medium',
            'method': 'medium',
            'need_js': True
        },
        'm.weibo.cn': {
            'name': '微博',
            'method': 'weibo',
            'need_js': True
        },
        'weibo.com': {
            'name': '微博',
            'method': 'weibo',
            'need_js': True
        },
        'mp.weixin.qq.com': {
            'name': '微信公众号',
            'method': 'wechat',
            'need_js': True
        },
        'juejin.cn': {
            'name': '掘金',
            'method': 'juejin',
            'need_js': False
        },
        'juejin.im': {
            'name': '掘金',
            'method': 'juejin',
            'need_js': False
        },
        'csdn.net': {
            'name': 'CSDN',
            'method': 'csdn',
            'need_js': False
        },
        'segmentfault.com': {
            'name': 'SegmentFault',
            'method': 'segmentfault',
            'need_js': False
        },
        'stackoverflow.com': {
            'name': 'StackOverflow',
            'method': 'stackoverflow',
            'need_js': False
        },
        'github.com': {
            'name': 'GitHub',
            'method': 'github_readme',
            'need_js': False
        },
        'dev.to': {
            'name': 'Dev.to',
            'method': 'devto',
            'need_js': False
        },
        'cloud.tencent.com': {
            'name': '腾讯云',
            'method': 'tencent_cloud',
            'need_js': False
        },
        'aliyun.com': {
            'name': '阿里云',
            'method': 'aliyun',
            'need_js': False
        }
    }

    def __init__(self):
        self.driver = None

    def identify_site(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        识别网站类型

        Args:
            url: 网页URL

        Returns:
            (网站名称, 网站配置) 或 (None, None)
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]

        # 精确匹配
        if domain in self.SPECIAL_SITES:
            return self.SPECIAL_SITES[domain]['name'], self.SPECIAL_SITES[domain]

        # 部分匹配
        for site_domain, config in self.SPECIAL_SITES.items():
            if site_domain in domain:
                return config['name'], config

        return None, None

    def extract(self, url: str, config: Dict) -> Dict[str, Any]:
        """
        根据配置提取网页内容

        Args:
            url: 网页URL
            config: 网站配置

        Returns:
            提取的内容字典
        """
        method = config.get('method', 'generic')

        if method == 'wechat':
            return self._extract_wechat(url)
        elif method == 'zhihu':
            return self._extract_zhihu(url)
        elif method == 'medium':
            return self._extract_medium(url)
        elif method == 'weibo':
            return self._extract_weibo(url)
        elif method == 'juejin':
            return self._extract_juejin(url)
        elif method == 'csdn':
            return self._extract_csdn(url)
        elif method == 'stackoverflow':
            return self._extract_stackoverflow(url)
        elif method == 'github_readme':
            return self._extract_github_readme(url)
        elif method == 'devto':
            return self._extract_devto(url)
        else:
            return {'title': '', 'content': '', 'error': '未支持的网站类型'}

    def _init_driver(self):
        """初始化Chrome驱动"""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')

            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.set_page_load_timeout(30)
            except Exception as e:
                print(f"初始化Chrome驱动失败: {e}")
                # 使用备用方案
                self.driver = None

    def _extract_wechat(self, url: str) -> Dict[str, Any]:
        """提取微信公众号文章"""
        self._init_driver()

        if self.driver is None:
            # 尝试使用API方式
            return self._extract_wechat_api(url)

        try:
            self.driver.get(url)
            time.sleep(3)

            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "activity-name"))
            )

            # 获取标题
            title_elem = self.driver.find_element(By.ID, "activity-name")
            title = title_elem.text.strip() if title_elem else ""

            # 获取作者
            author = ""
            try:
                author_elem = self.driver.find_element(By.ID, "js_author_name")
                author = author_elem.text.strip()
            except:
                pass

            # 获取发布日期
            publish_date = ""
            try:
                date_elem = self.driver.find_element(By.ID, "publish_date")
                publish_date = date_elem.text.strip()
            except:
                pass

            # 获取正文内容
            content_elem = self.driver.find_element(By.ID, "js_content")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            # 清理内容
            for tag in soup(['script', 'style', 'iframe', 'form']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {
                'title': title,
                'content': content,
                'author': author,
                'date': publish_date,
                'url': url
            }
        except Exception as e:
            return self._extract_wechat_api(url)

    def _extract_wechat_api(self, url: str) -> Dict[str, Any]:
        """使用微信API提取文章（备用方案）"""
        # 从URL中提取文章ID
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')

        # 尝试从URL获取文章ID
        article_id = None
        if 'appmsg' in url:
            match = re.search(r'appmsg([^&]+)', url)
            if match:
                params = parse_qs(match.group(1))
                article_id = params.get('mid', [None])[0] or params.get('appmsgid', [None])[0]

        # 返回基本结果
        return {
            'title': '微信公众号文章',
            'content': f'请手动访问: {url}\n\n该文章需要登录微信才能提取完整内容。',
            'url': url,
            'note': '微信文章需要微信客户端或Cookie才能完整提取'
        }

    def _extract_zhihu(self, url: str) -> Dict[str, Any]:
        """提取知乎文章"""
        self._init_driver()

        if self.driver is None:
            return {'title': '知乎文章', 'content': f'无法提取，请访问: {url}', 'url': url}

        try:
            self.driver.get(url)
            time.sleep(3)

            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Post-Title"))
            )

            # 获取标题
            title_elem = self.driver.find_element(By.CLASS_NAME, "Post-Title")
            title = title_elem.text.strip() if title_elem else ""

            # 获取作者
            author = ""
            try:
                author_elem = self.driver.find_element(By.CLASS_NAME, "AuthorInfo-name")
                author = author_elem.text.strip()
            except:
                pass

            # 获取发布日期
            publish_date = ""
            try:
                date_elem = self.driver.find_element(By.CLASS_NAME, "PublishTime")
                publish_date = date_elem.text.strip()
            except:
                pass

            # 获取正文内容
            content_elem = self.driver.find_element(By.CLASS_NAME, "Post-RichText")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            # 清理并获取文本
            for tag in soup(['script', 'style', 'iframe', 'ad']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {
                'title': title,
                'content': content,
                'author': author,
                'date': publish_date,
                'url': url
            }
        except Exception as e:
            # 备用方案：使用知乎API
            return self._extract_zhihu_api(url)

    def _extract_zhihu_api(self, url: str) -> Dict[str, Any]:
        """使用知乎API提取"""
        # 提取文章ID
        match = re.search(r'zhihu\.com/question/(\d+)', url)
        if not match:
            match = re.search(r'zhuanlan\.zhihu\.com/([a-zA-Z0-9-]+)', url)

        # 返回基本信息
        return {
            'title': '知乎文章',
            'content': f'请手动访问: {url}\n\n建议使用Selenium或手动复制内容。',
            'url': url
        }

    def _extract_medium(self, url: str) -> Dict[str, Any]:
        """提取Medium文章"""
        self._init_driver()

        if self.driver is None:
            return {'title': 'Medium文章', 'content': f'无法提取，请访问: {url}', 'url': url}

        try:
            self.driver.get(url)
            time.sleep(3)

            # 等待页面加载
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )

            # 获取标题
            title = ""
            try:
                title_elem = self.driver.find_element(By.TAG_NAME, "h1")
                title = title_elem.text.strip()
            except:
                pass

            # 获取作者
            author = ""
            try:
                author_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='authorName']")
                author = author_elem.text.strip()
            except:
                pass

            # 获取正文内容
            content_elem = self.driver.find_element(By.TAG_NAME, "article")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            # 清理内容
            for tag in soup(['script', 'style', 'iframe']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {
                'title': title,
                'content': content,
                'author': author,
                'url': url
            }
        except Exception as e:
            return {'title': 'Medium文章', 'content': f'提取失败: {str(e)}\n\n请访问: {url}', 'url': url}

    def _extract_weibo(self, url: str) -> Dict[str, Any]:
        """提取微博内容"""
        self._init_driver()

        if self.driver is None:
            return {'title': '微博', 'content': f'无法提取，请访问: {url}', 'url': url}

        try:
            self.driver.get(url)
            time.sleep(3)

            # 获取内容
            content = ""
            try:
                content_elem = self.driver.find_element(By.CLASS_NAME, "weibo-text")
                content = content_elem.text.strip()
            except:
                try:
                    content_elem = self.driver.find_element(By.CLASS_NAME, "WB_text")
                    content = content_elem.text.strip()
                except:
                    pass

            # 获取标题/用户
            title = ""
            try:
                user_elem = self.driver.find_element(By.CLASS_NAME, "WB_name")
                title = user_elem.text.strip()
            except:
                title = "微博内容"

            return {
                'title': title,
                'content': content,
                'url': url
            }
        except Exception as e:
            return {'title': '微博', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_juejin(self, url: str) -> Dict[str, Any]:
        """提取掘金文章"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # 获取标题
            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.text.strip()

            # 获取正文
            content_elem = soup.find('article') or soup.find(class_=re.compile(r'content|article'))
            if content_elem:
                # 清理脚本和样式
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {
                'title': title,
                'content': content,
                'url': url
            }
        except Exception as e:
            return {'title': '掘金文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_csdn(self, url: str) -> Dict[str, Any]:
        """提取CSDN文章"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # 获取标题
            title = ""
            title_elem = soup.find('h1', class_='title-article')
            if not title_elem:
                title_elem = soup.find('title')
            if title_elem:
                title = title_elem.text.strip()

            # 获取正文 - CSDN主要内容在blog_content或article_content中
            content_elem = soup.find('div', id='article_content') or \
                          soup.find('div', class_='blog_content') or \
                          soup.find('article')

            if content_elem:
                for tag in content_elem(['script', 'style', 'iframe', 'ad']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {
                'title': title,
                'content': content,
                'url': url
            }
        except Exception as e:
            return {'title': 'CSDN文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_stackoverflow(self, url: str) -> Dict[str, Any]:
        """提取StackOverflow内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # 获取标题
            title = ""
            title_elem = soup.find('a', class_='question-hyperlink')
            if title_elem:
                title = title_elem.text.strip()

            # 获取问题内容
            question_elem = soup.find('div', class_='s-prose')
            if question_elem:
                for tag in question_elem(['script', 'style']):
                    tag.decompose()
                content = question_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {
                'title': title,
                'content': content,
                'url': url
            }
        except Exception as e:
            return {'title': 'StackOverflow', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_github_readme(self, url: str) -> Dict[str, Any]:
        """提取GitHub README"""
        # 转换URL为原始内容URL
        # https://github.com/user/repo -> https://raw.githubusercontent.com/user/repo/main/README.md
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if len(path_parts) >= 2:
            user, repo = path_parts[0], path_parts[1]
            # 尝试获取README
            for readme_name in ['README.md', 'README.rst', 'README', 'readme.md']:
                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{readme_name}"
                try:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        return {
                            'title': f"{user}/{repo} README",
                            'content': response.text,
                            'url': url
                        }
                except:
                    pass

            # 尝试master分支
            for readme_name in ['README.md', 'README.rst', 'README']:
                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/master/{readme_name}"
                try:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        return {
                            'title': f"{user}/{repo} README",
                            'content': response.text,
                            'url': url
                        }
                except:
                    pass

        return {
            'title': 'GitHub仓库',
            'content': f'无法自动提取README，请访问: {url}',
            'url': url
        }

    def _extract_devto(self, url: str) -> Dict[str, Any]:
        """提取Dev.to文章"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # 获取标题
            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.text.strip()

            # 获取正文
            content_elem = soup.find('div', class_='crayons-article__body')
            if not content_elem:
                content_elem = soup.find('article')

            if content_elem:
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {
                'title': title,
                'content': content,
                'url': url
            }
        except Exception as e:
            return {'title': 'Dev.to文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def close(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# 便捷函数
def detect_and_extract(url: str) -> Dict[str, Any]:
    """
    自动识别网站并提取内容

    Args:
        url: 网页URL

    Returns:
        提取的内容字典
    """
    handler = SpecialSiteHandler()
    try:
        site_name, config = handler.identify_site(url)

        if config:
            return handler.extract(url, config)
        else:
            return {'title': '', 'content': '', 'error': '未知网站类型'}
    finally:
        handler.close()
