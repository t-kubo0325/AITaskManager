# Phase 4: Claude Skills機能 実装仕様

**優先度**: 中（元々の要件）
**実装時間**: 3-4時間
**実装予定**: Phase 2, 3 完了後

---

## 概要

Claude Codeが自動でタスク管理を実行できるようにする機能を実装します。これにより、ユーザーはタスク管理をAIに一任できます。

---

## 実装内容

### 1. Claude Skills定義ファイル

**ファイルパス**: `.claude/skills/task-manager/skill.json`

```json
{
  "name": "task-manager",
  "description": "AI Task Managerを使用してタスクを管理",
  "version": "1.0.0",
  "commands": {
    "daily-review": {
      "description": "毎日のタスク確認と整理",
      "script": "scripts/daily_review.py"
    },
    "deadline-check": {
      "description": "期限が近いタスクをチェック",
      "script": "scripts/deadline_check.py"
    },
    "progress-report": {
      "description": "プロジェクトの進捗レポート生成",
      "script": "scripts/progress_report.py"
    },
    "auto-organize": {
      "description": "タスクの自動整理",
      "script": "scripts/auto_organize.py"
    }
  },
  "schedule": {
    "daily-review": "0 9 * * *",
    "deadline-check": "0 9,17 * * *"
  }
}
```

---

### 2. 自動タスク管理スクリプト

#### 2.1 毎日のタスク確認（daily_review.py）

```python
#!/usr/bin/env python3
"""毎日のタスク確認と整理"""
import subprocess
import json
from datetime import date, timedelta

def daily_review():
    """毎日のタスクレビュー"""
    print("🔍 今日のタスク確認を開始します...\n")

    # 1. 今日期限のタスクを表示
    today = date.today()
    result = subprocess.run(
        ['python3', '-m', 'ai_task_manager.cli', 'list', '--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        tasks = json.loads(result.stdout)
        today_tasks = [t for t in tasks if t.get('due_date') == str(today)]

        if today_tasks:
            print(f"⚠️  今日期限のタスク: {len(today_tasks)}件")
            for task in today_tasks:
                print(f"  - {task['title']} (ID: {task['id']})")
        else:
            print("✅ 今日期限のタスクはありません")

    # 2. 期限超過タスクを確認
    print("\n🚨 期限超過タスクのチェック...")
    # 実装省略

    # 3. 進行中タスクの確認
    print("\n📋 進行中のタスク...")
    subprocess.run([
        'python3', '-m', 'ai_task_manager.cli',
        'list', '--status', 'in_progress'
    ])

    print("\n✅ 毎日のタスク確認が完了しました")

if __name__ == '__main__':
    daily_review()
```

#### 2.2 期限チェック（deadline_check.py）

```python
#!/usr/bin/env python3
"""期限が近いタスクをチェックして通知"""
import subprocess
import json
from datetime import date, timedelta

def deadline_check():
    """期限が近いタスクをチェック"""
    print("⏰ 期限チェックを開始します...\n")

    # 今後3日間の期限を確認
    today = date.today()
    deadline_range = today + timedelta(days=3)

    result = subprocess.run(
        ['python3', '-m', 'ai_task_manager.cli', 'list', '--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        tasks = json.loads(result.stdout)
        upcoming_tasks = []

        for task in tasks:
            if task.get('due_date'):
                due = date.fromisoformat(task['due_date'])
                if today <= due <= deadline_range:
                    days_left = (due - today).days
                    upcoming_tasks.append((task, days_left))

        if upcoming_tasks:
            print(f"⚠️  {len(upcoming_tasks)}件のタスクが3日以内に期限です:\n")
            for task, days in sorted(upcoming_tasks, key=lambda x: x[1]):
                urgency = "🔴" if days == 0 else "🟡" if days <= 1 else "🟢"
                print(f"{urgency} {task['title']} - あと{days}日 (ID: {task['id']})")
        else:
            print("✅ 今後3日間に期限のタスクはありません")

if __name__ == '__main__':
    deadline_check()
```

#### 2.3 進捗レポート（progress_report.py）

