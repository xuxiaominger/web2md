"""
Obsidian同步模块
将转换的Markdown文件保存到Obsidian库
"""

import os
import shutil
from typing import Tuple, Optional
from datetime import datetime
from pathlib import Path


class ObsidianSync:
    """Obsidian同步器"""

    def __init__(self, vault_path: str):
        """
        初始化Obsidian同步器

        Args:
            vault_path: Obsidian库路径
        """
        self.vault_path = Path(vault_path).expanduser().resolve()

        # 验证路径是否存在
        if not self.vault_path.exists():
            # 尝试创建目录
            try:
                self.vault_path.mkdir(parents=True, exist_ok=True)
                print(f"已创建Obsidian库目录: {self.vault_path}")
            except Exception as e:
                print(f"警告: 无法创建Obsidian库目录: {e}")

    def save_markdown(self, filename: str, content: str, subfolder: str = None) -> Tuple[bool, str]:
        """
        保存Markdown文件到Obsidian库

        Args:
            filename: 文件名
            content: Markdown内容
            subfolder: 子文件夹（可选）

        Returns:
            (success, message)
        """
        try:
            # 确定目标路径
            if subfolder:
                target_dir = self.vault_path / subfolder
            else:
                target_dir = self.vault_path

            # 创建目录（如果不存在）
            target_dir.mkdir(parents=True, exist_ok=True)

            # 完整文件路径
            file_path = target_dir / filename

            # 检查文件是否已存在
            if file_path.exists():
                # 添加时间戳避免覆盖
                timestamp = datetime.now().strftime('%H%M%S')
                name_parts = filename.rsplit('.md', 1)
                if len(name_parts) == 2:
                    filename = f"{name_parts[0]}_{timestamp}.md"
                else:
                    filename = f"{filename}_{timestamp}"
                file_path = target_dir / filename

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 确保文件可被Obsidian索引（添加frontmatter）
            self._ensure_frontmatter(file_path)

            return True, str(file_path)

        except Exception as e:
            return False, str(e)

    def _ensure_frontmatter(self, file_path: Path):
        """确保文件有Obsidian frontmatter"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已有frontmatter
            if content.startswith('---'):
                return  # 已有frontmatter

            # 添加frontmatter
            title = file_path.stem.replace('_', ' ')
            frontmatter = f"""---
title: "{title}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
source: web2md
---

"""
            new_content = frontmatter + content

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

        except Exception as e:
            print(f"添加frontmatter失败: {e}")

    def save_with_category(self, filename: str, content: str, category: str) -> Tuple[bool, str]:
        """
        保存到指定分类文件夹

        Args:
            filename: 文件名
            content: Markdown内容
            category: 分类文件夹名称

        Returns:
            (success, message)
        """
        # 根据URL或内容自动判断分类
        # 常见分类：技术、学习、生活
        return self.save_markdown(filename, content, subfolder=category)

    def list_files(self, pattern: str = "*.md") -> list:
        """
        列出库中的Markdown文件

        Args:
            pattern: 文件匹配模式

        Returns:
            文件列表
        """
        try:
            return list(self.vault_path.glob(f"**/{pattern}"))
        except Exception as e:
            print(f"列出文件失败: {e}")
            return []

    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        return (self.vault_path / filename).exists()

    def get_vault_path(self) -> str:
        """获取库路径"""
        return str(self.vault_path)

    def create_daily_note(self, content: str = None) -> Tuple[bool, str]:
        """
        创建每日笔记

        Args:
            content: 笔记内容（可选）

        Returns:
            (success, message)
        """
        today = datetime.now().strftime('%Y年%m月%d日')
        filename = f"{today}.md"

        if content is None:
            content = f"""# {today}

## 今日计划


## 今日总结


"""

        return self.save_markdown(filename, content)

    def backup_to_git(self, repo_path: str, commit_message: str = None) -> Tuple[bool, str]:
        """
        备份到Git仓库

        Args:
            repo_path: Git仓库路径
            commit_message: 提交信息

        Returns:
            (success, message)
        """
        if not commit_message:
            commit_message = f"Web2MD: 添加新笔记 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        try:
            import subprocess

            # 检查git是否可用
            result = subprocess.run(['git', '--version'], capture_output=True)
            if result.returncode != 0:
                return False, "Git不可用"

            # 执行git操作
            commands = [
                ['git', '-C', repo_path, 'add', '.'],
                ['git', '-C', repo_path, 'commit', '-m', commit_message],
                ['git', '-C', repo_path, 'push']
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"Git操作失败: {result.stderr}"

            return True, "已推送到Git"

        except FileNotFoundError:
            return False, "Git未安装"
        except Exception as e:
            return False, str(e)


def create_obsidian_sync(vault_path: str) -> ObsidianSync:
    """
    创建Obsidian同步器

    Args:
        vault_path: Obsidian库路径

    Returns:
        ObsidianSync实例
    """
    return ObsidianSync(vault_path)


# 测试
if __name__ == "__main__":
    # 测试
    vault = ObsidianSync("~/Documents/我的笔记本/test")
    print(f"Obsidian库路径: {vault.get_vault_path()}")
