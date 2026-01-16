# プロジェクト設定

このドキュメントは、AI Task Manager の実装前に決定した設定事項を記録します。

## 決定日

2026-01-16

---

## 1. 実装優先順位

**決定**: Phase 1から始めて、動作確認後に次へ進む

```
Phase 1（優先度: 高）✅ 完了
  ├─ データベース設計とスキーマ作成
  ├─ データモデル実装
  ├─ 基本CLIコマンド（add, list, update, delete）
  ├─ タグ機能の実装 ⭐ 追加要件
  ├─ ツリー表示機能
  └─ ASCII ガントチャート

完了時間: 約6時間（タグ機能含む）
実装日: 2026-01-16

Phase 2（優先度: 高）🚧 次の実装対象
  ├─ HTML ガントチャート生成（Mermaid.js）
  ├─ JSON出力モード（--json フラグ）
  ├─ ブラウザ自動起動（WSL対応）
  └─ HTMLテンプレートの最適化

完了目標: 4-5時間

Phase 3（優先度: 中）
  ├─ 統計ダッシュボード（CLI版）
  ├─ HTMLダッシュボード（Chart.js）
  ├─ エクスポート機能（PNG, PDF）
  └─ 設定ファイルサポート（config.yaml）

完了目標: 6-8時間

Phase 4（優先度: 中）⭐ 元々の要件
  ├─ Claude Skills機能の実装
  ├─ 自動タスク管理スクリプト
  ├─ 定期実行設定（毎日のタスク確認）
  ├─ 期限通知機能
  └─ プロジェクト進捗レポート自動生成

完了目標: 3-4時間
```

---

## 2. 技術的設定

### 2.1 データベース

**決定**: プロジェクトローカルに配置

```python
# ❌ 旧仕様（ドキュメント記載）
DB_PATH = Path.home() / ".ai_task_manager" / "tasks.db"

# ✅ 新仕様（採用）
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"
# または
DB_PATH = Path("./data/tasks.db").resolve()
```

**理由**:
- プロジェクトと一緒に管理しやすい
- バックアップが容易
- 複数のプロジェクトで異なるタスクを管理可能

**ディレクトリ構造**:
```
AITaskManager/
├── data/
│   └── tasks.db          # データベースファイル
├── ai_task_manager/
└── ...
```

### 2.2 コマンド名

**決定**: `ai-task-manager`（変更なし）

```bash
# メインコマンド
ai-task-manager add "タスク名"
ai-task-manager list
ai-task-manager tree
```

エイリアスは追加しない（シンプルさを優先）

---

## 3. データモデル拡張

### 3.1 カテゴリ

**決定**: 自由入力

```bash
# プリセットなし、ユーザーが自由に入力
ai-task-manager add "タスク" --category "Work"
ai-task-manager add "タスク" --category "個人的なプロジェクト"
```

**メリット**:
- 柔軟性が高い
- シンプルな実装

**デメリット**:
- タイポのリスク（軽減策: 既存カテゴリの補完を Phase 2 で検討）

### 3.2 タグ機能 ⭐ 重要

**決定**: Phase 1 に含める

#### データベーススキーマ追加

```sql
-- tags テーブル
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- task_tags 中間テーブル（多対多）
CREATE TABLE task_tags (
    task_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_task_tags_task_id ON task_tags(task_id);
CREATE INDEX idx_task_tags_tag_id ON task_tags(tag_id);
CREATE INDEX idx_tags_name ON tags(name);
```

#### CLI インターフェース

```bash
# タスク追加時にタグを指定
ai-task-manager add "レビュー対応" --tags "urgent,client-a,review"

# タグでフィルタ
ai-task-manager list --tags "urgent"
ai-task-manager tree --tags "client-a,urgent"

# タグ一覧
ai-task-manager tags

# タグの追加/削除
ai-task-manager update 1 --add-tags "important"
ai-task-manager update 1 --remove-tags "urgent"
```

#### データモデル

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Task:
    # ... 既存のフィールド ...
    tags: List[str] = field(default_factory=list)  # タグのリスト

@dataclass
class Tag:
    id: int
    name: str
    created_at: Optional[datetime] = None
```

**実装時間見積もり**: +1時間

---

## 4. 日付とタイムゾーン

### 4.1 日付フォーマット

**決定**: `YYYY-MM-DD` のみ

```bash
# ✅ 許可
ai-task-manager add "タスク" --due 2025-01-31

# ❌ 不許可（Phase 2 で検討）
ai-task-manager add "タスク" --due 2025/01/31
ai-task-manager add "タスク" --due "Jan 31, 2025"
ai-task-manager add "タスク" --due "明日"
```

### 4.2 時刻の扱い

**決定**: 日付のみ（時刻は管理しない）

```python
# データベース
start_date TEXT  -- YYYY-MM-DD
due_date TEXT    -- YYYY-MM-DD

# Python
from datetime import date  # ✅ date を使用
from datetime import datetime  # ❌ datetime は使わない（日付変換のみ）
```

---

## 5. エラーハンドリング

**決定**: 日本語エラーメッセージ

```python
# ✅ 採用
if not task:
    click.echo("エラー: タスクが見つかりません (ID: {id})")
    sys.exit(1)

# ❌ 不採用
if not task:
    click.echo("Error: Task not found (ID: {id})")
    sys.exit(1)
