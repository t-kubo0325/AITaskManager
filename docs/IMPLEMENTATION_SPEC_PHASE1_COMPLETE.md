# AI Task Manager Phase 1 完全実装仕様書

**対象読者**: ローカルLLM、Claude Code、人間の実装者
**実装時間**: 6時間（タグ機能含む）
**最終更新**: 2026-01-16

---

## 📋 0. 前提条件

### 環境要件

```bash
Python: 3.8以上
OS: Linux / macOS / Windows / WSL
必須パッケージ:
  - click>=8.0.0
  - jinja2>=3.0.0
  - python-dateutil>=2.8.0
```

### Phase 1 で実装する機能

- ✅ データベース設計・初期化（タグテーブル含む）
- ✅ データモデル（Task, Tag クラス）
- ✅ 基本CLIコマンド（add, list, update, delete, tags）
- ✅ タグ機能（追加、削除、フィルタ）
- ✅ ツリー表示（タグ表示対応）
- ✅ ASCII ガントチャート

### Phase 1 で実装しない機能

- ❌ HTML ガントチャート（Phase 2）
- ❌ 統計ダッシュボード（Phase 3）
- ❌ JSON出力（Phase 2）
- ❌ 設定ファイル（Phase 3）
- ❌ 相対日付入力（「明日」「来週」など）（Phase 2）

---

## 📁 1. ディレクトリ構造

Phase 1 で作成するファイル一覧:

```
AITaskManager/
├── data/                           # データベース格納ディレクトリ
│   └── tasks.db                    # SQLiteデータベース（自動生成）
├── ai_task_manager/
│   ├── __init__.py                 # パッケージ初期化
│   ├── cli.py                      # CLIエントリーポイント
│   ├── database.py                 # データベース操作
│   ├── models.py                   # データモデル
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── add.py                  # タスク追加
│   │   ├── list.py                 # タスク一覧
│   │   ├── update.py               # タスク更新
│   │   ├── delete.py               # タスク削除
│   │   ├── tree.py                 # ツリー表示
│   │   ├── gantt.py                # ガントチャート
│   │   └── tags.py                 # タグ管理 ⭐
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── tree_view.py            # ツリー表示ロジック
│   │   └── ascii_gantt.py          # ASCIIガントチャート
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py           # 日付操作
│       └── errors.py               # エラーハンドリング ⭐
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_models.py
│   ├── test_tags.py                # タグ機能テスト ⭐
│   ├── test_tree_view.py
│   └── test_ascii_gantt.py
├── setup.py
├── MANIFEST.in                      # パッケージデータ定義 ⭐
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

---

## 🗄️ 2. データベース設計

### 2.1 テーブル定義

#### tasks テーブル

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
    parent_id INTEGER,
    start_date TEXT,  -- ISO 8601: YYYY-MM-DD
    due_date TEXT,    -- ISO 8601: YYYY-MM-DD
    completed_date TEXT,
    progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE RESTRICT  -- ⭐ RESTRICT に変更
);
```

#### tags テーブル ⭐

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### task_tags テーブル（多対多中間テーブル）⭐

