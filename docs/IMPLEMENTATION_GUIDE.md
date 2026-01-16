# 実装ガイド - タスク視覚化機能

## クイックスタート

### 実装優先順位

```
Phase 1（必須）: ツリー表示 + ASCII ガントチャート
  ↓ 2-3日
Phase 2（推奨）: HTML ガントチャート（Mermaid.js）
  ↓ 1週間
Phase 3（オプション）: 統計ダッシュボード
```

---

## Phase 1: 基本実装（5時間）

### ステップ1: プロジェクト構造の構築（30分）

```bash
# ディレクトリ作成
mkdir -p ai_task_manager/{commands,visualization,utils,visualization/templates}
mkdir tests docs

# 依存関係
cat > requirements.txt << 'EOF'
click>=8.0.0
jinja2>=3.0.0
python-dateutil>=2.8.0
EOF

pip install -r requirements.txt
```

### ステップ2: データベース初期化（30分）

**ファイル**: `ai_task_manager/database.py`

```python
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".ai_task_manager" / "tasks.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
            progress INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)

    # インデックス
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")

    conn.commit()
    conn.close()
```

### ステップ3: データモデル（30分）

**ファイル**: `ai_task_manager/models.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Task:
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

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return self.due_date < date.today()
        return False

    @classmethod
    def from_db_row(cls, row):
        return cls(
            id=row[0],
            title=row[1],
            description=row[2],
            category=row[3],
            priority=row[4],
            status=row[5],
            parent_id=row[6],
            start_date=datetime.strptime(row[7], '%Y-%m-%d').date() if row[7] else None,
            due_date=datetime.strptime(row[8], '%Y-%m-%d').date() if row[8] else None,
            completed_date=datetime.strptime(row[9], '%Y-%m-%d').date() if row[9] else None,
            progress=row[10] or 0,
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None
        )
```

### ステップ4: ツリー表示実装（2時間）

**ファイル**: `ai_task_manager/visualization/tree_view.py`

<details>
<summary>完全なコードを表示</summary>

```python
from typing import List, Optional
from ai_task_manager.models import Task

def generate_tree_view(tasks: List[Task], parent_id: Optional[int] = None,
                       indent: str = '', is_last: bool = True) -> str:
    """タスクツリーを生成"""
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
    """タスクを1行で表示"""
    priority_map = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}
    status_map = {
        'pending': '[未着手]',
        'in_progress': '[進行中]',
        'completed': '[完了]',
        'cancelled': '[中止]'
    }

    parts = [
        priority_map.get(task.priority, '[中]'),
        task.title
    ]

    # 日付
    if task.start_date and task.due_date:
        parts.append(f"({task.start_date} - {task.due_date})")
    elif task.due_date:
        parts.append(f"({task.due_date})")

    # ステータス
    parts.append(status_map.get(task.status, ''))

    # 進捗率
    if task.status in ('in_progress', 'completed') and task.progress > 0:
        parts.append(f"{task.progress}%")

    return ' '.join(p for p in parts if p)
```
</details>

### ステップ5: ASCII ガントチャート実装（2時間）

**ファイル**: `ai_task_manager/visualization/ascii_gantt.py`

<details>
<summary>コアロジック</summary>

```python
from datetime import date, timedelta
from typing import List
from ai_task_manager.models import Task

def generate_ascii_gantt(tasks: List[Task], start_date: date, end_date: date, width: int = 80) -> str:
    """ASCII ガントチャートを生成"""
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
    for task in tasks:
        task_line = generate_task_bar(task, start_date, end_date, name_col_width, chart_width)
        output.append(task_line)

    output.append('━' * width)
    output.append("\n凡例:\n  [=] タスク期間  [>] 現在位置  [!] 期限超過  [✓] 完了")

    return '\n'.join(output)

def generate_timeline_header(start_date: date, end_date: date, name_width: int, chart_width: int) -> str:
    """タイムライン目盛り"""
    total_days = (end_date - start_date).days + 1
    timeline = [' '] * chart_width

    for i in range(0, total_days, 5):
        current_date = start_date + timedelta(days=i)
        position = int((i / total_days) * chart_width)
        if position < chart_width - 2:
            day_str = str(current_date.day).rjust(2)
            timeline[position] = day_str[0]
            if position + 1 < chart_width:
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

        bar_char = get_bar_character(task)
        for i in range(start_pos, min(end_pos, chart_width)):
            bar[i] = bar_char

        # 現在位置
        today_offset = (date.today() - start_date).days
        if 0 <= today_offset < total_days:
            today_pos = int((today_offset / total_days) * chart_width)
            if start_pos <= today_pos < end_pos:
                bar[today_pos] = '>'

    bar_str = ''.join(bar)
    task_name = task.title[:name_width]
    return f"{task.id:<3} | {task_name:<{name_width}} | [{bar_str}]"

def get_bar_character(task: Task) -> str:
    """ステータスに応じたバー文字"""
    if task.status == 'completed':
        return '✓'
    elif task.is_overdue:
        return '!'
    elif task.status == 'in_progress':
        return '='
    else:
        return '-'
```
</details>

