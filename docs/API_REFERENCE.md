# API リファレンス

## データモデル

### Task クラス

```python
@dataclass
class Task:
    id: int                           # タスクID（自動採番）
    title: str                        # タスク名（必須）
    description: Optional[str]        # 説明
    category: Optional[str]           # カテゴリ（Work, Personal, Study など）
    priority: str                     # 優先度: low, medium, high
    status: str                       # ステータス: pending, in_progress, completed, cancelled
    parent_id: Optional[int]          # 親タスクID（サブタスクの場合）
    start_date: Optional[date]        # 開始日
    due_date: Optional[date]          # 期限
    completed_date: Optional[date]    # 完了日
    progress: int                     # 進捗率 (0-100)
    created_at: Optional[datetime]    # 作成日時
    updated_at: Optional[datetime]    # 更新日時
```

#### プロパティ

```python
@property
def is_overdue(self) -> bool:
    """期限切れかどうかを判定"""
    if self.due_date and self.status not in ('completed', 'cancelled'):
        return self.due_date < date.today()
    return False
```

#### クラスメソッド

```python
@classmethod
def from_db_row(cls, row: tuple) -> Task:
    """データベース行からTaskオブジェクトを生成"""
    # row = (id, title, description, category, priority, status,
    #        parent_id, start_date, due_date, completed_date,
    #        progress, created_at, updated_at)
    return cls(...)
```

---

## データベース操作

### database.py

#### init_db()

```python
def init_db() -> None:
    """
    データベースを初期化

    - ~/.ai_task_manager/tasks.db にデータベースを作成
    - tasks テーブルが存在しない場合は作成
    - インデックスを作成
    """
```

#### get_connection()

```python
def get_connection() -> sqlite3.Connection:
    """データベース接続を取得"""
    return sqlite3.connect(DB_PATH)
```

### CRUD 操作例

#### タスクの追加

```python
import sqlite3
from ai_task_manager.database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO tasks (title, description, category, priority, start_date, due_date, parent_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (title, description, category, priority, start_date, due_date, parent_id))

conn.commit()
task_id = cursor.lastrowid
conn.close()
```

#### タスクの取得

```python
# 全タスク取得
cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
rows = cursor.fetchall()

# 条件付き取得
cursor.execute("SELECT * FROM tasks WHERE category = ? AND status = ?", (category, status))
rows = cursor.fetchall()

# Taskオブジェクトに変換
tasks = [Task.from_db_row(row) for row in rows]
```

#### タスクの更新

```python
cursor.execute("""
    UPDATE tasks
    SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
""", (status, progress, task_id))

conn.commit()
```

#### タスクの削除

```python
# 単一削除
cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

# カスケード削除（親を削除すると子も削除される）
cursor.execute("DELETE FROM tasks WHERE id = ?", (parent_id,))

conn.commit()
```

---

## 視覚化API

### tree_view.py

#### generate_tree_view()

```python
def generate_tree_view(
    tasks: List[Task],
    parent_id: Optional[int] = None,
    indent: str = '',
    is_last: bool = True
) -> str:
    """
    タスクツリーを生成

    Args:
        tasks: 全タスクのリスト
        parent_id: 親タスクID（Noneはルートレベル）
        indent: 現在のインデント文字列（内部使用）
        is_last: 最後の子要素かどうか（内部使用）

    Returns:
        ツリー表示の文字列

    Example:
        >>> tasks = get_all_tasks()
        >>> tree = generate_tree_view(tasks)
        >>> print(tree)
        ├─ [高] プロジェクトA (2025/01/10 - 2025/02/28) [進行中] 60%
        │  ├─ 要件定義 [完了] 100%
        │  └─ 設計 [進行中] 40%
        └─ [中] ドキュメント作成 [未着手]
    """
```

#### format_task_line()

```python
def format_task_line(task: Task) -> str:
    """
    タスクを1行で表示

    Args:
        task: タスクオブジェクト

    Returns:
        フォーマットされた文字列

    Example:
        >>> task = Task(id=1, title="テスト", priority="high", status="in_progress")
        >>> format_task_line(task)
        "[高] テスト [進行中] 50%"
    """
```

