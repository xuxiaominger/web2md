"""
WebClipper 命令行入口
使用: python -m webclipper [命令]
"""

import sys
from .cli import main

if __name__ == '__main__':
    sys.exit(main())