```sql
CREATE TABLE task_tags (
    task_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

#### インデックス

```sql
CREATE INDEX idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_task_tags_task_id ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag_id ON task_tags(tag_id);
```

### 2.2 重要な設計判断

#### ON DELETE RESTRICT の採用 ⭐

```python
# 理由: 親タスク削除時に子タスクが勝手に消えるのを防ぐ
# 親タスク削除前に以下をチェック:
# 1. 子タスクが存在するか確認
# 2. 存在する場合はエラーメッセージを表示
# 3. ユーザーに「先に子タスクを削除してください」と案内
```

**実装例**:

```python
def delete_task(task_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 子タスクの存在チェック
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE parent_id = ?", (task_id,))
    child_count = cursor.fetchone()[0]

    if child_count > 0:
        click.echo(f"❌ エラー: このタスクには {child_count} 件の子タスクがあります")
        click.echo("先に子タスクを削除してください")
        conn.close()
        sys.exit(1)

    # 削除実行
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
```

#### progress の扱い

**Phase 1 の仕様**:
- **手動更新のみ**（自動計算は Phase 3 で検討）
- ユーザーが `--progress` オプションで明示的に指定
- デフォルト値: 0
- status が `completed` になっても自動で 100 にはならない（ユーザーが手動で設定）

---

## 🔧 3. 実装手順（厳密な順序）

### ステップ0: プロジェクト初期化（15分）

#### 3.0.1 ディレクトリ作成

```bash
mkdir -p ai_task_manager/{commands,visualization,utils}
mkdir -p tests
mkdir -p data
touch ai_task_manager/__init__.py
touch ai_task_manager/commands/__init__.py
touch ai_task_manager/visualization/__init__.py
touch ai_task_manager/utils/__init__.py
touch tests/__init__.py
```

#### 3.0.2 requirements.txt

```text
click>=8.0.0
jinja2>=3.0.0
python-dateutil>=2.8.0
```

#### 3.0.3 requirements-dev.txt

```text
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
```

#### 3.0.4 .gitignore

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
data/tasks.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

#### 3.0.5 動作確認

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

### ステップ1: エラーハンドリング基盤（30分）

#### 3.1.1 `ai_task_manager/utils/errors.py`

```python
"""エラーハンドリング共通モジュール"""
import sys
import click


class TaskManagerError(Exception):
    """AI Task Manager 基底例外クラス"""
    pass


class TaskNotFoundError(TaskManagerError):
    """タスクが見つからない"""
    pass


class InvalidDateFormatError(TaskManagerError):
    """日付フォーマットが不正"""
    pass


class ParentTaskNotFoundError(TaskManagerError):
    """親タスクが存在しない"""
    pass


class TaskHasChildrenError(TaskManagerError):
    """タスクに子タスクが存在する"""
    pass


class DatabaseError(TaskManagerError):
    """データベースエラー"""
    pass


def handle_error(error: Exception, exit_code: int = 1):
    """
    エラーを処理してユーザーに表示

    Args:
        error: 例外オブジェクト
        exit_code: 終了コード
    """
    if isinstance(error, TaskNotFoundError):
        click.echo(f"❌ エラー: {error}", err=True)
    elif isinstance(error, InvalidDateFormatError):
        click.echo(f"❌ エラー: {error}", err=True)
        click.echo("💡 日付は YYYY-MM-DD 形式で指定してください（例: 2025-01-31）", err=True)
    elif isinstance(error, ParentTaskNotFoundError):
        click.echo(f"❌ エラー: {error}", err=True)
    elif isinstance(error, TaskHasChildrenError):
        click.echo(f"❌ エラー: {error}", err=True)
        click.echo("💡 先に子タスクを削除してください", err=True)
    elif isinstance(error, DatabaseError):
        click.echo(f"❌ データベースエラー: {error}", err=True)
    else:
        click.echo(f"❌ 予期しないエラー: {error}", err=True)

    sys.exit(exit_code)
```

#### 3.1.2 動作確認

```bash
python -c "from ai_task_manager.utils.errors import TaskNotFoundError, handle_error; handle_error(TaskNotFoundError('タスクID 999 が見つかりません'))"
# 期待される出力:
# ❌ エラー: タスクID 999 が見つかりません
# (プロセス終了コード: 1)
```

---

### ステップ2: データベース層（30分）

#### 3.2.1 `ai_task_manager/database.py`

```python
"""データベース操作モジュール"""
import sqlite3
from pathlib import Path
from ai_task_manager.utils.errors import DatabaseError

# データベースパス
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


def get_connection() -> sqlite3.Connection:
    """データベース接続を取得"""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約を有効化
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"データベース接続に失敗しました: {e}")


def init_db():
    """データベースを初期化"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # tasks テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
                parent_id INTEGER,
                start_date TEXT,
                due_date TEXT,
                completed_date TEXT,
                progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE RESTRICT
            )
        """)

        # tags テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # task_tags テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # インデックス
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_tags_task_id ON task_tags(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_tags_tag_id ON task_tags(tag_id)")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"データベース初期化に失敗しました: {e}")
    finally:
        conn.close()


def get_or_create_tag(tag_name: str) -> int:
    """
    タグを取得または作成

    Args:
        tag_name: タグ名

    Returns:
        タグID
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 既存タグを検索
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        row = cursor.fetchone()

        if row:
            return row[0]

        # 新規作成
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの取得/作成に失敗しました: {e}")
    finally:
        conn.close()


def add_tags_to_task(task_id: int, tag_names: list[str]):
    """
    タスクにタグを追加

    Args:
        task_id: タスクID
        tag_names: タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for tag_name in tag_names:
            tag_id = get_or_create_tag(tag_name)
            cursor.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id)
            )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの追加に失敗しました: {e}")
    finally:
        conn.close()


def remove_tags_from_task(task_id: int, tag_names: list[str]):
    """
    タスクからタグを削除

    Args:
        task_id: タスクID
        tag_names: タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for tag_name in tag_names:
            cursor.execute("""
                DELETE FROM task_tags
                WHERE task_id = ? AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """, (task_id, tag_name))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの削除に失敗しました: {e}")
    finally:
        conn.close()


def get_task_tags(task_id: int) -> list[str]:
    """
    タスクのタグ一覧を取得

    Args:
        task_id: タスクID

    Returns:
        タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
            ORDER BY t.name
        """, (task_id,))
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise DatabaseError(f"タグの取得に失敗しました: {e}")
    finally:
        conn.close()
```

#### 3.2.2 動作確認

```bash
python -c "from ai_task_manager.database import init_db; init_db(); print('✅ データベース初期化成功')"
# 期待される出力:
# ✅ データベース初期化成功

# データベースファイルの確認
ls -lh data/tasks.db
# 期待される出力:
# -rw-r--r-- 1 user user 8.0K Jan 16 12:00 data/tasks.db

# スキーマ確認
sqlite3 data/tasks.db ".schema tasks"
# 期待される出力: tasks テーブルのDDL
```

---

### ステップ3: データモデル層（30分）

#### 3.3.1 `ai_task_manager/utils/date_utils.py`

```python
"""日付操作ユーティリティ"""
from datetime import date, datetime
from typing import Optional
from ai_task_manager.utils.errors import InvalidDateFormatError


def parse_date(date_str: str) -> date:
    """
    文字列を日付オブジェクトに変換

    Args:
        date_str: 日付文字列（YYYY-MM-DD）

    Returns:
        date オブジェクト

    Raises:
        InvalidDateFormatError: フォーマットが不正な場合
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise InvalidDateFormatError(
            f"日付フォーマットが不正です: {date_str}"
        )


