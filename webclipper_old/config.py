"""
配置管理模块
"""

import os
import json
from pathlib import Path
from typing import Optional

DEFAULT_CONFIG = {
    "obsidian": {
        "vault_path": "/Users/xuxiaoming/Documents/我的笔记本/2025年10月2日至"
    },
    "search": {
        "engine": "baidu",
        "max_results": 10
    },
    "scheduler": {
        "enabled": True,
        "log_path": "./logs"
    },
    "crawler": {
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
}


class Config:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """获取默认配置路径"""
        config_dir = Path.home() / ".webclipper"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.json")

    def _load_config(self) -> dict:
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                return self._merge_config(DEFAULT_CONFIG, config)
            except Exception as e:
                print(f"加载配置失败: {e}, 使用默认配置")
        return DEFAULT_CONFIG.copy()

    def _merge_config(self, default: dict, custom: dict) -> dict:
        """合并配置"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    @property
    def obsidian_path(self) -> str:
        """获取Obsidian路径"""
        return self.get('obsidian.vault_path', DEFAULT_CONFIG['obsidian']['vault_path'])

    @property
    def search_engine(self) -> str:
        """获取搜索引擎"""
        return self.get('search.engine', 'baidu')

    @property
    def max_results(self) -> int:
        """获取最大结果数"""
        return self.get('search.max_results', 10)


# 全局配置实例
_config = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def init_config(config_path: str = None) -> Config:
    """初始化配置"""
    global _config
    _config = Config(config_path)
    return _config
