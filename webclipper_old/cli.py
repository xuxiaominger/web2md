"""
命令行界面
"""

import sys
import argparse
from pathlib import Path

from .crawler import crawl_url, crawl_urls
from .searcher import search, get_search_engine
from .scheduler import get_scheduler
from .config import get_config, init_config


def cmd_crawl(args):
    """爬取单个URL"""
    config = get_config()
    result = crawl_url(args.url, config.obsidian_path)

    if 'error' in result and result['error']:
        print(f"错误: {result['error']}")
        return 1

    if args.print:
        print("\n" + "=" * 50)
        print(result.get('markdown', ''))
        print("=" * 50)

    return 0


def cmd_search(args):
    """搜索并爬取"""
    config = get_config()

    print(f"正在搜索: {args.keyword}")
    results = search(args.keyword, args.engine, args.limit)

    if not results:
        print("未找到结果")
        return 1

    print(f"找到 {len(results)} 个结果:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        if r.get('snippet'):
            print(f"   {r['snippet'][:100]}...")
        print()

    if args.crawl:
        print("开始爬取...")
        urls = [r['url'] for r in results]
        crawl_urls(urls, config.obsidian_path)

    return 0


def cmd_schedule(args):
    """添加定时任务"""
    scheduler = get_scheduler()

    # 解析关键词
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    else:
        keywords = [args.keyword] if hasattr(args, 'keyword') and args.keyword else []

    if not keywords:
        print("错误: 请提供关键词")
        return 1

    # 解析间隔
    interval = None
    if args.interval:
        try:
            interval = int(args.interval)
        except:
            pass

    task = scheduler.add_task(
        name=args.name,
        keywords=keywords,
        cron_expr=args.cron,
        max_results=args.limit,
        interval_minutes=interval
    )

    if args.run_now:
        scheduler.run_task(task)

    return 0


def cmd_tasks(args):
    """任务管理"""
    scheduler = get_scheduler()

    if args.subcommand == 'list':
        task_list = scheduler.list_tasks()
        if not task_list:
            print("暂无任务")
            return 0

        print(f"{'ID':<10} {'名称':<20} {'关键词':<25} {'状态':<8} {'下次运行':<20}")
        print("-" * 90)
        for task in task_list:
            status = "启用" if task.enabled else "禁用"
            keywords = ', '.join(task.keywords[:2])
            if len(task.keywords) > 2:
                keywords += '...'
            print(f"{task.id:<10} {task.name:<20} {keywords:<25} {status:<8} {task.next_run or 'N/A':<20}")
        return 0

    elif args.subcommand == 'delete':
        if scheduler.delete_task(args.task_id):
            print(f"已删除任务: {args.task_id}")
            return 0
        else:
            print(f"任务不存在: {args.task_id}")
            return 1

    elif args.subcommand == 'enable':
        if scheduler.enable_task(args.task_id):
            print(f"已启用任务: {args.task_id}")
            return 0
        else:
            print(f"任务不存在: {args.task_id}")
            return 1

    elif args.subcommand == 'disable':
        if scheduler.disable_task(args.task_id):
            print(f"已禁用任务: {args.task_id}")
            return 0
        else:
            print(f"任务不存在: {args.task_id}")
            return 1

    elif args.subcommand == 'run':
        task_list = scheduler.list_tasks()
        task = next((t for t in task_list if t.id == args.task_id), None)
        if task:
            scheduler.run_task(task)
            return 0
        else:
            print(f"任务不存在: {args.task_id}")
            return 1


def cmd_daemon(args):
    """启动守护进程"""
    scheduler = get_scheduler()

    if args.action == 'start':
        scheduler.start(args.interval)
        print("按 Ctrl+C 停止")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
    elif args.action == 'stop':
        scheduler.stop()
    elif args.action == 'status':
        task_list = scheduler.list_tasks()
        enabled = sum(1 for t in task_list if t.enabled)
        print(f"调度器状态: {'运行中' if scheduler.running else '已停止'}")
        print(f"总任务数: {len(task_list)}, 启用: {enabled}")


def cmd_config(args):
    """配置管理"""
    config = get_config()

    if args.subcommand == 'show':
        print(f"Obsidian路径: {config.obsidian_path}")
        print(f"搜索引擎: {config.search_engine}")
        print(f"最大结果数: {config.max_results}")
    elif args.subcommand == 'set':
        if args.key and args.value:
            config.set(args.key, args.value)
            config.save()
            print(f"已设置 {args.key} = {args.value}")
        else:
            print("请提供 --key 和 --value")

    return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='WebClipper - 自动化网页爬取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  webclipper crawl https://example.com
  webclipper search "Python教程" --crawl
  webclipper schedule "科技新闻" --keywords "科技,新闻" --cron "0 21 * * *"
  webclipper tasks list
  webclipper daemon start
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取单个URL')
    crawl_parser.add_argument('url', help='要爬取的URL')
    crawl_parser.add_argument('--print', '-p', action='store_true', help='打印Markdown内容')

    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索并爬取')
    search_parser.add_argument('keyword', help='搜索关键词')
    search_parser.add_argument('--engine', '-e', default='baidu', choices=['baidu', 'bing', 'google'], help='搜索引擎')
    search_parser.add_argument('--limit', '-l', type=int, default=10, help='结果数量')
    search_parser.add_argument('--crawl', '-c', action='store_true', help='搜索后自动爬取')

    # schedule 命令
    schedule_parser = subparsers.add_parser('schedule', help='添加定时任务')
    schedule_parser.add_argument('name', help='任务名称')
    schedule_parser.add_argument('keyword', nargs='?', help='搜索关键词')
    schedule_parser.add_argument('--keywords', '-k', help='关键词，多个用逗号分隔')
    schedule_parser.add_argument('--cron', '-c', help='Cron表达式 (如 0 21 * * *)')
    schedule_parser.add_argument('--interval', '-i', type=int, help='间隔分钟数 (如 60 表示每小时)')
    schedule_parser.add_argument('--limit', '-l', type=int, default=5, help='每个关键词最多爬取数量')
    schedule_parser.add_argument('--run-now', '-r', action='store_true', help='立即执行一次')

    # tasks 命令
    tasks_parser = subparsers.add_subparsers(dest='subcommand', help='任务子命令')
    tasks_parser.add_parser('list', help='列出所有任务')
    tasks_parser.add_parser('delete', help='删除任务').add_argument('task_id', help='任务ID')
    tasks_parser.add_parser('enable', help='启用任务').add_argument('task_id', help='任务ID')
    tasks_parser.add_parser('disable', help='禁用任务').add_argument('task_id', help='任务ID')
    tasks_parser.add_parser('run', help='手动运行任务').add_argument('task_id', help='任务ID')

    # daemon 命令
    daemon_parser = subparsers.add_subparsers(dest='action', help='守护进程操作')
    daemon_parser.add_parser('start', help='启动守护进程')
    daemon_parser.add_parser('stop', help='停止守护进程')
    daemon_parser.add_parser('status', help='查看状态')

    # config 命令
    config_parser = subparsers.add_subparsers(dest='subcommand', help='配置子命令')
    config_parser.add_parser('show', help='显示配置')
    set_parser = config_parser.add_parser('set', help='设置配置')
    set_parser.add_argument('--key', help='配置键')
    set_parser.add_argument('--value', help='配置值')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # 初始化配置
    init_config()

    # 执行命令
    if args.command == 'crawl':
        return cmd_crawl(args)
    elif args.command == 'search':
        return cmd_search(args)
    elif args.command == 'schedule':
        return cmd_schedule(args)
    elif args.command == 'tasks':
        return cmd_tasks(args)
    elif args.command == 'daemon':
        return cmd_daemon(args)
    elif args.command == 'config':
        return cmd_config(args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