### ascii_gantt.py

#### generate_ascii_gantt()

```python
def generate_ascii_gantt(
    tasks: List[Task],
    start_date: date,
    end_date: date,
    width: int = 80
) -> str:
    """
    ASCII ガントチャートを生成

    Args:
        tasks: 表示するタスクのリスト
        start_date: 表示開始日
        end_date: 表示終了日
        width: チャート全体の幅（文字数）

    Returns:
        ガントチャートの文字列

    Example:
        >>> tasks = get_tasks_in_range(date(2025, 1, 1), date(2025, 1, 31))
        >>> chart = generate_ascii_gantt(tasks, date(2025, 1, 1), date(2025, 1, 31))
        >>> print(chart)
        タスクガントチャート: 2025年1月
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ID  | タスク名            | 10   15   20   25   30
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        1   | プロジェクトA       | [=============================>     ]
        2   | ├─ 要件定義         | [====>                              ]
    """
```

#### get_bar_character()

```python
def get_bar_character(task: Task) -> str:
    """
    タスクのステータスに応じたバー文字を返す

    Args:
        task: タスクオブジェクト

    Returns:
        バー文字（'✓', '!', '=', '-'）

    Mapping:
        - completed: '✓'
        - overdue: '!'
        - in_progress: '='
        - pending: '-'
    """
```

### html_generator.py

#### generate_html_gantt()

```python
def generate_html_gantt(
    tasks: List[Task],
    output_path: str
) -> str:
    """
    Mermaid.js を使用したHTML ガントチャートを生成

    Args:
        tasks: タスクリスト
        output_path: 出力ファイルパス（相対パスまたは絶対パス）

    Returns:
        生成されたファイルの絶対パス

    Raises:
        OSError: ファイル書き込みに失敗した場合

    Example:
        >>> tasks = get_all_tasks()
        >>> file_path = generate_html_gantt(tasks, '~/gantt.html')
        >>> print(f"Generated: {file_path}")
        Generated: /home/user/gantt.html
    """
```

#### generate_mermaid_syntax()

```python
def generate_mermaid_syntax(tasks: List[Task]) -> str:
    """
    Mermaid ガントチャート構文を生成

    Args:
        tasks: タスクリスト

    Returns:
        Mermaid構文の文字列

    Example:
        >>> tasks = [Task(id=1, title="タスク1", category="Work",
        ...               start_date=date(2025,1,10), due_date=date(2025,1,20),
        ...               status="in_progress")]
        >>> print(generate_mermaid_syntax(tasks))
        gantt
            title タスク管理ガントチャート
            dateFormat YYYY-MM-DD
            section Work
            タスク1    :active, task1, 2025-01-10, 2025-01-20
    """
```

---

## コマンドライン インターフェース

### 基本コマンド

#### add - タスク追加

```bash
ai-task-manager add <TITLE> [OPTIONS]

Arguments:
  TITLE  タスク名（必須）

Options:
  -d, --description TEXT            タスクの説明
  -c, --category TEXT               カテゴリ
  -p, --priority [low|medium|high]  優先度（デフォルト: medium）
  --start DATE                      開始日 (YYYY-MM-DD)
  --due DATE                        期限 (YYYY-MM-DD)
  -P, --parent INTEGER              親タスクID

Examples:
  ai-task-manager add "プロジェクト計画" -c Work -p high --start 2025-01-10 --due 2025-02-28
  ai-task-manager add "要件定義" --parent 1 --start 2025-01-10 --due 2025-01-15
```

#### list - タスク一覧

```bash
ai-task-manager list [OPTIONS]

Options:
  -c, --category TEXT   カテゴリでフィルタ
  -s, --status TEXT     ステータスでフィルタ
  -p, --priority TEXT   優先度でフィルタ

Examples:
  ai-task-manager list
  ai-task-manager list -c Work -s in_progress
  ai-task-manager list -p high
```

#### update - タスク更新