def format_date(d: date) -> str:
    """日付を文字列に変換"""
    return d.strftime('%Y-%m-%d')


def parse_date_optional(date_str: Optional[str]) -> Optional[date]:
    """オプショナルな日付文字列をパース"""
    if date_str is None:
        return None
    return parse_date(date_str)
```

#### 3.3.2 `ai_task_manager/models.py`

```python
"""データモデル"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from ai_task_manager.utils.date_utils import parse_date_optional


@dataclass
class Task:
    """タスクモデル"""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = 'medium'
    status: str = 'pending'
    parent_id: Optional[int] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    progress: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)

    @property
    def is_overdue(self) -> bool:
        """期限切れかどうかを判定"""
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return self.due_date < date.today()
        return False

    @classmethod
    def from_db_row(cls, row: tuple, tags: list[str] = None) -> 'Task':
        """
        データベース行からTaskオブジェクトを生成

        Args:
            row: データベース行（タプル）
            tags: タグのリスト（オプション）

        Returns:
            Task オブジェクト
        """
        return cls(
            id=row[0],
            title=row[1],
            description=row[2],
            category=row[3],
            priority=row[4] or 'medium',
            status=row[5] or 'pending',
            parent_id=row[6],
            start_date=parse_date_optional(row[7]),
            due_date=parse_date_optional(row[8]),
            completed_date=parse_date_optional(row[9]),
            progress=row[10] or 0,
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
            tags=tags or []
        )


@dataclass
class Tag:
    """タグモデル"""
    id: int
    name: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Tag':
        """データベース行からTagオブジェクトを生成"""
        return cls(
            id=row[0],
            name=row[1],
            created_at=datetime.fromisoformat(row[2]) if row[2] else None
        )
```

#### 3.3.3 動作確認

```python
# test_models.py（簡易テスト）
from datetime import date
from ai_task_manager.models import Task, Tag

# Taskの作成
task = Task(
    id=1,
    title="テストタスク",
    priority="high",
    status="in_progress",
    due_date=date(2025, 1, 31),
    tags=["urgent", "test"]
)

print(f"✅ Task作成成功: {task.title}")
print(f"   期限切れ: {task.is_overdue}")
print(f"   タグ: {', '.join(task.tags)}")

# Tagの作成
tag = Tag(id=1, name="urgent")
print(f"✅ Tag作成成功: {tag.name}")
```

---

### ステップ4: 基本CLIコマンド（2時間）

#### 3.4.1 `ai_task_manager/cli.py`

```python
"""CLIエントリーポイント"""
import click
from ai_task_manager.database import init_db


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """AI Task Manager - Claude Code対応タスク管理ツール"""
    init_db()


@cli.command()
@click.argument('title')
@click.option('--description', '-d', help='タスクの説明')
@click.option('--category', '-c', help='カテゴリ')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), default='medium', help='優先度')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--parent', type=int, help='親タスクID')
@click.option('--tags', help='タグ（カンマ区切り）')
def add(title, description, category, priority, start, due, parent, tags):
    """新しいタスクを追加"""
    from ai_task_manager.commands.add import add_task
    add_task(title, description, category, priority, start, due, parent, tags)


@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
@click.option('--tags', help='タグでフィルタ（カンマ区切り）')
def list(category, status, priority, tags):
    """タスク一覧を表示"""
    from ai_task_manager.commands.list import list_tasks
    list_tasks(category, status, priority, tags)


@cli.command()
@click.argument('task_id', type=int)
@click.option('--title', help='タスク名')
@click.option('--description', '-d', help='説明')
@click.option('--category', '-c', help='カテゴリ')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), help='優先度')
@click.option('--status', '-s', type=click.Choice(['pending', 'in_progress', 'completed', 'cancelled']), help='ステータス')
@click.option('--progress', type=int, help='進捗率 (0-100)')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--add-tags', help='追加するタグ（カンマ区切り）')
@click.option('--remove-tags', help='削除するタグ（カンマ区切り）')
def update(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags):
    """タスクを更新"""
    from ai_task_manager.commands.update import update_task
    update_task(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags)


@cli.command()
@click.argument('task_id', type=int)
@click.option('--force', '-f', is_flag=True, help='確認なしで削除')
def delete(task_id, force):
    """タスクを削除"""
    from ai_task_manager.commands.delete import delete_task
    delete_task(task_id, force)


@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--tags', help='タグでフィルタ（カンマ区切り）')
def tree(category, status, tags):
    """タスクをツリー形式で表示"""
    from ai_task_manager.commands.tree import tree_command
    tree_command(category, status, tags)


@cli.command()
@click.option('--range', 'range_str', help='表示範囲 (YYYY-MM)')
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
@click.option('--width', default=80, help='チャート幅')
def gantt(range_str, category, status, priority, width):
    """ASCIIガントチャートを表示"""
    from ai_task_manager.commands.gantt import gantt_command
    gantt_command(range_str, category, status, priority, width)


@cli.command()
def tags():
    """タグ一覧を表示"""
    from ai_task_manager.commands.tags import tags_command
    tags_command()


if __name__ == '__main__':
    cli()
```

#### 3.4.2 `ai_task_manager/commands/add.py`

```python
"""タスク追加コマンド"""
import click
from ai_task_manager.database import get_connection, add_tags_to_task
from ai_task_manager.utils.errors import (
    handle_error,
    InvalidDateFormatError,
    ParentTaskNotFoundError,
    DatabaseError
)
from ai_task_manager.utils.date_utils import parse_date_optional


def add_task(title, description, category, priority, start, due, parent, tags):
    """タスクを追加"""
    try:
        # 日付のパース
        start_date = parse_date_optional(start)
        due_date = parse_date_optional(due)

        conn = get_connection()
        cursor = conn.cursor()

        # 親タスクの存在確認
        if parent:
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (parent,))
            if not cursor.fetchone():
                raise ParentTaskNotFoundError(f"親タスクID {parent} が見つかりません")

        # タスク追加
        cursor.execute("""
            INSERT INTO tasks (title, description, category, priority, start_date, due_date, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            category,
            priority,
            start_date.isoformat() if start_date else None,
            due_date.isoformat() if due_date else None,
            parent
        ))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # タグの追加
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            add_tags_to_task(task_id, tag_list)

        click.echo(f"✅ タスクを追加しました (ID: {task_id})")

    except (InvalidDateFormatError, ParentTaskNotFoundError, DatabaseError) as e:
        handle_error(e)