```python
#!/usr/bin/env python3
"""プロジェクトの進捗レポートを生成"""
import subprocess
import json
from datetime import datetime

def progress_report():
    """進捗レポートを生成"""
    print("📊 プロジェクト進捗レポートを生成します...\n")
    print(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # タスク一覧を取得
    result = subprocess.run(
        ['python3', '-m', 'ai_task_manager.cli', 'list', '--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        tasks = json.loads(result.stdout)

        # カテゴリ別集計
        categories = {}
        for task in tasks:
            cat = task.get('category', 'その他')
            if cat not in categories:
                categories[cat] = {'total': 0, 'completed': 0, 'in_progress': 0}

            categories[cat]['total'] += 1
            if task['status'] == 'completed':
                categories[cat]['completed'] += 1
            elif task['status'] == 'in_progress':
                categories[cat]['in_progress'] += 1

        # レポート出力
        print("=" * 60)
        print("カテゴリ別進捗状況")
        print("=" * 60)
        for cat, stats in categories.items():
            completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"\n{cat}:")
            print(f"  総数: {stats['total']} 件")
            print(f"  完了: {stats['completed']} 件 ({completion_rate:.1f}%)")
            print(f"  進行中: {stats['in_progress']} 件")

        print("\n" + "=" * 60)

        # ツリー表示
        print("\nタスク階層:")
        subprocess.run(['python3', '-m', 'ai_task_manager.cli', 'tree'])

if __name__ == '__main__':
    progress_report()
```

#### 2.4 自動整理（auto_organize.py）

```python
#!/usr/bin/env python3
"""タスクの自動整理"""
import subprocess
import json
from datetime import date

def auto_organize():
    """タスクを自動整理"""
    print("🔧 タスクの自動整理を開始します...\n")

    # 1. 完了済みで古いタスクにタグ付け
    # 2. 期限超過タスクにタグ付け
    # 3. 優先度の自動調整

    result = subprocess.run(
        ['python3', '-m', 'ai_task_manager.cli', 'list', '--json'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        tasks = json.loads(result.stdout)
        today = date.today()

        # 期限超過タスクにタグ追加
        overdue_count = 0
        for task in tasks:
            if task.get('due_date') and task['status'] != 'completed':
                due = date.fromisoformat(task['due_date'])
                if due < today and 'overdue' not in task.get('tags', []):
                    subprocess.run([
                        'python3', '-m', 'ai_task_manager.cli',
                        'update', str(task['id']), '--add-tags', 'overdue'
                    ])
                    overdue_count += 1

        print(f"✅ {overdue_count}件のタスクに期限超過タグを追加しました")

        # 完了済みで30日以上経過したタスクにarchiveタグ
        # 実装省略

if __name__ == '__main__':
    auto_organize()
```

---

### 3. Claude Code連携設定

**ファイル**: `.claude/config.yaml`

```yaml
skills:
  task-manager:
    enabled: true
    auto_run:
      - command: daily-review
        schedule: "0 9 * * *"
      - command: deadline-check
        schedule: "0 9,17 * * *"

aliases:
  tm: "python3 -m ai_task_manager.cli"
  task: "python3 -m ai_task_manager.cli"
```

---

### 4. ユーザーガイド

**ファイル**: `docs/CLAUDE_SKILLS_GUIDE.md`

```markdown
# Claude Skills によるタスク管理

## セットアップ

1. スキルのインストール
```bash
# スキル定義ファイルを配置
cp -r .claude/skills/task-manager ~/.claude/skills/
```

2. Claude Codeでスキルを有効化
```bash
claude skills enable task-manager
```

## 使い方

### 手動実行

```bash
# 毎日のタスク確認
claude run task-manager:daily-review

# 期限チェック
claude run task-manager:deadline-check

# 進捗レポート
claude run task-manager:progress-report
```

### 自動実行

設定ファイルで schedule を指定すると、自動的に実行されます：

- `daily-review`: 毎日 9:00
- `deadline-check`: 毎日 9:00 と 17:00

## Claude Codeに依頼する例

```
"今日のタスクを確認して"
"期限が近いタスクを教えて"
"プロジェクトAの進捗レポートを作成して"
```
```

---

## 実装チェックリスト

- [ ] `.claude/skills/task-manager/skill.json` 作成
- [ ] `scripts/daily_review.py` 実装
- [ ] `scripts/deadline_check.py` 実装
- [ ] `scripts/progress_report.py` 実装
- [ ] `scripts/auto_organize.py` 実装
- [ ] `.claude/config.yaml` 設定
- [ ] `docs/CLAUDE_SKILLS_GUIDE.md` 作成
- [ ] JSON出力モード実装（Phase 2で対応）
- [ ] 動作テスト
- [ ] ユーザードキュメント更新

---

## 依存関係

- Phase 2 の JSON出力モード（`--json` フラグ）が必須
- Claude Code環境

---

## 注意事項

- スクリプトは PYTHONPATH を適切に設定すること
- Claude Code のバージョン互換性を確認すること
- cron式のスケジュール設定は環境により異なる可能性あり