```bash
ai-task-manager update <ID> [OPTIONS]

Arguments:
  ID  タスクID（必須）

Options:
  --title TEXT                                  タスク名
  --status [pending|in_progress|completed|cancelled]  ステータス
  --progress INTEGER                            進捗率 (0-100)
  --start DATE                                  開始日
  --due DATE                                    期限

Examples:
  ai-task-manager update 1 --status in_progress --progress 50
  ai-task-manager update 2 --status completed
```

#### delete - タスク削除

```bash
ai-task-manager delete <ID>

Arguments:
  ID  タスクID（必須）

Examples:
  ai-task-manager delete 5
```

### 視覚化コマンド

#### tree - ツリー表示

```bash
ai-task-manager tree [OPTIONS]

Options:
  -c, --category TEXT  カテゴリでフィルタ
  -s, --status TEXT    ステータスでフィルタ
  --depth INTEGER      表示する階層の深さ

Examples:
  ai-task-manager tree
  ai-task-manager tree -c Work
  ai-task-manager tree -s in_progress --depth 2
```

#### gantt - ガントチャート

```bash
ai-task-manager gantt [OPTIONS]

Options:
  --range TEXT            表示範囲 (YYYY-MM または YYYY-MM-DD:YYYY-MM-DD)
  -c, --category TEXT     カテゴリでフィルタ
  -s, --status TEXT       ステータスでフィルタ
  -p, --priority TEXT     優先度でフィルタ
  --width INTEGER         チャート幅（デフォルト: 80）
  --html                  HTML形式で出力
  -o, --output PATH       出力ファイルパス（デフォルト: gantt.html）
  --open                  生成後ブラウザで開く

Examples:
  # ASCII ガントチャート（今月）
  ai-task-manager gantt

  # 2025年1月のガントチャート
  ai-task-manager gantt --range 2025-01

  # 特定期間のガントチャート
  ai-task-manager gantt --range 2025-01-10:2025-02-28

  # Workカテゴリのみ表示
  ai-task-manager gantt -c Work

  # HTML生成
  ai-task-manager gantt --html --output ~/gantt.html

  # HTML生成してブラウザで開く
  ai-task-manager gantt --html --open
```

#### dashboard - 統計ダッシュボード（Phase 3）

```bash
ai-task-manager dashboard [OPTIONS]

Options:
  --html            HTML形式で出力
  -o, --output PATH 出力ファイルパス
  --open            生成後ブラウザで開く

Examples:
  # CLIダッシュボード
  ai-task-manager dashboard

  # HTMLダッシュボード
  ai-task-manager dashboard --html --open
```

---

## ユーティリティ関数

### date_utils.py

```python
def parse_date(date_str: str) -> date:
    """文字列を日付オブジェクトに変換"""
    return datetime.strptime(date_str, '%Y-%m-%d').date()

def format_date(d: date) -> str:
    """日付を文字列に変換"""
    return d.strftime('%Y-%m-%d')

def get_month_range(year: int, month: int) -> Tuple[date, date]:
    """指定月の開始日と終了日を取得"""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end
```

### color.py

```python
def colorize(
    text: str,
    color: Optional[str] = None,
    bold: bool = False,
    underline: bool = False,
    strikethrough: bool = False
) -> str:
    """
    テキストに色とスタイルを適用

    Args:
        text: 対象テキスト
        color: 色名 ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'gray')
        bold: 太字
        underline: 下線
        strikethrough: 取り消し線

    Returns:
        ANSIエスケープコード付きテキスト

    Example:
        >>> colorize("重要", "red", bold=True)
        '\033[91m\033[1m重要\033[0m'
    """
```

---

## データベーススキーマ

### tasks テーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | タスクID |
| title | TEXT | NOT NULL | タスク名 |
| description | TEXT | | 説明 |
| category | TEXT | | カテゴリ |
| priority | TEXT | CHECK(priority IN ('low', 'medium', 'high')) | 優先度 |
| status | TEXT | CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) | ステータス |
| parent_id | INTEGER | FOREIGN KEY (tasks.id) | 親タスクID |
| start_date | TEXT | | 開始日 (ISO 8601) |
| due_date | TEXT | | 期限 (ISO 8601) |
| completed_date | TEXT | | 完了日 (ISO 8601) |
| progress | INTEGER | CHECK(progress >= 0 AND progress <= 100) | 進捗率 |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