```

#### 3.4.3 `ai_task_manager/commands/list.py`

```python
"""タスク一覧コマンド"""
import click
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.utils.errors import handle_error, DatabaseError


def list_tasks(category, status, priority, tags):
    """タスク一覧を表示"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        # タグフィルタ
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            placeholders = ','.join('?' * len(tag_list))
            query += f"""
                AND id IN (
                    SELECT tt.task_id FROM task_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                    GROUP BY tt.task_id
                    HAVING COUNT(DISTINCT t.name) = ?
                )
            """
            params.extend(tag_list)
            params.append(len(tag_list))

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("📭 タスクが見つかりません")
            return

        # タスクの表示
        click.echo(f"\n📋 タスク一覧 ({len(rows)} 件)\n")
        click.echo("=" * 80)

        for row in rows:
            task_tags = get_task_tags(row[0])
            task = Task.from_db_row(row, task_tags)

            # 優先度マーク
            priority_mark = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}
            status_mark = {
                'pending': '[未着手]',
                'in_progress': '[進行中]',
                'completed': '[完了]',
                'cancelled': '[中止]'
            }

            # タグ表示
            tags_str = f" 🏷️  {', '.join(task.tags)}" if task.tags else ""

            click.echo(f"ID: {task.id} | {priority_mark.get(task.priority)} {task.title}")
            click.echo(f"  ステータス: {status_mark.get(task.status)} | 進捗: {task.progress}%")
            if task.category:
                click.echo(f"  カテゴリ: {task.category}")
            if task.start_date and task.due_date:
                click.echo(f"  期間: {task.start_date} 〜 {task.due_date}")
            elif task.due_date:
                click.echo(f"  期限: {task.due_date}")
            if tags_str:
                click.echo(f"  {tags_str}")
            click.echo("-" * 80)

    except DatabaseError as e:
        handle_error(e)
```

#### 3.4.4 `ai_task_manager/commands/update.py`

```python
"""タスク更新コマンド"""
import click
from ai_task_manager.database import (
    get_connection,
    add_tags_to_task,
    remove_tags_from_task
)
from ai_task_manager.utils.errors import (
    handle_error,
    TaskNotFoundError,
    InvalidDateFormatError,
    DatabaseError
)
from ai_task_manager.utils.date_utils import parse_date_optional


def update_task(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags):
    """タスクを更新"""
    try:
        # 日付のパース
        start_date = parse_date_optional(start)
        due_date = parse_date_optional(due)

        conn = get_connection()
        cursor = conn.cursor()

        # タスクの存在確認
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise TaskNotFoundError(f"タスクID {task_id} が見つかりません")

        # 更新クエリを構築
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if category is not None:
            updates.append("category = ?")
            params.append(category)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if progress is not None:
            if not (0 <= progress <= 100):
                raise ValueError("進捗率は 0〜100 の範囲で指定してください")
            updates.append("progress = ?")
            params.append(progress)

        if start_date is not None:
            updates.append("start_date = ?")
            params.append(start_date.isoformat())

        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat())

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)

            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

        conn.close()

        # タグの追加
        if add_tags:
            tag_list = [t.strip() for t in add_tags.split(',')]
            add_tags_to_task(task_id, tag_list)

        # タグの削除
        if remove_tags:
            tag_list = [t.strip() for t in remove_tags.split(',')]
            remove_tags_from_task(task_id, tag_list)

        click.echo(f"✅ タスク {task_id} を更新しました")

    except (TaskNotFoundError, InvalidDateFormatError, DatabaseError, ValueError) as e:
        handle_error(e)
```

#### 3.4.5 `ai_task_manager/commands/delete.py`

```python
"""タスク削除コマンド"""
import click
from ai_task_manager.database import get_connection
from ai_task_manager.utils.errors import (
    handle_error,
    TaskNotFoundError,
    TaskHasChildrenError,
    DatabaseError
)


def delete_task(task_id, force):
    """タスクを削除"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # タスクの存在確認
        cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise TaskNotFoundError(f"タスクID {task_id} が見つかりません")

        task_title = row[0]

        # 子タスクの存在確認
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE parent_id = ?", (task_id,))
        child_count = cursor.fetchone()[0]

        if child_count > 0:
            raise TaskHasChildrenError(
                f"タスク '{task_title}' には {child_count} 件の子タスクがあります"
            )

        # 削除確認
        if not force:
            if not click.confirm(f"タスク '{task_title}' を削除しますか？"):
                click.echo("❌ キャンセルしました")
                conn.close()
                return

        # 削除実行
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

        click.echo(f"✅ タスク '{task_title}' を削除しました")

    except (TaskNotFoundError, TaskHasChildrenError, DatabaseError) as e:
        handle_error(e)
