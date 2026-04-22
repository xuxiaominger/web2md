#!/usr/bin/env python3
"""
Web2MD - 网页转Markdown工具
将网页内容转换为格式良好的Markdown文件
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web2md.extractor import WebExtractor
from web2md.markdown_formatter import MarkdownFormatter, format_web_content
from web2md.obsidian_sync import ObsidianSync
from web2md.github_sync import GitHubSync
from web2md.gui import create_gui


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='Web2MD - 网页转Markdown工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --url "https://example.com/article"
  python main.py --gui
  python main.py --sync-github --token YOUR_TOKEN
        """
    )

    parser.add_argument('--url', '-u', help='要转换的网页URL')
    parser.add_argument('--gui', '-g', action='store_true', help='启动图形界面')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--obsidian', help='Obsidian库路径')
    parser.add_argument('--sync-github', action='store_true', help='同步到GitHub')
    parser.add_argument('--token', help='GitHub Token')
    parser.add_argument('--repo', default='web2md-notes', help='GitHub仓库名')

    args = parser.parse_args()

    # 图形界面模式
    if args.gui or (not args.url):
        # 默认启动GUI
        obsidian_path = args.obsidian or os.environ.get('OBSIDIAN_PATH')

        # 如果用户提供了obsidian路径但不是完整路径，尝试处理中文路径
        if obsidian_path:
            # 处理中文路径
            obsidian_path = os.path.expanduser(obsidian_path)

        app = create_gui(obsidian_path)
        try:
            app.run()
        except KeyboardInterrupt:
            app.close()
        return

    # 命令行模式
    if args.url:
        convert_url(args.url, args.output, args.obsidian)

    # GitHub同步
    if args.sync-github:
        sync_to_github(args.token, args.repo, args.output or '.')


def convert_url(url: str, output_path: str = None, obsidian_path: str = None):
    """转换单个URL"""
    print(f"正在提取: {url}")

    # 提取内容
    extractor = WebExtractor()
    content = extractor.extract(url)
    extractor.close()

    if 'error' in content:
        print(f"错误: {content['error']}")
        return

    # 转换为Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format(content)

    # 输出
    if output_path:
        filename = formatter.generate_filename(content.get('title', 'untitled'))
        if not output_path.endswith('.md'):
            output_path = os.path.join(output_path, f"{filename}.md")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"已保存到: {output_path}")
    else:
        print(markdown)

    # 保存到Obsidian
    if obsidian_path:
        obsidian = ObsidianSync(obsidian_path)
        filename = formatter.generate_filename(content.get('title', 'untitled'))
        success, message = obsidian.save_markdown(f"{filename}.md", markdown)
        if success:
            print(f"已保存到Obsidian: {message}")
        else:
            print(f"Obsidian保存失败: {message}")


def sync_to_github(token: str, repo_name: str, local_path: str):
    """同步到GitHub"""
    github = GitHubSync(token, repo_name)
    success, message = github.get_or_create_repo()

    if not success:
        print(f"创建仓库失败: {message}")
        return

    success, message = github.push_to_github(local_path)
    if success:
        print(f"推送成功: {message}")
    else:
        print(f"推送失败: {message}")


if __name__ == "__main__":
    main()