### インデックス

- `idx_tasks_parent_id`: parent_id にインデックス（階層クエリの高速化）
- `idx_tasks_category`: category にインデックス
- `idx_tasks_status`: status にインデックス
- `idx_tasks_due_date`: due_date にインデックス

---

## 使用例

### Python APIとして使用

```python
from ai_task_manager.database import DB_PATH, init_db
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view
from ai_task_manager.visualization.ascii_gantt import generate_ascii_gantt
from datetime import date
import sqlite3

# データベース初期化
init_db()

# タスク追加
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO tasks (title, category, priority, start_date, due_date)
    VALUES (?, ?, ?, ?, ?)
""", ("新規プロジェクト", "Work", "high", "2025-01-10", "2025-02-28"))

conn.commit()
project_id = cursor.lastrowid

# サブタスク追加
cursor.execute("""
    INSERT INTO tasks (title, parent_id, start_date, due_date)
    VALUES (?, ?, ?, ?)
""", ("要件定義", project_id, "2025-01-10", "2025-01-15"))

conn.commit()
conn.close()

# タスク取得
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT * FROM tasks")
rows = cursor.fetchall()
conn.close()

tasks = [Task.from_db_row(row) for row in rows]

# ツリー表示
tree = generate_tree_view(tasks)
print(tree)

# ガントチャート表示
gantt = generate_ascii_gantt(tasks, date(2025, 1, 1), date(2025, 1, 31))
print(gantt)
```

### CLIとして使用

```bash
# タスク追加
ai-task-manager add "プロジェクト開始" -c Work -p high --start 2025-01-10 --due 2025-03-31

# サブタスク追加
ai-task-manager add "フェーズ1" --parent 1 --start 2025-01-10 --due 2025-02-10
ai-task-manager add "フェーズ2" --parent 1 --start 2025-02-11 --due 2025-03-15

# ツリー表示
ai-task-manager tree

# ガントチャート（ASCII）
ai-task-manager gantt --range 2025-01

# ガントチャート（HTML）
ai-task-manager gantt --html --open

# タスクの進捗更新
ai-task-manager update 2 --status in_progress --progress 50

# タスク一覧（Work カテゴリの進行中タスク）
ai-task-manager list -c Work -s in_progress
```

---

## エラーハンドリング

### データベースエラー

```python
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # ... データベース操作 ...
    conn.commit()
except sqlite3.IntegrityError as e:
    print(f"整合性エラー: {e}")
    conn.rollback()
except sqlite3.OperationalError as e:
    print(f"操作エラー: {e}")
finally:
    conn.close()
```

### 日付パースエラー

```python
from datetime import datetime

def parse_date_safe(date_str: str) -> Optional[date]:
    """安全に日付をパース"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None
```

---

## パフォーマンス最適化

### クエリ最適化

```python
# ❌ 非効率: 全タスクを取得してからフィルタ
cursor.execute("SELECT * FROM tasks")
all_tasks = cursor.fetchall()
work_tasks = [t for t in all_tasks if t[3] == 'Work']

# ✅ 効率的: データベースでフィルタ
cursor.execute("SELECT * FROM tasks WHERE category = ?", ('Work',))
work_tasks = cursor.fetchall()
```

### インデックスの活用

```python
# よく使うカラムにインデックスを作成済み
# - parent_id (階層クエリ)
# - category (カテゴリフィルタ)
# - status (ステータスフィルタ)
# - due_date (期限検索)
```

---

## セキュリティ

### SQLインジェクション対策

```python
# ❌ 危険: 文字列連結
cursor.execute(f"SELECT * FROM tasks WHERE title = '{title}'")

# ✅ 安全: プレースホルダー使用
cursor.execute("SELECT * FROM tasks WHERE title = ?", (title,))
```

### パス操作

```python
from pathlib import Path

# ❌ 危険: ユーザー入力をそのまま使用
output_path = user_input

# ✅ 安全: パスの正規化
output_path = Path(user_input).expanduser().resolve()
```