```

#### 3.4.6 `ai_task_manager/commands/tags.py`

```python
"""タグ管理コマンド"""
import click
from ai_task_manager.database import get_connection
from ai_task_manager.utils.errors import handle_error, DatabaseError


def tags_command():
    """タグ一覧を表示"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # タグ一覧を取得（使用回数付き）
        cursor.execute("""
            SELECT t.name, COUNT(tt.task_id) as count
            FROM tags t
            LEFT JOIN task_tags tt ON t.id = tt.tag_id
            GROUP BY t.id, t.name
            ORDER BY count DESC, t.name
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("🏷️  タグがありません")
            return

        click.echo(f"\n🏷️  タグ一覧 ({len(rows)} 件)\n")
        click.echo("=" * 50)

        for name, count in rows:
            click.echo(f"{name:30} ({count} 件のタスク)")

        click.echo("=" * 50)

    except DatabaseError as e:
        handle_error(e)
```

#### 3.4.7 動作確認

```bash
# タスク追加
ai-task-manager add "テストタスク" --category "Test" --priority high --tags "urgent,test"
# 期待される出力: ✅ タスクを追加しました (ID: 1)

# タスク一覧
ai-task-manager list
# 期待される出力: タスク一覧の表示

# タスク更新
ai-task-manager update 1 --status in_progress --progress 50
# 期待される出力: ✅ タスク 1 を更新しました

# タグ一覧
ai-task-manager tags
# 期待される出力: タグ一覧の表示

# タスク削除（確認あり）
ai-task-manager delete 1
# 期待される出力: 削除確認 → ✅ タスク 'テストタスク' を削除しました
```

---

### ステップ5: ツリー表示（1.5時間）

#### 3.5.1 `ai_task_manager/visualization/tree_view.py`

```python
"""ツリー表示ロジック"""
from typing import List, Optional
from ai_task_manager.models import Task


def generate_tree_view(tasks: List[Task], parent_id: Optional[int] = None,
                       indent: str = '', is_last: bool = True) -> str:
    """
    タスクツリーを生成

    Args:
        tasks: 全タスクのリスト
        parent_id: 親タスクID（Noneはルート）
        indent: 現在のインデント文字列
        is_last: 最後の子要素かどうか

    Returns:
        ツリー表示の文字列
    """
    output = []
    child_tasks = [t for t in tasks if t.parent_id == parent_id]

    for i, task in enumerate(child_tasks):
        is_last_child = (i == len(child_tasks) - 1)
        prefix = '└─ ' if is_last_child else '├─ '

        task_line = format_task_line(task)
        output.append(f"{indent}{prefix}{task_line}")

        new_indent = indent + ('   ' if is_last_child else '│  ')
        child_output = generate_tree_view(tasks, task.id, new_indent, is_last_child)
        if child_output:
            output.append(child_output)

    return '\n'.join(output)


def format_task_line(task: Task) -> str:
    """
    タスクを1行で表示

    Args:
        task: タスクオブジェクト

    Returns:
        フォーマットされた文字列
    """
    # 優先度
    priority_map = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}
    priority_mark = priority_map.get(task.priority, '[中]')

    # ステータス
    status_map = {
        'pending': '[未着手]',
        'in_progress': '[進行中]',
        'completed': '[完了]',
        'cancelled': '[中止]'
    }
    status_mark = status_map.get(task.status, '')

    # 基本情報
    parts = [priority_mark, task.title]

    # 日付
    if task.start_date and task.due_date:
        parts.append(f"({task.start_date} - {task.due_date})")
    elif task.due_date:
        parts.append(f"({task.due_date})")

    # ステータス
    parts.append(status_mark)

    # 進捗率
    if task.status in ('in_progress', 'completed') and task.progress > 0:
        parts.append(f"{task.progress}%")

    # タグ
    if task.tags:
        parts.append(f"🏷️  {', '.join(task.tags)}")

    return ' '.join(p for p in parts if p)


def generate_statistics(tasks: List[Task]) -> str:
    """
    統計情報を生成

    Args:
        tasks: タスクのリスト

    Returns:
        統計情報の文字列
    """
    total = len(tasks)
    if total == 0:
        return ""

    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    pending = sum(1 for t in tasks if t.status == 'pending')

    output = [
        "\n統計:",
        f"  総タスク数: {total}",
        f"  完了: {completed} ({completed/total*100:.1f}%)",
        f"  進行中: {in_progress} ({in_progress/total*100:.1f}%)",
        f"  未着手: {pending} ({pending/total*100:.1f}%)"
    ]

    return '\n'.join(output)
