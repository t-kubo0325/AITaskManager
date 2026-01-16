# AI Task Manager

Claude Codeが操作できるCLIベースのタスク管理ツール

## 概要

AI Task Managerは、Claude Codeが自動操作できるタスク管理システムです。CLIインターフェースを提供し、タスクの追加・更新・削除をプログラマティックに実行できます。また、人間が視覚的にタスクを確認できるように、ツリー表示、ASCII/HTMLガントチャート、統計ダッシュボードなどの視覚化機能も備えています。

### 主な機能

- ✅ **タスク管理**: 階層的なタスク構造をサポート（親子タスク）
- 📊 **ツリー表示**: タスクの階層関係を視覚的に表示
- 📅 **ASCII ガントチャート**: ターミナルで動作する軽量なガントチャート
- 🌐 **HTML ガントチャート**: ブラウザで美しく表示できる高品質ガントチャート（Mermaid.js）
- 📈 **統計ダッシュボード**: タスクの進捗状況を多角的に分析（Phase 3）
- 🤖 **Claude Code対応**: AIが自動でタスク管理を実行可能

### 技術スタック

- **言語**: Python 3.8+
- **データベース**: SQLite
- **CLI**: Click
- **視覚化**: Mermaid.js, Chart.js
- **テンプレート**: Jinja2

## クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/AITaskManager.git
cd AITaskManager

# 依存関係をインストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

### 基本的な使い方

```bash
# タスクを追加
ai-task-manager add "プロジェクト計画" --category Work --priority high --start 2025-01-10 --due 2025-02-28

# サブタスクを追加
ai-task-manager add "要件定義" --parent 1 --start 2025-01-10 --due 2025-01-15
ai-task-manager add "設計" --parent 1 --start 2025-01-16 --due 2025-01-25

# ツリー表示
ai-task-manager tree

# ASCII ガントチャート
ai-task-manager gantt --range 2025-01

# HTML ガントチャート生成
ai-task-manager gantt --html --output ~/gantt.html --open

# タスク一覧
ai-task-manager list --category Work --status in_progress

# タスク更新
ai-task-manager update 1 --status in_progress --progress 50

# タスク削除
ai-task-manager delete 5
```

## 出力例

### ツリー表示

```
📁 すべてのタスク
├─ [高] プロジェクトA (2025/01/10 - 2025/02/28) [進行中] 60%
│  ├─ 要件定義 (2025/01/10 - 2025/01/15) [完了] 100%
│  ├─ 設計書作成 (2025/01/16 - 2025/01/25) [完了] 100%
│  └─ 実装 (2025/01/26 - 2025/02/15) [進行中] 40%
│     ├─ フロントエンド [進行中] 50%
│     └─ バックエンド [未着手] 0%
└─ [中] ドキュメント作成 (2025/01/20 - 2025/01/31) [進行中] 30%

統計:
  総タスク数: 7
  完了: 3 (42.9%)
```

### ASCII ガントチャート

```
タスクガントチャート: 2025年1月
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID  | タスク名                    | 10   15   20   25   30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
42  | プロジェクトA               | [=============================>     ]
43  | ├─ 要件定義                 | [====>                              ]
44  | ├─ 設計書作成               |       [========>                    ]
45  | └─ 実装                     |                [============>       ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

凡例:
  [=] タスク期間  [>] 現在位置  [!] 期限超過  [✓] 完了
```

## ドキュメント

- **[タスク視覚化機能 技術仕様書](docs/TASK_VISUALIZATION_SPEC.md)**: 詳細な実装仕様
- **[実装ガイド](docs/IMPLEMENTATION_GUIDE.md)**: ステップバイステップの実装手順
- **[APIリファレンス](docs/API_REFERENCE.md)**: 全APIの詳細リファレンス

## 開発ロードマップ

### Phase 1: 基本実装（完了目標: 5時間）

- [x] データベース設計とスキーマ作成
- [x] データモデル実装
- [x] 基本CLIコマンド（add, list, update, delete）
- [x] ツリー表示機能
- [x] ASCII ガントチャート

### Phase 2: 高度な視覚化（完了目標: +4-5時間）

- [ ] HTML ガントチャート（Mermaid.js）
- [ ] ブラウザ自動起動（WSL対応）
- [ ] HTMLテンプレートの最適化

### Phase 3: 統計とダッシュボード（完了目標: +6-8時間）

- [ ] 統計情報の集計
- [ ] CLIダッシュボード
- [ ] HTMLダッシュボード（Chart.js）
- [ ] エクスポート機能

## プロジェクト構造

```
AITaskManager/
├── ai_task_manager/
│   ├── __init__.py
│   ├── cli.py                  # CLIエントリーポイント
│   ├── database.py             # データベース操作
│   ├── models.py               # データモデル
│   ├── commands/               # コマンド実装
│   │   ├── add.py
│   │   ├── list.py
│   │   ├── update.py
│   │   ├── delete.py
│   │   ├── tree.py
│   │   ├── gantt.py
│   │   └── dashboard.py
│   ├── visualization/          # 視覚化機能
│   │   ├── ascii_gantt.py
│   │   ├── tree_view.py
│   │   ├── html_generator.py
│   │   └── templates/
│   │       ├── gantt.html
│   │       └── dashboard.html
│   └── utils/                  # ユーティリティ
│       ├── date_utils.py
│       └── color.py
├── tests/                      # テスト
├── docs/                       # ドキュメント
├── setup.py
├── requirements.txt
└── README.md
```

## データベーススキーマ

```sql
CREATE TABLE tasks (
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
);
```

## Claude Codeとの連携

このツールは、Claude Codeが自動でタスク管理を行うために設計されています。

### 使用例

```python
# Claude Codeによる自動タスク管理
import subprocess

# タスクを追加
subprocess.run([
    'ai-task-manager', 'add', 'レポート作成',
    '--category', 'Work',
    '--priority', 'high',
    '--due', '2025-01-31'
])

# 進捗を更新
subprocess.run([
    'ai-task-manager', 'update', '1',
    '--status', 'in_progress',
    '--progress', '50'
])

# ガントチャートを生成
subprocess.run([
    'ai-task-manager', 'gantt',
    '--html', '--output', 'report.html', '--open'
])
```

## トークン消費とコスト

| 操作 | トークン消費 | 頻度 | 月間コスト（目安） |
|------|------------|------|------------------|
| ASCII ガントチャート | 1,500〜2,000 | 1日5回 | 数百円 |
| HTML 生成 | 500（初回のみ） | 週1回 | 数十円 |
| ツリー表示 | 1,000〜1,500 | 1日3回 | 数百円 |

Claude API (Opus 4.5) の場合、月間合計で約1,000円程度の想定

## ライセンス

MIT License

## コントリビューション

プルリクエストを歓迎します。大きな変更を行う場合は、まずIssueを開いて変更内容を議論してください。

## 作者

Your Name

## 謝辞

- Mermaid.js: ガントチャート視覚化
- Chart.js: 統計グラフ
- Click: CLIフレームワーク