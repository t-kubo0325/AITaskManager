# タスク視覚化機能 技術仕様書

## 目次

1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [データベーススキーマ](#データベーススキーマ)
4. [コマンドラインインターフェース](#コマンドラインインターフェース)
5. [機能詳細仕様](#機能詳細仕様)
6. [実装手順](#実装手順)
7. [コード実装例](#コード実装例)

---

## 概要

### 目的

Claude Codeが操作できるCLIベースのタスク管理ツールに、人間が視覚的にタスクを確認できる表示機能を追加する。

### 実装フェーズ

| フェーズ | 機能 | 優先度 | 実装時間 | トークン消費 |
|---------|------|--------|---------|-------------|
| Phase 1 | ツリー表示 | 高 | 2時間 | 1,000〜1,500/回 |
| Phase 1 | ASCII ガントチャート | 高 | 3時間 | 1,500〜2,000/回 |
| Phase 2 | HTML生成（Mermaid.js） | 中 | 4〜5時間 | 500（初回のみ） |
| Phase 3 | 統計ダッシュボード | 低 | 6〜8時間 | 500（初回のみ） |

---

## システムアーキテクチャ

### ディレクトリ構造

```
AITaskManager/
├── ai_task_manager/
│   ├── __init__.py
│   ├── cli.py                  # CLIエントリーポイント
│   ├── database.py             # データベース操作
│   ├── models.py               # データモデル
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── add.py              # タスク追加
│   │   ├── list.py             # タスク一覧
│   │   ├── update.py           # タスク更新
│   │   ├── delete.py           # タスク削除
│   │   ├── tree.py             # ツリー表示（新規）
│   │   ├── gantt.py            # ガントチャート（新規）
│   │   └── dashboard.py        # ダッシュボード（新規）
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── ascii_gantt.py      # ASCIIガントチャート生成
│   │   ├── tree_view.py        # ツリー表示生成
│   │   ├── html_generator.py   # HTML生成
│   │   └── templates/
│   │       ├── gantt.html      # Mermaidガントチャート
│   │       └── dashboard.html  # 統計ダッシュボード
│   └── utils/
│       ├── __init__.py
│       ├── date_utils.py       # 日付操作
│       └── color.py            # ターミナル色付け
├── tests/
│   ├── test_visualization.py
│   └── test_commands.py
├── docs/
│   ├── TASK_VISUALIZATION_SPEC.md
│   └── API_REFERENCE.md
├── setup.py
├── requirements.txt
└── README.md
```

### 技術スタック

- **言語**: Python 3.8+
- **データベース**: SQLite
- **CLI フレームワーク**: Click または argparse
- **日付操作**: datetime, dateutil
- **HTML生成**: Jinja2
- **視覚化ライブラリ**: Mermaid.js（CDN）, Chart.js（CDN）

---

## データベーススキーマ

### tasks テーブル

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
    parent_id INTEGER,
    start_date TEXT,  -- ISO 8601 format: YYYY-MM-DD
    due_date TEXT,    -- ISO 8601 format: YYYY-MM-DD
    completed_date TEXT,
    progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),  -- 0〜100%
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

### インデックス

```sql
CREATE INDEX idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
```

### マイグレーション（既存DBに追加する場合）

```sql
-- 進捗率カラム追加
ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0;

-- 開始日カラム追加（存在しない場合）
ALTER TABLE tasks ADD COLUMN start_date TEXT;
```

---

## コマンドラインインターフェース

### 基本コマンド

```bash
# タスク追加
ai-task-manager add "タスク名" [OPTIONS]
  --description, -d TEXT       タスクの説明
  --category, -c TEXT          カテゴリ
  --priority, -p [low|medium|high]  優先度
  --parent, -P INTEGER         親タスクID
  --start DATE                 開始日 (YYYY-MM-DD)
  --due DATE                   期限 (YYYY-MM-DD)

# タスク一覧
ai-task-manager list [OPTIONS]
  --category, -c TEXT          カテゴリでフィルタ
  --status, -s TEXT            ステータスでフィルタ
  --priority, -p TEXT          優先度でフィルタ

# タスク更新
ai-task-manager update <ID> [OPTIONS]
  --title TEXT                 タスク名
  --status [pending|in_progress|completed|cancelled]
  --progress INTEGER           進捗率 (0-100)
  --start DATE                 開始日
  --due DATE                   期限

# タスク削除
ai-task-manager delete <ID>
```

### 視覚化コマンド（新規）

```bash
# ツリー表示
ai-task-manager tree [OPTIONS]
  --category, -c TEXT          カテゴリでフィルタ
  --status, -s TEXT            ステータスでフィルタ
  --depth INTEGER              表示する階層の深さ（デフォルト: 無制限）

# ASCII ガントチャート
ai-task-manager gantt [OPTIONS]
  --range TEXT                 表示範囲 (YYYY-MM または YYYY-MM-DD:YYYY-MM-DD)
  --category, -c TEXT          カテゴリでフィルタ
  --status, -s TEXT            ステータスでフィルタ
  --priority, -p TEXT          優先度でフィルタ
  --width INTEGER              チャート幅（デフォルト: 80）

# HTML ガントチャート生成
ai-task-manager gantt --html [OPTIONS]
  --output, -o PATH            出力ファイルパス（デフォルト: gantt.html）
  --open                       生成後ブラウザで開く
  --range TEXT                 表示範囲

# 統計ダッシュボード
ai-task-manager dashboard [OPTIONS]
  --html                       HTML形式で出力
  --output, -o PATH            出力ファイルパス
  --open                       生成後ブラウザで開く
```

---

## 機能詳細仕様

### 1. ツリー表示

#### 出力例

```
📁 すべてのタスク
├─ [高] プロジェクトA (2025/01/10 - 2025/02/28) [進行中] 60%
│  ├─ 要件定義 (2025/01/10 - 2025/01/15) [完了] 100%
│  ├─ 設計書作成 (2025/01/16 - 2025/01/25) [完了] 100%
│  └─ 実装 (2025/01/26 - 2025/02/15) [進行中] 40%
│     ├─ フロントエンド (2025/01/26 - 2025/02/05) [進行中] 50%
│     └─ バックエンド (2025/02/01 - 2025/02/15) [未着手] 0%
├─ [中] ドキュメント作成 (2025/01/20 - 2025/01/31) [進行中] 30%
└─ [低] ミーティング準備 (2025/01/15) [完了] 100%

統計:
  総タスク数: 7
  完了: 3 (42.9%)
  進行中: 3 (42.9%)
  未着手: 1 (14.2%)
```

#### 表示ルール

- 親子関係を階層的に表示
- インデントは全角スペース2つ
- 記号: `├─` (子), `└─` (最後の子), `│` (縦線)
- 優先度: `[高]`, `[中]`, `[低]`
- ステータス: `[未着手]`, `[進行中]`, `[完了]`, `[中止]`
- 進捗率: `60%` （status=in_progress または completed の場合のみ表示）
- 日付: `(開始日 - 期限)` または `(期限)` （開始日がない場合）

#### 色付けルール（ターミナル対応）

- 優先度高: 赤
- 優先度中: 黄
- 優先度低: 緑
- 完了: 灰色（取り消し線）
- 期限超過: 赤背景

---

### 2. ASCII ガントチャート

#### 出力例（月表示）

```
タスクガントチャート: 2025年1月
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID  | タスク名                    | 10   15   20   25   30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
42  | プロジェクトA               | [=============================>     ]
43  | ├─ 要件定義                 | [====>                              ]
44  | ├─ 設計書作成               |       [========>                    ]
45  | └─ 実装                     |                [============>       ]
46  | ドキュメント作成            |           [==========>              ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

凡例:
  [=] タスク期間  [>] 現在位置  [!] 期限超過  [✓] 完了

統計:
  期間: 2025/01/10 - 2025/01/31
  総タスク数: 5
  完了: 2 (40%)
```

#### 表示ルール

- X軸: 日付（5日単位で目盛り）
- Y軸: タスクID + タスク名（親子関係を視覚化）
- バーの種類:
  - `[====]`: 進行中のタスク
  - `[✓✓✓✓]`: 完了したタスク
  - `[!!!!]`: 期限超過のタスク
  - `[----]`: 未着手のタスク
- 現在位置: `>` 記号で表示
- 親子関係: インデント + `├─`, `└─`

#### アルゴリズム

```python
def generate_ascii_gantt(tasks, start_date, end_date, width=80):
    """
    1. 表示期間の日数を計算
    2. width から日付軸の幅を決定（タスク名カラムを除く）
    3. 各タスクの開始日・期限から、バーの開始位置と長さを計算
    4. バーを描画（ステータスに応じて記号を変更）
    5. 現在日を `>` で表示
    """
    pass
```

#### 期間指定の処理

- `--range 2025-01`: 2025年1月全体を表示
- `--range 2025-01-10:2025-01-31`: 指定期間を表示
- 指定なし: 今月を表示

---

### 3. HTML ガントチャート（Mermaid.js）

#### 生成されるHTML

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>タスク管理 ガントチャート</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .info {
            margin: 20px 0;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 4px;
        }
        .mermaid {
            background: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗓️ タスク管理 ガントチャート</h1>
        <div class="info">
            <p><strong>生成日時:</strong> {{ generated_at }}</p>
            <p><strong>表示期間:</strong> {{ start_date }} 〜 {{ end_date }}</p>
            <p><strong>総タスク数:</strong> {{ total_tasks }}</p>
        </div>
        <div class="mermaid">
{{ mermaid_chart }}
        </div>
    </div>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            gantt: {
                titleTopMargin: 25,
                barHeight: 30,
                fontSize: 14
            }
        });
    </script>
</body>
</html>
```

#### Mermaid ガントチャート構文生成

```python
def generate_mermaid_gantt(tasks):
    """
    Mermaid.js のガントチャート構文を生成

    例:
    gantt
        title タスク管理ガントチャート
        dateFormat YYYY-MM-DD
        section プロジェクトA
        要件定義      :done, task1, 2025-01-10, 2025-01-15
        設計書作成    :done, task2, 2025-01-16, 2025-01-25
        実装          :active, task3, 2025-01-26, 2025-02-15
        section ドキュメント
        ドキュメント作成 :task4, 2025-01-20, 2025-01-31
    """
    lines = [
        "gantt",
        "    title タスク管理ガントチャート",
        "    dateFormat YYYY-MM-DD"
    ]

    # カテゴリごとにセクション分け
    tasks_by_category = group_by_category(tasks)

    for category, category_tasks in tasks_by_category.items():
        lines.append(f"    section {category}")

        for task in category_tasks:
            status = get_mermaid_status(task.status)
            lines.append(
                f"    {task.title}      :{status}, task{task.id}, "
                f"{task.start_date}, {task.due_date}"
            )

    return "\n".join(lines)

def get_mermaid_status(status):
    """ステータスをMermaidの状態に変換"""
    mapping = {
        'completed': 'done',
        'in_progress': 'active',
        'pending': '',
        'cancelled': 'crit'
    }
    return mapping.get(status, '')
```

#### ブラウザ起動（WSL対応）

```python
import subprocess
import platform

def open_in_browser(file_path):
    """生成されたHTMLをブラウザで開く"""
    abs_path = os.path.abspath(file_path)

    if platform.system() == "Windows":
        os.startfile(abs_path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", abs_path])
    else:  # Linux / WSL
        # WSL環境の検出
        if "microsoft" in platform.uname().release.lower():
            # WSL: wslview を使用
            subprocess.run(["wslview", abs_path])
        else:
            # 通常のLinux: xdg-open
            subprocess.run(["xdg-open", abs_path])
```

---

### 4. 統計ダッシュボード

#### 出力例（CLI版）

```
📊 タスク管理 統計ダッシュボード
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 全体概要
  総タスク数: 42
  完了: 18 (42.9%)
  進行中: 15 (35.7%)
  未着手: 9 (21.4%)

■ カテゴリ別タスク数
  Work     : ████████████████████ 20 (47.6%)
  Personal : ████████████ 12 (28.6%)
  Study    : ██████ 6 (14.3%)
  その他   : ████ 4 (9.5%)

■ 優先度別分布
  高       : ███████ 8 (19.0%)
  中       : ████████████████████████ 25 (59.5%)
  低       : ████████ 9 (21.4%)

■ 期限別タスク
  期限超過 : 3件
  今日期限 : 2件
  今週期限 : 7件
  今月期限 : 15件

■ 今週の進捗
  完了タスク: 5件
  追加タスク: 3件
  平均進捗率: 65%

■ 期限超過タスク ⚠️
  [42] プロジェクトA - 設計書 (期限: 2025/01/10) [進行中]
  [56] レポート提出 (期限: 2025/01/12) [未着手]
  [61] 請求書作成 (期限: 2025/01/14) [進行中]
```

#### HTML ダッシュボード

Chart.js を使用して以下のグラフを表示:

1. **円グラフ**: カテゴリ別タスク数
2. **棒グラフ**: ステータス別タスク数
3. **折れ線グラフ**: 週次完了タスク数の推移
4. **テーブル**: 期限超過タスク一覧

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>タスク管理ダッシュボード</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>📊 タスク管理ダッシュボード</h1>
    <div class="dashboard">
        <div class="chart-container">
            <canvas id="categoryChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="statusChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="priorityChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="progressChart"></canvas>
        </div>
    </div>
    <script>
        // Chart.js グラフ生成コード
        const categoryData = {{ category_data | tojson }};
        new Chart(document.getElementById('categoryChart'), {
            type: 'pie',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.values,
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: { display: true, text: 'カテゴリ別タスク数' }
                }
            }
        });
        // ... 他のグラフも同様に生成
    </script>
</body>
</html>
```

---

## 実装手順

### Phase 1: 基本構造の実装（3〜4時間）

#### 1. プロジェクト初期化

```bash
# ディレクトリ作成
mkdir -p ai_task_manager/{commands,visualization,utils,visualization/templates}
mkdir tests docs

# 依存関係ファイル作成
cat > requirements.txt << EOF
click>=8.0.0
jinja2>=3.0.0
python-dateutil>=2.8.0
EOF

# setup.py 作成（後述）
```

#### 2. データベース初期化

`ai_task_manager/database.py` を作成:

```python
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".ai_task_manager" / "tasks.db"

def init_db():
    """データベースを初期化"""
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
            progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")

    conn.commit()
    conn.close()
```

#### 3. データモデル

`ai_task_manager/models.py`:

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
        """期限切れかどうか"""
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return self.due_date < date.today()
        return False

    @classmethod
    def from_db_row(cls, row):
        """データベース行からTaskオブジェクトを生成"""
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
            progress=row[10],
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None
        )
```

#### 4. CLI エントリーポイント

`ai_task_manager/cli.py`:

```python
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
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), default='medium')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--parent', '-P', type=int, help='親タスクID')
def add(title, description, category, priority, start, due, parent):
    """新しいタスクを追加"""
    from ai_task_manager.commands.add import add_task
    add_task(title, description, category, priority, start, due, parent)

@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
def list(category, status, priority):
    """タスク一覧を表示"""
    from ai_task_manager.commands.list import list_tasks
    list_tasks(category, status, priority)

# ... 他のコマンドも同様に定義

if __name__ == '__main__':
    cli()
```

---

### Phase 2: ツリー表示の実装（2時間）

`ai_task_manager/visualization/tree_view.py`:

```python
from typing import List, Optional
from ai_task_manager.models import Task
from ai_task_manager.utils.color import colorize

TREE_SYMBOLS = {
    'branch': '├─ ',
    'last': '└─ ',
    'pipe': '│  ',
    'space': '   '
}

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

    # 指定された親IDの子タスクを取得
    child_tasks = [t for t in tasks if t.parent_id == parent_id]

    for i, task in enumerate(child_tasks):
        is_last_child = (i == len(child_tasks) - 1)

        # 現在のタスクの表示
        prefix = TREE_SYMBOLS['last'] if is_last_child else TREE_SYMBOLS['branch']
        task_line = format_task_line(task)
        output.append(f"{indent}{prefix}{task_line}")

        # 子タスクの再帰的表示
        new_indent = indent + (TREE_SYMBOLS['space'] if is_last_child else TREE_SYMBOLS['pipe'])
        child_output = generate_tree_view(tasks, task.id, new_indent, is_last_child)
        if child_output:
            output.append(child_output)

    return '\n'.join(output)

def format_task_line(task: Task) -> str:
    """タスクを1行で表示"""
    # 優先度
    priority_mark = {
        'high': colorize('[高]', 'red'),
        'medium': colorize('[中]', 'yellow'),
        'low': colorize('[低]', 'green')
    }.get(task.priority, '[中]')

    # タスク名
    title = task.title
    if task.status == 'completed':
        title = colorize(title, 'gray', strikethrough=True)
    elif task.is_overdue:
        title = colorize(title, 'red', bold=True)

    # 日付
    date_str = ''
    if task.start_date and task.due_date:
        date_str = f"({task.start_date} - {task.due_date})"
    elif task.due_date:
        date_str = f"({task.due_date})"

    # ステータス
    status_mark = {
        'pending': '[未着手]',
        'in_progress': '[進行中]',
        'completed': '[完了]',
        'cancelled': '[中止]'
    }.get(task.status, '')

    # 進捗率
    progress_str = ''
    if task.status in ('in_progress', 'completed') and task.progress > 0:
        progress_str = f"{task.progress}%"

    parts = [priority_mark, title, date_str, status_mark, progress_str]
    return ' '.join(p for p in parts if p)
```

---

### Phase 3: ASCII ガントチャートの実装（3時間）

`ai_task_manager/visualization/ascii_gantt.py`:

```python
from datetime import date, timedelta
from typing import List, Tuple
from ai_task_manager.models import Task

def generate_ascii_gantt(tasks: List[Task], start_date: date, end_date: date,
                         width: int = 80) -> str:
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
    # タスク名カラムの幅を計算
    max_task_name_len = max(len(format_task_name(t)) for t in tasks)
    name_col_width = min(max_task_name_len + 5, 40)

    # チャート部分の幅
    chart_width = width - name_col_width - 10  # IDカラム + 区切り文字分

    # ヘッダー生成
    output = []
    output.append(generate_header(start_date, end_date))
    output.append('━' * width)
    output.append(generate_timeline_header(start_date, end_date, name_col_width, chart_width))
    output.append('━' * width)

    # 各タスクのバー生成
    for task in tasks:
        task_line = generate_task_bar(task, start_date, end_date, name_col_width, chart_width)
        output.append(task_line)

    output.append('━' * width)
    output.append(generate_legend())
    output.append(generate_statistics(tasks, start_date, end_date))

    return '\n'.join(output)

def generate_timeline_header(start_date: date, end_date: date,
                             name_width: int, chart_width: int) -> str:
    """タイムライン目盛りヘッダーを生成"""
    total_days = (end_date - start_date).days + 1

    # 5日単位で目盛りを配置
    timeline = [''] * chart_width
    for i in range(0, total_days, 5):
        current_date = start_date + timedelta(days=i)
        position = int((i / total_days) * chart_width)
        if position < chart_width:
            timeline[position] = str(current_date.day).rjust(2)

    timeline_str = ''.join(timeline)
    return f"{'ID':<3} | {'タスク名':<{name_width}} | {timeline_str}"

def generate_task_bar(task: Task, start_date: date, end_date: date,
                      name_width: int, chart_width: int) -> str:
    """個別タスクのバーを生成"""
    # タスク名（親子関係を表示）
    task_name = format_task_name(task)

    # バーの描画
    bar = [' '] * chart_width

    if task.start_date and task.due_date:
        # タスクの開始・終了位置を計算
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
    return f"{task.id:<3} | {task_name:<{name_width}} | [{bar_str}]"

def format_task_name(task: Task) -> str:
    """タスク名をフォーマット（親子関係を表示）"""
    # 親子関係の判定は呼び出し元で処理済みと仮定
    # ここではタスク名のみ返す
    return task.title

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

def generate_statistics(tasks: List[Task], start_date: date, end_date: date) -> str:
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

---

### Phase 4: HTML生成の実装（4〜5時間）

`ai_task_manager/visualization/html_generator.py`:

```python
from datetime import datetime
from pathlib import Path
from typing import List
from jinja2 import Template
from ai_task_manager.models import Task

TEMPLATE_DIR = Path(__file__).parent / 'templates'

def generate_html_gantt(tasks: List[Task], output_path: str) -> str:
    """
    Mermaid.js を使用したHTML ガントチャートを生成

    Args:
        tasks: タスクリスト
        output_path: 出力ファイルパス

    Returns:
        生成されたファイルの絶対パス
    """
    template_path = TEMPLATE_DIR / 'gantt.html'
    template = Template(template_path.read_text(encoding='utf-8'))

    # Mermaid チャート構文を生成
    mermaid_chart = generate_mermaid_syntax(tasks)

    # テンプレートに値を注入
    html_content = template.render(
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        start_date=min(t.start_date for t in tasks if t.start_date),
        end_date=max(t.due_date for t in tasks if t.due_date),
        total_tasks=len(tasks),
        mermaid_chart=mermaid_chart
    )

    # ファイルに書き込み
    output_file = Path(output_path).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding='utf-8')

    return str(output_file)

def generate_mermaid_syntax(tasks: List[Task]) -> str:
    """Mermaid ガントチャート構文を生成"""
    lines = [
        "gantt",
        "    title タスク管理ガントチャート",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %m/%d"
    ]

    # カテゴリごとにグループ化
    tasks_by_category = {}
    for task in tasks:
        category = task.category or 'その他'
        if category not in tasks_by_category:
            tasks_by_category[category] = []
        tasks_by_category[category].append(task)

    # 各カテゴリのタスクを出力
    for category, category_tasks in tasks_by_category.items():
        lines.append(f"    section {category}")

        for task in category_tasks:
            if not task.start_date or not task.due_date:
                continue

            # ステータスをMermaidの状態に変換
            status = {
                'completed': 'done',
                'in_progress': 'active',
                'cancelled': 'crit',
                'pending': ''
            }.get(task.status, '')

            task_line = f"    {task.title}    :{status}, task{task.id}, "
            task_line += f"{task.start_date}, {task.due_date}"
            lines.append(task_line)

    return '\n'.join(lines)
```

`ai_task_manager/visualization/templates/gantt.html`:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>タスク管理 ガントチャート</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', 'Hiragino Sans', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .info-item {
            display: flex;
            flex-direction: column;
        }
        .info-label {
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .info-value {
            font-size: 18px;
            font-weight: 600;
            color: #212529;
        }
        .chart-wrapper {
            padding: 30px;
            background: white;
        }
        .mermaid {
            display: flex;
            justify-content: center;
        }
        footer {
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗓️ タスク管理ガントチャート</h1>
            <p>AI Task Manager によって生成されました</p>
        </header>

        <div class="info">
            <div class="info-item">
                <span class="info-label">生成日時</span>
                <span class="info-value">{{ generated_at }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">表示期間</span>
                <span class="info-value">{{ start_date }} 〜 {{ end_date }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">総タスク数</span>
                <span class="info-value">{{ total_tasks }}件</span>
            </div>
        </div>

        <div class="chart-wrapper">
            <div class="mermaid">
{{ mermaid_chart }}
            </div>
        </div>

        <footer>
            Generated by AI Task Manager | Powered by Mermaid.js
        </footer>
    </div>

    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            themeVariables: {
                primaryColor: '#667eea',
                primaryTextColor: '#fff',
                primaryBorderColor: '#667eea',
                lineColor: '#667eea',
                secondaryColor: '#764ba2',
                tertiaryColor: '#f8f9fa'
            },
            gantt: {
                titleTopMargin: 25,
                barHeight: 35,
                barGap: 8,
                topPadding: 50,
                leftPadding: 120,
                gridLineStartPadding: 35,
                fontSize: 14,
                numberSectionStyles: 4
            }
        });
    </script>
</body>
</html>
```

---

### Phase 5: コマンド実装

`ai_task_manager/commands/tree.py`:

```python
import click
import sqlite3
from ai_task_manager.database import DB_PATH
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view

def tree_command(category, status, depth):
    """ツリー表示コマンド"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # フィルタ条件を構築
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        click.echo("タスクが見つかりません。")
        return

    tasks = [Task.from_db_row(row) for row in rows]

    # ツリー表示を生成
    tree_output = generate_tree_view(tasks)
    click.echo("📁 すべてのタスク")
    click.echo(tree_output)

    # 統計情報
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    pending = sum(1 for t in tasks if t.status == 'pending')

    click.echo(f"\n統計:")
    click.echo(f"  総タスク数: {total}")
    click.echo(f"  完了: {completed} ({completed/total*100:.1f}%)")
    click.echo(f"  進行中: {in_progress} ({in_progress/total*100:.1f}%)")
    click.echo(f"  未着手: {pending} ({pending/total*100:.1f}%)")
```

`ai_task_manager/commands/gantt.py`:

```python
import click
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from ai_task_manager.database import DB_PATH
from ai_task_manager.models import Task
from ai_task_manager.visualization.ascii_gantt import generate_ascii_gantt
from ai_task_manager.visualization.html_generator import generate_html_gantt
import subprocess
import platform

def gantt_command(range_str, category, status, priority, width, html, output, open_browser):
    """ガントチャート表示コマンド"""
    # 日付範囲の解析
    start_date, end_date = parse_date_range(range_str)

    # タスクを取得
    conn = sqlite3.connect(DB_PATH)
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
        click.echo("表示するタスクがありません。")
        return

    tasks = [Task.from_db_row(row) for row in rows]

    if html:
        # HTML生成
        output_path = output or 'gantt.html'
        file_path = generate_html_gantt(tasks, output_path)
        click.echo(f"✓ HTMLファイルを生成しました: {file_path}")

        if open_browser:
            open_in_browser(file_path)
            click.echo("ブラウザで開きました。")
    else:
        # ASCII表示
        gantt_chart = generate_ascii_gantt(tasks, start_date, end_date, width)
        click.echo(gantt_chart)

def parse_date_range(range_str):
    """日付範囲文字列を解析"""
    if not range_str:
        # デフォルト: 今月
        today = date.today()
        start = date(today.year, today.month, 1)
        end = start + relativedelta(months=1) - relativedelta(days=1)
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
    end = start + relativedelta(months=1) - relativedelta(days=1)
    return start, end

def open_in_browser(file_path):
    """ブラウザでHTMLファイルを開く"""
    import os
    abs_path = os.path.abspath(file_path)

    if platform.system() == "Windows":
        os.startfile(abs_path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", abs_path])
    else:
        # Linux / WSL
        if "microsoft" in platform.uname().release.lower():
            subprocess.run(["wslview", abs_path])
        else:
            subprocess.run(["xdg-open", abs_path])
```

---

## コード実装例

### カラー出力ユーティリティ

`ai_task_manager/utils/color.py`:

```python
from typing import Optional

# ANSI エスケープコード
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'gray': '\033[90m',
    'reset': '\033[0m'
}

STYLES = {
    'bold': '\033[1m',
    'underline': '\033[4m',
    'strikethrough': '\033[9m'
}

def colorize(text: str, color: Optional[str] = None,
             bold: bool = False, underline: bool = False,
             strikethrough: bool = False) -> str:
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
    """
    codes = []

    if color and color in COLORS:
        codes.append(COLORS[color])

    if bold:
        codes.append(STYLES['bold'])

    if underline:
        codes.append(STYLES['underline'])

    if strikethrough:
        codes.append(STYLES['strikethrough'])

    if not codes:
        return text

    return ''.join(codes) + text + COLORS['reset']
```

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name='ai-task-manager',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
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
    author='Your Name',
    author_email='your.email@example.com',
    description='Claude Code対応タスク管理ツール',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/ai-task-manager',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
```

---

## テスト

### ツリー表示のテスト

`tests/test_tree_view.py`:

```python
import pytest
from datetime import date
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view, format_task_line

def test_tree_view_single_task():
    """単一タスクのツリー表示"""
    tasks = [
        Task(id=1, title="タスク1", status='pending')
    ]

    output = generate_tree_view(tasks)
    assert "タスク1" in output

def test_tree_view_parent_child():
    """親子タスクのツリー表示"""
    tasks = [
        Task(id=1, title="親タスク", status='in_progress'),
        Task(id=2, title="子タスク1", parent_id=1, status='completed'),
        Task(id=3, title="子タスク2", parent_id=1, status='pending')
    ]

    output = generate_tree_view(tasks)
    assert "親タスク" in output
    assert "├─ " in output or "└─ " in output
    assert "子タスク1" in output
    assert "子タスク2" in output

def test_format_task_line():
    """タスク行のフォーマット"""
    task = Task(
        id=1,
        title="テストタスク",
        priority='high',
        status='in_progress',
        start_date=date(2025, 1, 10),
        due_date=date(2025, 1, 31),
        progress=50
    )

    line = format_task_line(task)
    assert "テストタスク" in line
    assert "進行中" in line
    assert "50%" in line
```

### ASCII ガントチャートのテスト

`tests/test_ascii_gantt.py`:

```python
import pytest
from datetime import date
from ai_task_manager.models import Task
from ai_task_manager.visualization.ascii_gantt import (
    generate_ascii_gantt,
    get_bar_character,
    generate_task_bar
)

def test_bar_character_selection():
    """ステータスに応じたバー文字"""
    assert get_bar_character(Task(id=1, title="T", status='completed')) == '✓'
    assert get_bar_character(Task(id=1, title="T", status='in_progress')) == '='
    assert get_bar_character(Task(id=1, title="T", status='pending')) == '-'

def test_overdue_bar_character():
    """期限超過タスクのバー文字"""
    task = Task(
        id=1,
        title="期限超過",
        status='in_progress',
        start_date=date(2025, 1, 1),
        due_date=date(2025, 1, 5)  # 過去の日付
    )
    assert task.is_overdue
    assert get_bar_character(task) == '!'

def test_generate_gantt_chart():
    """ガントチャート全体の生成"""
    tasks = [
        Task(
            id=1,
            title="タスク1",
            status='in_progress',
            start_date=date(2025, 1, 10),
            due_date=date(2025, 1, 20)
        )
    ]

    chart = generate_ascii_gantt(tasks, date(2025, 1, 1), date(2025, 1, 31))

    assert "タスク1" in chart
    assert "2025年1月" in chart
    assert "統計" in chart
```

---

## インストールと実行

### インストール

```bash
# 開発モードでインストール
cd /home/user/AITaskManager
pip install -e .

# または通常インストール
pip install .
```

### 初回実行

```bash
# データベース初期化（自動）
ai-task-manager list

# サンプルタスク追加
ai-task-manager add "プロジェクトA" --category "Work" --priority high --start 2025-01-10 --due 2025-02-28
ai-task-manager add "要件定義" --parent 1 --start 2025-01-10 --due 2025-01-15
ai-task-manager add "設計書作成" --parent 1 --start 2025-01-16 --due 2025-01-25
ai-task-manager add "実装" --parent 1 --start 2025-01-26 --due 2025-02-15

# ツリー表示
ai-task-manager tree

# ASCII ガントチャート
ai-task-manager gantt --range 2025-01

# HTML ガントチャート生成
ai-task-manager gantt --html --output ~/gantt.html --open
```

---

## まとめ

この仕様書に従って実装することで、以下の機能が実現できます:

1. **ツリー表示**: 階層的なタスク構造を一目で把握
2. **ASCII ガントチャート**: ターミナルで動作する軽量な視覚化
3. **HTML ガントチャート**: ブラウザで美しく表示できる高品質な視覚化
4. **統計ダッシュボード**: タスクの進捗状況を多角的に分析

各フェーズを段階的に実装することで、必要な機能から順に利用可能になります。

---

## 次のステップ

1. Phase 1（ツリー表示 + ASCII ガントチャート）の実装
2. 動作確認とバグ修正
3. Phase 2（HTML生成）の実装
4. WSL環境での動作確認
5. Phase 3（統計ダッシュボード）の実装
6. ドキュメント整備
7. テストカバレッジの向上