```

#### 3.5.2 `ai_task_manager/commands/tree.py`

```python
"""ツリー表示コマンド"""
import click
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view, generate_statistics
from ai_task_manager.utils.errors import handle_error, DatabaseError


def tree_command(category, status, tags):
    """ツリー表示"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        # タグフィルタ
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            placeholders = ','.join('?' * len(tag_list))
            query += f"""
                AND id IN (
                    SELECT tt.task_id FROM task_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                )
            """
            params.extend(tag_list)

        query += " ORDER BY created_at"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("📭 タスクが見つかりません")
            return

        # タスクオブジェクトに変換（タグ付き）
        tasks = []
        for row in rows:
            task_tags = get_task_tags(row[0])
            tasks.append(Task.from_db_row(row, task_tags))

        # ツリー表示
        click.echo("\n📁 すべてのタスク\n")
        tree = generate_tree_view(tasks)
        if tree:
            click.echo(tree)

        # 統計情報
        stats = generate_statistics(tasks)
        if stats:
            click.echo(stats)

    except DatabaseError as e:
        handle_error(e)
```

#### 3.5.3 動作確認

```bash
# テストデータ作成
ai-task-manager add "プロジェクトA" --category Work --priority high --start 2025-01-10 --due 2025-02-28 --tags "project,important"
ai-task-manager add "要件定義" --parent 1 --start 2025-01-10 --due 2025-01-15 --tags "planning"
ai-task-manager add "設計" --parent 1 --start 2025-01-16 --due 2025-01-25 --tags "planning"
ai-task-manager add "実装" --parent 1 --start 2025-01-26 --due 2025-02-15 --tags "coding"

# ツリー表示
ai-task-manager tree

# 期待される出力:
# 📁 すべてのタスク
#
# └─ [高] プロジェクトA (2025-01-10 - 2025-02-28) [未着手] 🏷️  project, important
#    ├─ [中] 要件定義 (2025-01-10 - 2025-01-15) [未着手] 🏷️  planning
#    ├─ [中] 設計 (2025-01-16 - 2025-01-25) [未着手] 🏷️  planning
#    └─ [中] 実装 (2025-01-26 - 2025-02-15) [未着手] 🏷️  coding
#
# 統計:
#   総タスク数: 4
#   完了: 0 (0.0%)
#   進行中: 0 (0.0%)
#   未着手: 4 (100.0%)
```

---

### ステップ6: ASCII ガントチャート（2時間）

#### 3.6.1 `ai_task_manager/visualization/ascii_gantt.py`

```python
"""ASCIIガントチャート生成"""
from datetime import date, timedelta
from typing import List
from ai_task_manager.models import Task


def generate_ascii_gantt(tasks: List[Task], start_date: date, end_date: date, width: int = 80) -> str:
    """
    ASCII ガントチャートを生成

    Args:
        tasks: 表示するタスクのリスト
        start_date: 表示開始日
        end_date: 表示終了日
        width: チャート全体の幅

    Returns:
        ガントチャートの文字列
    """
    # ガントチャート表示可能なタスクのみフィルタ
    valid_tasks = [t for t in tasks if t.start_date and t.due_date]

    if not valid_tasks:
        return "⚠️  開始日と期限の両方が設定されているタスクがありません"

    name_col_width = 30
    chart_width = width - name_col_width - 10

    output = []
    output.append(f"タスクガントチャート: {start_date.strftime('%Y年%m月')}")
    output.append('━' * width)

    # タイムラインヘッダー
    timeline_header = generate_timeline_header(start_date, end_date, name_col_width, chart_width)
    output.append(timeline_header)
    output.append('━' * width)

    # 各タスクのバー
    for task in valid_tasks:
        task_line = generate_task_bar(task, start_date, end_date, name_col_width, chart_width)
        output.append(task_line)

    output.append('━' * width)
    output.append(generate_legend())
    output.append(generate_statistics_gantt(valid_tasks, start_date, end_date))

    return '\n'.join(output)


def generate_timeline_header(start_date: date, end_date: date, name_width: int, chart_width: int) -> str:
    """タイムライン目盛りヘッダーを生成"""
    total_days = (end_date - start_date).days + 1
    timeline = [' '] * chart_width

    # 5日単位で目盛りを配置
    for i in range(0, total_days, 5):
        current_date = start_date + timedelta(days=i)
        position = int((i / total_days) * chart_width)
        if position < chart_width - 2:
            day_str = str(current_date.day).rjust(2)
            if position + 1 < chart_width:
                timeline[position] = day_str[0]
                timeline[position + 1] = day_str[1]

    timeline_str = ''.join(timeline)
    return f"{'ID':<3} | {'タスク名':<{name_width}} | {timeline_str}"


def generate_task_bar(task: Task, start_date: date, end_date: date, name_width: int, chart_width: int) -> str:
    """個別タスクのバーを生成"""
    bar = [' '] * chart_width

    if task.start_date and task.due_date:
        total_days = (end_date - start_date).days + 1
        task_start_offset = max(0, (task.start_date - start_date).days)
        task_end_offset = min(total_days, (task.due_date - start_date).days + 1)

        start_pos = int((task_start_offset / total_days) * chart_width)
        end_pos = int((task_end_offset / total_days) * chart_width)

        # バーの記号を決定
        bar_char = get_bar_character(task)

        for i in range(start_pos, min(end_pos, chart_width)):
            bar[i] = bar_char

        # 現在位置を表示
        today_offset = (date.today() - start_date).days
        if 0 <= today_offset < total_days:
            today_pos = int((today_offset / total_days) * chart_width)
            if start_pos <= today_pos < end_pos:
                bar[today_pos] = '>'

    bar_str = ''.join(bar)
    task_name = task.title[:name_width]
    return f"{task.id:<3} | {task_name:<{name_width}} | [{bar_str}]"


def get_bar_character(task: Task) -> str:
    """タスクのステータスに応じたバー文字を返す"""
    if task.status == 'completed':
        return '✓'
    elif task.is_overdue:
        return '!'
    elif task.status == 'in_progress':
        return '='
    else:  # pending
        return '-'


def generate_legend() -> str:
    """凡例を生成"""
    return """
