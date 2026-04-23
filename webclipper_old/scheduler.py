"""
定时任务调度器
"""

import json
import os
import uuid
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from .crawler import WebCrawler
from .searcher import get_search_engine
from .config import get_config


# 简单的Cron表达式解析
def parse_cron(cron_expr: str) -> Optional[timedelta]:
    """
    解析Cron表达式为时间间隔
    支持: 每隔N分钟, 每隔N小时, 每天, 每周
    """
    parts = cron_expr.strip().split()

    # 格式: */N * * * * (每N分钟)
    if len(parts) >= 2 and parts[0].startswith('*/'):
        try:
            minutes = int(parts[0][2:])
            return timedelta(minutes=minutes)
        except:
            pass

    # 格式: 0 */N * * * (每N小时)
    if len(parts) >= 3 and parts[1].startswith('*/'):
        try:
            hours = int(parts[1][2:])
            return timedelta(hours=hours)
        except:
            pass

    # 格式: 0 H * * * (每天 at hour H)
    if len(parts) >= 2:
        try:
            # 每天 at 指定小时
            if parts[1].isdigit():
                hour = int(parts[1])
                now = datetime.now()
                next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run - now
        except:
            pass

    # 默认: 每天 21:00
    return timedelta(days=1)


class Task:
    """定时任务"""

    def __init__(self, task_id: str, name: str, keywords: List[str], cron_expr: str,
                 enabled: bool = True, max_results: int = 5, interval_minutes: int = None):
        self.id = task_id
        self.name = name
        self.keywords = keywords
        self.cron_expr = cron_expr
        self.enabled = enabled
        self.max_results = max_results
        self.interval_minutes = interval_minutes
        self.created_at = datetime.now().isoformat()
        self.last_run = None
        self.next_run = None
        self.run_count = 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords,
            'cron_expr': self.cron_expr,
            'enabled': self.enabled,
            'max_results': self.max_results,
            'interval_minutes': self.interval_minutes,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'run_count': self.run_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        task = cls(
            data['id'],
            data['name'],
            data['keywords'],
            data['cron_expr'],
            data.get('enabled', True),
            data.get('max_results', 5),
            data.get('interval_minutes')
        )
        task.created_at = data.get('created_at')
        task.last_run = data.get('last_run')
        task.next_run = data.get('next_run')
        task.run_count = data.get('run_count', 0)
        return task


class TaskScheduler:
    """任务调度器"""

    def __init__(self, tasks_file: str = None):
        self.tasks_file = tasks_file or self._get_default_tasks_file()
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.thread = None
        self.load_tasks()

    def _get_default_tasks_file(self) -> str:
        """获取默认任务文件路径"""
        config_dir = Path.home() / ".webclipper"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "tasks.json")

    def load_tasks(self):
        """加载任务"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = Task.from_dict(task_data)
                        self.tasks[task.id] = task
            except Exception as e:
                print(f"加载任务失败: {e}")

    def save_tasks(self):
        """保存任务"""
        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
        data = {
            'tasks': [task.to_dict() for task in self.tasks.values()]
        }
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_task(self, name: str, keywords: List[str], cron_expr: str = None,
                 max_results: int = 5, interval_minutes: int = None) -> Task:
        """添加任务"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id, name, keywords, cron_expr or '0 21 * * *',
                    max_results=max_results, interval_minutes=interval_minutes)

        # 计算下次运行时间
        self._update_next_run(task)

        self.tasks[task_id] = task
        self.save_tasks()
        print(f"已添加任务: {name} (ID: {task_id})")
        print(f"  关键词: {keywords}")
        print(f"  Cron: {cron_expr}")
        print(f"  下次运行: {task.next_run}")
        return task

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._update_next_run(self.tasks[task_id])
            self.save_tasks()
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.save_tasks()
            return True
        return False

    def list_tasks(self) -> List[Task]:
        """列出所有任务"""
        return list(self.tasks.values())

    def _update_next_run(self, task: Task):
        """更新任务下次运行时间"""
        try:
            if task.interval_minutes:
                # 使用间隔分钟数
                delta = timedelta(minutes=task.interval_minutes)
                task.next_run = (datetime.now() + delta).strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 解析cron表达式
                delta = parse_cron(task.cron_expr)
                if delta:
                    task.next_run = (datetime.now() + delta).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    task.next_run = None
        except Exception as e:
            print(f"计算下次运行时间失败: {e}")
            task.next_run = None

    def run_task(self, task: Task):
        """执行任务"""
        print(f"\n=== 执行任务: {task.name} ===")

        config = get_config()
        obsidian_path = config.obsidian_path
        search_engine = config.search_engine

        crawler = WebCrawler(obsidian_path)
        se = get_search_engine(search_engine)

        try:
            for keyword in task.keywords:
                print(f"搜索关键词: {keyword}")
                results = se.search(keyword, task.max_results)

                if not results:
                    print(f"未找到结果: {keyword}")
                    continue

                print(f"找到 {len(results)} 个结果")

                for i, result in enumerate(results, 1):
                    print(f"[{i}] {result.get('title', 'untitled')}")
                    try:
                        crawler.crawl(result['url'])
                    except Exception as e:
                        print(f"  爬取失败: {e}")

            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            self._update_next_run(task)
            self.save_tasks()

        finally:
            crawler.close()

        print(f"=== 任务完成 ===\n")

    def start(self, interval: int = 60):
        """启动调度器"""
        if self.running:
            print("调度器已在运行")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, args=(interval,), daemon=True)
        self.thread.start()
        print(f"调度器已启动，每 {interval} 秒检查一次任务")

    def stop(self):
        """停止调度器"""
        self.running = False
        print("调度器已停止")

    def _run_loop(self, interval: int):
        """运行循环"""
        while self.running:
            try:
                now = datetime.now()
                for task in self.tasks.values():
                    if not task.enabled:
                        continue

                    if task.next_run:
                        try:
                            next_run = datetime.strptime(task.next_run, '%Y-%m-%d %H:%M:%S')
                            if now >= next_run:
                                self.run_task(task)
                        except:
                            pass
            except Exception as e:
                print(f"调度器错误: {e}")

            time.sleep(interval)


# 全局调度器实例
_scheduler = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
