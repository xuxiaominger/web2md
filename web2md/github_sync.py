"""
GitHub同步模块
将项目同步到GitHub仓库
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from github import Github
from github.GithubException import GithubException


class GitHubSync:
    """GitHub同步器"""

    def __init__(self, token: str = None, repo_name: str = "web2md"):
        """
        初始化GitHub同步器

        Args:
            token: GitHub Personal Access Token
            repo_name: 仓库名称
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.repo_name = repo_name
        self.github = None
        self.repo = None

        if self.token:
            try:
                self.github = Github(self.token)
            except Exception as e:
                print(f"GitHub初始化失败: {e}")

    def create_repo(self, private: bool = False, description: str = None) -> Tuple[bool, str]:
        """
        创建GitHub仓库

        Args:
            private: 是否私有
            description: 仓库描述

        Returns:
            (success, message)
        """
        if not self.github:
            return False, "GitHub Token未配置"

        try:
            user = self.github.get_user()

            # 创建仓库
            repo = user.create_repo(
                name=self.repo_name,
                description=description or "Web2MD - 网页转Markdown工具",
                private=private,
                auto_init=True
            )

            self.repo = repo
            return True, repo.clone_url

        except GithubException as e:
            return False, f"创建仓库失败: {str(e)}"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def get_or_create_repo(self, private: bool = False) -> Tuple[bool, str]:
        """
        获取或创建仓库

        Args:
            private: 是否私有

        Returns:
            (success, message)
        """
        if not self.github:
            return False, "GitHub Token未配置"

        try:
            user = self.github.get_user()

            # 尝试获取现有仓库
            try:
                repo = user.get_repo(self.repo_name)
                self.repo = repo
                return True, repo.clone_url
            except:
                pass

            # 创建新仓库
            return self.create_repo(private)

        except Exception as e:
            return False, str(e)

    def push_to_github(self, local_path: str, commit_message: str = None) -> Tuple[bool, str]:
        """
        推送本地代码到GitHub

        Args:
            local_path: 本地项目路径
            commit_message: 提交信息

        Returns:
            (success, message)
        """
        if not self.repo:
            return False, "仓库未初始化"

        try:
            import subprocess
            from pathlib import Path

            local_path = Path(local_path).resolve()

            if not local_path.exists():
                return False, "本地路径不存在"

            # 初始化git（如果需要）
            git_dir = local_path / '.git'
            if not git_dir.exists():
                subprocess.run(['git', 'init'], cwd=local_path, check=True)
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', self.repo.clone_url],
                    cwd=local_path,
                    check=True
                )

            # 添加所有文件
            subprocess.run(['git', 'add', '.'], cwd=local_path, check=True)

            # 提交
            if not commit_message:
                commit_message = f"Update: Web2MD {self._get_timestamp()}"

            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=local_path,
                check=True
            )

            # 推送到GitHub
            # 注意：可能需要处理分支名称
            result = subprocess.run(
                ['git', 'push', '-u', 'origin', 'main'],
                cwd=local_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return True, self.repo.html_url
            else:
                # 尝试master分支
                result = subprocess.run(
                    ['git', 'push', '-u', 'origin', 'master'],
                    cwd=local_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True, self.repo.html_url
                return False, result.stderr

        except subprocess.CalledProcessError as e:
            return False, f"Git命令失败: {str(e)}"
        except Exception as e:
            return False, str(e)

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_repo_url(self) -> Optional[str]:
        """获取仓库URL"""
        if self.repo:
            return self.repo.html_url
        return None


def create_github_sync(token: str = None, repo_name: str = "web2md") -> GitHubSync:
    """
    创建GitHub同步器

    Args:
        token: GitHub Token
        repo_name: 仓库名称

    Returns:
        GitHubSync实例
    """
    return GitHubSync(token, repo_name)


# 命令行工具
def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Web2MD GitHub同步工具')
    parser.add_argument('--token', '-t', help='GitHub Token')
    parser.add_argument('--repo', '-r', default='web2md', help='仓库名称')
    parser.add_argument('--path', '-p', default='.', help='本地项目路径')
    parser.add_argument('--message', '-m', help='提交信息')
    parser.add_argument('--create', '-c', action='store_true', help='创建新仓库')

    args = parser.parse_args()

    sync = GitHubSync(args.token, args.repo)

    if args.create:
        success, msg = sync.get_or_create_repo()
        if success:
            print(f"仓库已创建: {msg}")
        else:
            print(f"失败: {msg}")
            return

    success, msg = sync.push_to_github(args.path, args.message)
    if success:
        print(f"推送成功: {msg}")
    else:
        print(f"推送失败: {msg}")


if __name__ == "__main__":
    main()