凡例:
  [=] タスク期間（進行中）  [✓] 完了  [!] 期限超過  [-] 未着手  [>] 本日
"""


def generate_statistics_gantt(tasks: List[Task], start_date: date, end_date: date) -> str:
    """統計情報を生成"""
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')

    return f"""
統計:
  期間: {start_date} - {end_date}
  総タスク数: {total}
  完了: {completed} ({completed/total*100:.1f}%)
"""
```

#### 3.6.2 `ai_task_manager/commands/gantt.py`

```python
"""ガントチャートコマンド"""
import click
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.visualization.ascii_gantt import generate_ascii_gantt
from ai_task_manager.utils.errors import handle_error, DatabaseError, InvalidDateFormatError


def gantt_command(range_str, category, status, priority, width):
    """ASCIIガントチャート表示"""
    try:
        # 日付範囲の解析
        start_date, end_date = parse_date_range(range_str)

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM tasks
            WHERE start_date IS NOT NULL
            AND due_date IS NOT NULL
            AND due_date >= ?
            AND start_date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY start_date, id"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("⚠️  表示するタスクがありません")
            return

        # タスクオブジェクトに変換（タグ付き）
        tasks = []
        for row in rows:
            task_tags = get_task_tags(row[0])
            tasks.append(Task.from_db_row(row, task_tags))

        # ガントチャート生成
        gantt_chart = generate_ascii_gantt(tasks, start_date, end_date, width)
        click.echo(gantt_chart)

    except (DatabaseError, InvalidDateFormatError) as e:
        handle_error(e)


def parse_date_range(range_str):
    """
    日付範囲文字列を解析

    Args:
        range_str: 範囲文字列（YYYY-MM または YYYY-MM-DD:YYYY-MM-DD）

    Returns:
        (start_date, end_date) のタプル
    """
    try:
        if not range_str:
            # デフォルト: 今月
            today = date.today()
            start = date(today.year, today.month, 1)
            end = start + relativedelta(months=1, days=-1)
            return start, end

        if ':' in range_str:
            # 範囲指定: YYYY-MM-DD:YYYY-MM-DD
            start_str, end_str = range_str.split(':')
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start, end

        # 月指定: YYYY-MM
        year_month = datetime.strptime(range_str, '%Y-%m')
        start = date(year_month.year, year_month.month, 1)
        end = start + relativedelta(months=1, days=-1)
        return start, end

    except ValueError as e:
        raise InvalidDateFormatError(f"日付範囲のフォーマットが不正です: {range_str}")
```

#### 3.6.3 動作確認

```bash
# 1月のガントチャート
ai-task-manager gantt --range 2025-01

# 期待される出力:
# タスクガントチャート: 2025年1月
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ID  | タスク名                         | 10   15   20   25   30
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1   | プロジェクトA                    | [=============================>     ]
# 2   | 要件定義                         | [====>                              ]
# 3   | 設計                             |       [========>                    ]
# 4   | 実装                             |                [============>       ]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 凡例:
#   [=] タスク期間（進行中）  [✓] 完了  [!] 期限超過  [-] 未着手  [>] 本日
#
# 統計:
#   期間: 2025-01-01 - 2025-01-31
#   総タスク数: 4
#   完了: 0 (0.0%)
```

---

### ステップ7: パッケージング（30分）

#### 3.7.1 `setup.py`

```python
"""Setup configuration"""
from setuptools import setup, find_packages
from pathlib import Path

# README読み込み
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text(encoding='utf-8') if readme.exists() else ""

setup(
    name='ai-task-manager',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'ai_task_manager': [
            'visualization/templates/*.html',
        ],
    },
    install_requires=[
        'click>=8.0.0',
        'jinja2>=3.0.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'ai-task-manager=ai_task_manager.cli:cli',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='Claude Code対応タスク管理ツール',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/t-kubo0325/AITaskManager',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
)
```

#### 3.7.2 `MANIFEST.in`

```text
include README.md
include requirements.txt
include requirements-dev.txt
recursive-include ai_task_manager/visualization/templates *.html
```

#### 3.7.3 インストールと動作確認

```bash
# 開発モードでインストール
pip install -e .

# バージョン確認
ai-task-manager --version
# 期待される出力: ai-task-manager, version 0.1.0

# ヘルプ表示
ai-task-manager --help
# 期待される出力: コマンド一覧
```

---

## ✅ 4. Phase 1 完了チェックリスト

実装後に以下を確認してください:

### データベース
- [ ] `data/tasks.db` が作成される
- [ ] tasks, tags, task_tags テーブルが存在
- [ ] 外部キー制約が有効（`PRAGMA foreign_keys = ON`）

### データモデル
- [ ] Task クラスが正常に動作
- [ ] Tag クラスが正常に動作
- [ ] `Task.is_overdue` プロパティが正しく判定

### CLIコマンド
- [ ] `add` コマンドでタスク追加（タグ対応）
- [ ] `list` コマンドでフィルタ（タグ対応）
- [ ] `update` コマンドで更新（タグ追加/削除対応）
- [ ] `delete` コマンドで削除（子タスクチェック）
- [ ] `tree` コマンドでツリー表示（タグ表示）
- [ ] `gantt` コマンドでガントチャート
- [ ] `tags` コマンドでタグ一覧

### エラーハンドリング
- [ ] 存在しないタスクIDで適切なエラー
- [ ] 不正な日付フォーマットでエラー
- [ ] 子タスクがある親を削除しようとしたらエラー
- [ ] 日本語エラーメッセージが表示される

### 視覚化
- [ ] ツリー表示が正しく階層を表現
- [ ] ガントチャートがバーを正しく描画
- [ ] 統計情報が正確に計算される

---

## 🧪 5. テスト

### 5.1 基本的なテストシナリオ

```bash
# 1. タスク追加
ai-task-manager add "親タスク" --category Work --priority high --start 2025-01-10 --due 2025-02-28 --tags "project,urgent"
ai-task-manager add "子タスク1" --parent 1 --start 2025-01-10 --due 2025-01-20 --tags "phase1"
ai-task-manager add "子タスク2" --parent 1 --start 2025-01-21 --due 2025-02-10 --tags "phase2"

# 2. 一覧表示
ai-task-manager list

# 3. タグフィルタ
ai-task-manager list --tags "urgent"

# 4. ツリー表示
ai-task-manager tree

# 5. 進捗更新
ai-task-manager update 2 --status in_progress --progress 50

# 6. タグ追加/削除
ai-task-manager update 1 --add-tags "important"
ai-task-manager update 1 --remove-tags "urgent"

# 7. ガントチャート
ai-task-manager gantt --range 2025-01

# 8. タグ一覧
ai-task-manager tags

# 9. 削除エラー確認（子タスクあり）
ai-task-manager delete 1
# 期待: エラーメッセージ表示

# 10. 子タスク削除 → 親タスク削除
ai-task-manager delete 2 --force
ai-task-manager delete 3 --force
ai-task-manager delete 1 --force
```

### 5.2 ユニットテスト

```python
# tests/test_database.py
import pytest
from ai_task_manager.database import init_db, get_or_create_tag

def test_init_db():
    """データベース初期化テスト"""
    init_db()  # エラーが発生しないこと

def test_get_or_create_tag():
    """タグ取得/作成テスト"""
    tag_id1 = get_or_create_tag("test")
    tag_id2 = get_or_create_tag("test")
    assert tag_id1 == tag_id2  # 同じIDが返される
```

---

## 📚 6. ドキュメント更新

Phase 1 完了後、以下のドキュメントを更新:

1. **README.md**: タグ機能の使用例を追加
2. **API_REFERENCE.md**: タグ関連APIを追加
3. **PROJECT_SETTINGS.md**: Phase 1 完了チェックをONに

---

## 🚀 7. Phase 2 への準備

Phase 1 が完了したら、以下を検討:

- [ ] HTML ガントチャート（Mermaid.js）
- [ ] JSON出力モード（`--json` フラグ）
- [ ] 相対日付入力（「明日」「来週」）
- [ ] ブラウザ自動起動（WSL対応）

---

## 📝 8. トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'ai_task_manager'`

```bash
pip install -e .
```

### エラー: `sqlite3.OperationalError: no such table: tasks`

```bash
rm -rf data/tasks.db
ai-task-manager list  # 自動的に再作成
```

### エラー: `FOREIGN KEY constraint failed`

```bash
# 外部キー制約の確認
sqlite3 data/tasks.db "PRAGMA foreign_keys"
# 1 が返ってくること
```

---

## 🎓 9. まとめ

このドキュメントに従って実装すれば、以下が完成します:

- ✅ タグ機能付きタスク管理システム
- ✅ 階層的なタスク構造
- ✅ ツリー表示とガントチャート
- ✅ 包括的なエラーハンドリング
- ✅ 6時間で実装可能な設計

**実装時間の内訳**:
- ステップ0-2: 1.5時間（基盤）
- ステップ3-4: 2.5時間（CLI）
- ステップ5: 1.5時間（ツリー）
- ステップ6: 1.5時間（ガントチャート）
- ステップ7: 0.5時間（パッケージング）

**合計: 6時間**