### ステップ6: CLI コマンド実装（1時間）

**ファイル**: `ai_task_manager/cli.py`

```python
import click
from ai_task_manager.database import init_db

@click.group()
def cli():
    """AI Task Manager"""
    init_db()

@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
def tree(category, status):
    """ツリー表示"""
    from ai_task_manager.commands.tree import tree_command
    tree_command(category, status)

@cli.command()
@click.option('--range', 'range_str', help='表示範囲 (YYYY-MM)')
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--width', default=80, help='チャート幅')
def gantt(range_str, category, width):
    """ASCII ガントチャート"""
    from ai_task_manager.commands.gantt import gantt_command
    gantt_command(range_str, category, None, None, width, False, None, False)

# 基本コマンドも追加
@cli.command()
@click.argument('title')
@click.option('--category', '-c', help='カテゴリ')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), default='medium')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--parent', type=int, help='親タスクID')
def add(title, category, priority, start, due, parent):
    """タスク追加"""
    from ai_task_manager.commands.add import add_task
    add_task(title, None, category, priority, start, due, parent)

if __name__ == '__main__':
    cli()
```

**ファイル**: `ai_task_manager/commands/add.py`

```python
import sqlite3
from ai_task_manager.database import DB_PATH
import click

def add_task(title, description, category, priority, start, due, parent):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (title, description, category, priority, start_date, due_date, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, category, priority, start, due, parent))

    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    click.echo(f"✓ タスクを追加しました (ID: {task_id})")
```

**ファイル**: `ai_task_manager/commands/tree.py`

```python
import sqlite3
from ai_task_manager.database import DB_PATH
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view
import click

def tree_command(category, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if status:
        query += " AND status = ?"
        params.append(status)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        click.echo("タスクが見つかりません。")
        return

    tasks = [Task.from_db_row(row) for row in rows]

    click.echo("📁 すべてのタスク")
    click.echo(generate_tree_view(tasks))

    # 統計
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')
    click.echo(f"\n統計: 総数={total}, 完了={completed} ({completed/total*100:.1f}%)")
```

**ファイル**: `ai_task_manager/commands/gantt.py`

```python
import sqlite3
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from ai_task_manager.database import DB_PATH
from ai_task_manager.models import Task
from ai_task_manager.visualization.ascii_gantt import generate_ascii_gantt
import click

def gantt_command(range_str, category, status, priority, width, html, output, open_browser):
    # 日付範囲解析
    start_date, end_date = parse_date_range(range_str)

    # タスク取得
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT * FROM tasks
        WHERE start_date IS NOT NULL AND due_date IS NOT NULL
        AND due_date >= ? AND start_date <= ?
    """
    params = [start_date.isoformat(), end_date.isoformat()]

    if category:
        query += " AND category = ?"
        params.append(category)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        click.echo("表示するタスクがありません。")
        return

    tasks = [Task.from_db_row(row) for row in rows]
    gantt_chart = generate_ascii_gantt(tasks, start_date, end_date, width)
    click.echo(gantt_chart)

def parse_date_range(range_str):
    if not range_str:
        today = date.today()
        start = date(today.year, today.month, 1)
        end = start + relativedelta(months=1, days=-1)
        return start, end

    year_month = datetime.strptime(range_str, '%Y-%m')
    start = date(year_month.year, year_month.month, 1)
    end = start + relativedelta(months=1, days=-1)
    return start, end
```

### ステップ7: setup.py（15分）

```python
from setuptools import setup, find_packages

setup(
    name='ai-task-manager',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.0',
        'jinja2>=3.0.0',
        'python-dateutil>=2.8.0'
    ],
    entry_points={
        'console_scripts': [
            'ai-task-manager=ai_task_manager.cli:cli',
        ],
    },
)
```

### 動作確認

```bash
# インストール
pip install -e .

# テストデータ追加
ai-task-manager add "プロジェクトA" --category "Work" --priority high --start 2025-01-10 --due 2025-02-28
ai-task-manager add "要件定義" --parent 1 --start 2025-01-10 --due 2025-01-15
ai-task-manager add "設計" --parent 1 --start 2025-01-16 --due 2025-01-25
ai-task-manager add "実装" --parent 1 --start 2025-01-26 --due 2025-02-15

# ツリー表示
ai-task-manager tree

# ガントチャート
ai-task-manager gantt --range 2025-01
```

---

## Phase 2: HTML 生成（4〜5時間）

### HTML ガントチャート実装

**ファイル**: `ai_task_manager/visualization/html_generator.py`

