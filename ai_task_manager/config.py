"""設定ファイル管理"""
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# デフォルト設定
DEFAULT_CONFIG = {
    'database': {
        'path': './data/tasks.db'
    },
    'display': {
        'default_category': None,
        'default_priority': 'medium',
        'date_format': '%Y-%m-%d',
        'timezone': 'Asia/Tokyo'
    },
    'gantt': {
        'default_width': 80,
        'default_range': 'current_month',
        'auto_open_browser': False,
        'html_output_dir': './output'
    },
    'dashboard': {
        'theme': 'light',
        'auto_refresh': False,
        'default_period': 'month'
    },
    'export': {
        'png_width': 1920,
        'png_height': 1080,
        'csv_encoding': 'utf-8-sig',
        'pdf_paper_size': 'A4'
    },
    'notifications': {
        'enabled': False,
        'deadline_warning_days': 3
    }
}


class Config:
    """設定クラス"""

    def __init__(self):
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self):
        """設定ファイルを読み込み"""
        if not HAS_YAML:
            return

        # 設定ファイルのパス（優先順位順）
        config_paths = [
            Path('./config.yaml'),                              # プロジェクトローカル
            Path.home() / '.ai-task-manager' / 'config.yaml'   # ユーザーグローバル
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        user_config = yaml.safe_load(f) or {}
                        self._merge_config(user_config)
                        break
                except Exception:
                    # 設定ファイルの読み込みエラーは無視（デフォルト値を使用）
                    pass

    def _merge_config(self, user_config: Dict[str, Any]):
        """ユーザー設定をデフォルト設定にマージ"""
        for key, value in user_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得

        Args:
            key: 設定キー（ドット区切り、例: 'database.path'）
            default: デフォルト値

        Returns:
            設定値
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """設定値を設定

        Args:
            key: 設定キー（ドット区切り）
            value: 設定値
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None):
        """設定をファイルに保存

        Args:
            path: 保存先パス（省略時は ~/.ai-task-manager/config.yaml）
        """
        if not HAS_YAML:
            raise ImportError("PyYAMLがインストールされていません。pip install pyyaml を実行してください。")

        if path is None:
            path = Path.home() / '.ai-task-manager' / 'config.yaml'
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)


# グローバル設定インスタンス
_config: Optional[Config] = None


def get_config() -> Config:
    """グローバル設定インスタンスを取得"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def init_config_file(path: Optional[str] = None) -> str:
    """設定ファイルを生成

    Args:
        path: 保存先パス（省略時は ~/.ai-task-manager/config.yaml）

    Returns:
        生成されたファイルの絶対パス
    """
    config = Config()  # デフォルト設定
    config.save(path)

    if path is None:
        path = Path.home() / '.ai-task-manager' / 'config.yaml'
    else:
        path = Path(path)

    return str(path.resolve())
