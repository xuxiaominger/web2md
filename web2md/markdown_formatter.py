"""
Markdown格式化模块
将提取的网页内容转换为格式良好的Markdown
"""

import re
import html
from typing import Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import html2text


class MarkdownFormatter:
    """Markdown格式化器"""

    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.body_width = 0  # 不换行
        self.html2text.ignore_links = False
        self.html2text.ignore_images = False
        self.html2text.ignore_emphasis = False
        self.html2text.ignore_tables = False
        self.html2text.single_line_break = True

    def format(self, content: Dict[str, Any], use_trafilatura: bool = True) -> str:
        """
        将提取的内容格式化为Markdown

        Args:
            content: 提取的内容字典
            use_trafilatura: 是否优先使用trafilatura提取

        Returns:
            Markdown格式的字符串
        """
        # 获取原始内容
        raw_content = content.get('content', '')
        title = content.get('title', '')
        author = content.get('author', '')
        date = content.get('date', '')
        url = content.get('url', '')

        # 如果有HTML内容，转换为Markdown
        if raw_content and '<' in raw_content:
            markdown = self._html_to_markdown(raw_content)
        else:
            markdown = raw_content

        # 构建完整的Markdown文档
        result = self._build_markdown_document(
            title=title,
            content=markdown,
            author=author,
            date=date,
            url=url
        )

        return result

    def _html_to_markdown(self, html_content: str) -> str:
        """将HTML转换为Markdown"""
        try:
            # 使用html2text转换
            markdown = self.html2text.handle(html_content)
            return markdown.strip()
        except Exception as e:
            # 回退到简单处理
            return self._simple_html_convert(html_content)

    def _simple_html_convert(self, html_content: str) -> str:
        """简单的HTML转换"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 移除脚本和样式
        for tag in soup(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()

        # 获取纯文本
        text = soup.get_text(separator='\n', strip=True)

        # 清理多余空行
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        return '\n\n'.join(lines)

    def _build_markdown_document(
        self,
        title: str,
        content: str,
        author: Optional[str] = None,
        date: Optional[str] = None,
        url: Optional[str] = None
    ) -> str:
        """构建完整的Markdown文档"""
        parts = []

        # 标题
        if title:
            parts.append(f"# {title}")
            parts.append("")

        # 元信息
        meta_parts = []
        if author:
            meta_parts.append(f"**作者**: {author}")
        if date:
            meta_parts.append(f"**发布日期**: {date}")
        if url:
            meta_parts.append(f"**原文链接**: {url}")

        if meta_parts:
            parts.append("> " + " | ".join(meta_parts))
            parts.append("")

        # 分割线
        parts.append("---")
        parts.append("")

        # 正文内容
        parts.append(content)
        parts.append("")

        # 底部信息
        parts.append("---")
        parts.append("")
        parts.append(f"*本文由 Web2MD 自动转换，生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return '\n'.join(parts)

    def format_title_for_filename(self, title: str) -> str:
        """
        格式化标题用于文件名

        Args:
            title: 原始标题

        Returns:
            适合文件名的字符串
        """
        if not title:
            return "untitled"

        # 移除或替换非法文件名字符
        filename = re.sub(r'[<>:"/\\|?*]', '', title)
        filename = filename.strip()
        filename = re.sub(r'\s+', '_', filename)

        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]

        return filename or "untitled"

    def generate_filename(self, title: str, date: str = None) -> str:
        """
        生成文件名

        Args:
            title: 文章标题
            date: 日期字符串，默认为今天

        Returns:
            完整的文件名（不含扩展名）
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        else:
            # 尝试解析日期
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                date = date_obj.strftime('%Y%m%d')
            except:
                # 如果解析失败，使用今天的日期
                date = datetime.now().strftime('%Y%m%d')

        formatted_title = self.format_title_for_filename(title)

        # 格式：标题_YYYYMMDD
        return f"{formatted_title}_{date}"

    def extract_title_from_html(self, html_content: str) -> str:
        """从HTML中提取标题"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 尝试多种方式获取标题
        # 1. og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # 2. title标签
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.strip()

        # 3. h1标签
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.text.strip()

        return ""

    def clean_content(self, content: str) -> str:
        """清理内容"""
        # 移除多余的空白
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return '\n\n'.join(cleaned_lines)


def format_web_content(content: Dict[str, Any]) -> str:
    """
    便捷函数：格式化网页内容为Markdown

    Args:
        content: 提取的内容字典

    Returns:
        Markdown格式的字符串
    """
    formatter = MarkdownFormatter()
    return formatter.format(content)


def create_markdown_file(title: str, content: str, author: str = None,
                         date: str = None, url: str = None) -> tuple:
    """
    创建Markdown文件内容并生成文件名

    Args:
        title: 文章标题
        content: 文章内容
        author: 作者
        date: 日期
        url: 原文链接

    Returns:
        (filename, markdown_content)
    """
    formatter = MarkdownFormatter()

    content_dict = {
        'title': title,
        'content': content,
        'author': author,
        'date': date,
        'url': url
    }

    markdown = formatter.format(content_dict)
    filename = formatter.generate_filename(title, date)

    return filename, markdown