```

**例外メッセージ一覧**:
- `"タスクが見つかりません"`
- `"無効な日付形式です。YYYY-MM-DD で指定してください"`
- `"親タスクが存在しません"`
- `"データベース接続エラー"`
- `"必須項目が入力されていません"`

---

## 6. テスト方針

**決定**: 標準的なユニットテスト

### テスト対象

```
tests/
├── test_database.py       # データベース操作
├── test_models.py         # データモデル
├── test_tree_view.py      # ツリー表示
├── test_ascii_gantt.py    # ガントチャート
├── test_commands.py       # CLIコマンド
└── test_tags.py           # タグ機能 ⭐ 追加
```

### カバレッジ目標

- **最低**: 60%
- **目標**: 75%
- **理想**: 85%

### テストフレームワーク

```python
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=4.0.0
```

### 実行コマンド

```bash
# すべてのテスト実行
pytest

# カバレッジ付き
pytest --cov=ai_task_manager --cov-report=html

# 特定のテストのみ
pytest tests/test_tags.py -v
```

---

## 7. 依存関係

**決定**: 最小バージョン指定（柔軟性優先）

### requirements.txt

```
click>=8.0.0
jinja2>=3.0.0
python-dateutil>=2.8.0
```

### requirements-dev.txt（開発用）

```
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

### Python バージョン

```python
# setup.py
python_requires='>=3.8'
```

**サポート対象**:
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

---

## 8. Claude Code 連携

### Phase 1: 標準出力のみ

```bash
# 人間が読みやすい形式
ai-task-manager list
```

### Phase 2: JSON 出力追加（予定）

```bash
# Claude Code がパースしやすい形式
ai-task-manager list --json

# 出力例
{
  "tasks": [
    {
      "id": 1,
      "title": "タスク1",
      "category": "Work",
      "tags": ["urgent", "client-a"],
      "status": "in_progress",
      "progress": 50
    }
  ]
}
```

### Claude Code からの操作例

```python
import subprocess
import json

# タスク追加
subprocess.run([
    'ai-task-manager', 'add', 'レポート作成',
    '--category', 'Work',
    '--tags', 'urgent,report',
    '--due', '2025-01-31'
])

# タスク一覧取得（Phase 2）
result = subprocess.run(
    ['ai-task-manager', 'list', '--json'],
    capture_output=True,
    text=True
)
tasks = json.loads(result.stdout)
```

---

## 9. 設定ファイル（Phase 3）

Phase 3 で以下の設定ファイルをサポート予定:

```yaml
# ~/.ai_task_manager/config.yaml（または ./config.yaml）
default_category: Work
default_priority: medium
gantt_width: 100
date_format: "%Y-%m-%d"
language: ja
theme: default  # or dark, light
```

Phase 1 では設定ファイルなし（コマンドライン引数のみ）

---

## 10. ドキュメント言語

**決定**: 日本語

### 対象

- ✅ README.md: 日本語
- ✅ ドキュメント (docs/): 日本語
- ✅ コメント: 日本語
- ✅ エラーメッセージ: 日本語
- ✅ CLI ヘルプ: 日本語

### コード内コメント例

```python
def generate_tree_view(tasks: List[Task]) -> str:
    """
    タスクツリーを生成

    Args:
        tasks: タスクのリスト

    Returns:
        ツリー表示の文字列
    """
    # ルートタスクのみを抽出
    root_tasks = [t for t in tasks if t.parent_id is None]

    # ツリーを再帰的に構築
    return build_tree(root_tasks, tasks, indent=0)
```

---

## Phase 1 実装チェックリスト

実装時にこのチェックリストを使用してください：

### データベース

- [ ] `./data/` ディレクトリの自動作成
- [ ] tasks テーブルの作成
- [ ] tags テーブルの作成 ⭐
- [ ] task_tags テーブルの作成 ⭐
- [ ] 必要なインデックスの作成

### データモデル

- [ ] Task クラスの実装
- [ ] Tag クラスの実装 ⭐
- [ ] `Task.tags` プロパティの追加 ⭐
- [ ] `is_overdue` プロパティ
- [ ] `from_db_row` クラスメソッド

### CLI コマンド

- [ ] `add` コマンド（`--tags` オプション追加）⭐
- [ ] `list` コマンド（`--tags` フィルタ追加）⭐
- [ ] `update` コマンド（`--add-tags`, `--remove-tags`）⭐
- [ ] `delete` コマンド
- [ ] `tree` コマンド（タグ表示対応）⭐
- [ ] `gantt` コマンド
- [ ] `tags` コマンド（タグ一覧）⭐

### 視覚化

- [ ] ツリー表示（タグ表示対応）⭐
- [ ] ASCII ガントチャート
- [ ] 日本語エラーメッセージ

### テスト

- [ ] データベース操作のテスト
- [ ] タグ機能のテスト ⭐
- [ ] ツリー表示のテスト
- [ ] ガントチャートのテスト
- [ ] カバレッジ 60% 以上

---

## 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-01-16 | 初版作成 |

---

## 注意事項

### ⭐ マークの項目

これらは元の仕様書に含まれていない追加要件です：

1. **データベースパスの変更**: `~/.ai_task_manager/` → `./data/`
2. **タグ機能の Phase 1 実装**: 元々は Phase 3 の予定

### ドキュメント更新が必要な箇所

以下のドキュメントを更新する必要があります：

1. **TASK_VISUALIZATION_SPEC.md**
   - データベーススキーマにタグテーブル追加
   - DB_PATH の変更

2. **IMPLEMENTATION_GUIDE.md**
   - Phase 1 にタグ機能の実装手順追加
   - 実装時間を 5時間 → 6時間 に更新

3. **API_REFERENCE.md**
   - Tag モデルの追加
   - タグ関連コマンドの追加

これらの更新を実装前に行いますか？