```python
from pathlib import Path
from jinja2 import Template
from datetime import datetime
from typing import List
from ai_task_manager.models import Task

TEMPLATE_DIR = Path(__file__).parent / 'templates'

def generate_html_gantt(tasks: List[Task], output_path: str) -> str:
    template = Template((TEMPLATE_DIR / 'gantt.html').read_text(encoding='utf-8'))

    mermaid_chart = generate_mermaid_syntax(tasks)

    html_content = template.render(
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        start_date=min((t.start_date for t in tasks if t.start_date), default='N/A'),
        end_date=max((t.due_date for t in tasks if t.due_date), default='N/A'),
        total_tasks=len(tasks),
        mermaid_chart=mermaid_chart
    )

    output_file = Path(output_path).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding='utf-8')

    return str(output_file)

def generate_mermaid_syntax(tasks: List[Task]) -> str:
    lines = [
        "gantt",
        "    title タスク管理ガントチャート",
        "    dateFormat YYYY-MM-DD"
    ]

    # カテゴリ別にグループ化
    by_category = {}
    for task in tasks:
        cat = task.category or 'その他'
        by_category.setdefault(cat, []).append(task)

    for category, cat_tasks in by_category.items():
        lines.append(f"    section {category}")
        for task in cat_tasks:
            if not task.start_date or not task.due_date:
                continue

            status_map = {
                'completed': 'done',
                'in_progress': 'active',
                'cancelled': 'crit',
                'pending': ''
            }
            status = status_map.get(task.status, '')

            lines.append(f"    {task.title}    :{status}, task{task.id}, {task.start_date}, {task.due_date}")

    return '\n'.join(lines)
```

### テンプレートファイル

**ファイル**: `ai_task_manager/visualization/templates/gantt.html`

（詳細は TASK_VISUALIZATION_SPEC.md を参照）

### CLIコマンド拡張

`ai_task_manager/cli.py` の gantt コマンドに以下を追加:

```python
@cli.command()
@click.option('--range', 'range_str', help='表示範囲 (YYYY-MM)')
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--width', default=80, help='チャート幅')
@click.option('--html', is_flag=True, help='HTML形式で出力')
@click.option('--output', '-o', default='gantt.html', help='出力ファイルパス')
@click.option('--open', 'open_browser', is_flag=True, help='生成後ブラウザで開く')
def gantt(range_str, category, width, html, output, open_browser):
    """ガントチャート表示"""
    from ai_task_manager.commands.gantt import gantt_command
    gantt_command(range_str, category, None, None, width, html, output, open_browser)
```

`ai_task_manager/commands/gantt.py` に HTML 生成ロジックを追加:

```python
def gantt_command(range_str, category, status, priority, width, html, output, open_browser):
    # ... (タスク取得は同じ)

    if html:
        from ai_task_manager.visualization.html_generator import generate_html_gantt
        import subprocess
        import platform

        file_path = generate_html_gantt(tasks, output)
        click.echo(f"✓ HTMLファイルを生成しました: {file_path}")

        if open_browser:
            if "microsoft" in platform.uname().release.lower():
                subprocess.run(["wslview", file_path])
            elif platform.system() == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
    else:
        # ASCII表示
        gantt_chart = generate_ascii_gantt(tasks, start_date, end_date, width)
        click.echo(gantt_chart)
```

---

## トラブルシューティング

### エラー: `No module named 'ai_task_manager'`

```bash
# 開発モードで再インストール
pip install -e .
```

### エラー: `sqlite3.OperationalError: no such column`

```bash
# データベースを削除して再作成
rm -rf ~/.ai_task_manager/
ai-task-manager tree  # 自動的に再作成される
```

### WSL でブラウザが開かない

```bash
# wslview をインストール
sudo apt install wslu

# または、ファイルパスを手動でコピー
ai-task-manager gantt --html --output ~/gantt.html
# 出力されたパスをWindowsブラウザで開く
```

---

## テストデータ生成スクリプト

```python
# scripts/generate_test_data.py
import subprocess
from datetime import date, timedelta

def add_task(title, category=None, priority='medium', start=None, due=None, parent=None):
    cmd = ['ai-task-manager', 'add', title]
    if category:
        cmd.extend(['--category', category])
    if priority:
        cmd.extend(['--priority', priority])
    if start:
        cmd.extend(['--start', str(start)])
    if due:
        cmd.extend(['--due', str(due)])
    if parent:
        cmd.extend(['--parent', str(parent)])

    subprocess.run(cmd)

# サンプルデータ
today = date.today()

add_task("プロジェクトA", "Work", "high",
         today, today + timedelta(days=60))

add_task("要件定義", parent=1,
         start=today, due=today + timedelta(days=10))

add_task("設計", parent=1,
         start=today + timedelta(days=11), due=today + timedelta(days=25))

add_task("実装", parent=1,
         start=today + timedelta(days=26), due=today + timedelta(days=50))

add_task("ドキュメント作成", "Work", "medium",
         today + timedelta(days=5), today + timedelta(days=30))

print("✓ テストデータを生成しました")
```

実行:

```bash
python scripts/generate_test_data.py
```

---

## まとめ

このガイドに従って実装すると、以下が完成します:

- ✅ SQLiteベースのタスク管理システム
- ✅ ツリー表示（階層的なタスク一覧）
- ✅ ASCII ガントチャート（CLI）
- ✅ HTML ガントチャート（Mermaid.js）
- ✅ WSL対応のブラウザ起動

**開発時間**: Phase 1 で 5時間、Phase 2 で 4〜5時間

**次のステップ**: 統計ダッシュボード（Phase 3）の実装
