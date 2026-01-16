#!/usr/bin/env python3
"""期限が近いタスクをチェックして通知"""
import subprocess
import json
import sys
from datetime import date, timedelta


def run_cli_command(args):
    """CLIコマンドを実行"""
    cmd = ['python3', '-m', 'ai_task_manager.cli'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def deadline_check(warning_days=3):
    """期限が近いタスクをチェック

    Args:
        warning_days: 警告する日数（デフォルト: 3日）
    """
    print("=" * 80)
    print("⏰ 期限チェックを開始します")
    print("=" * 80)
    print()

    # タスクデータを取得
    result = run_cli_command(['list', '--json'])

    if result.returncode != 0:
        print("❌ エラー: タスクの取得に失敗しました")
        sys.exit(1)

    tasks = json.loads(result.stdout)
    today = date.today()
    deadline_range = today + timedelta(days=warning_days)

    # 未完了タスクのみをフィルタ
    active_tasks = [
        t for t in tasks
        if t['status'] not in ['completed', 'cancelled']
    ]

    # 期限が近いタスクを抽出
    upcoming_tasks = []
    for task in active_tasks:
        if task.get('due_date'):
            due = date.fromisoformat(task['due_date'])
            if today <= due <= deadline_range:
                days_left = (due - today).days
                upcoming_tasks.append((task, days_left))

    # 期限順にソート
    upcoming_tasks.sort(key=lambda x: x[1])

    # 表示
    if upcoming_tasks:
        print(f"⚠️  {len(upcoming_tasks)}件のタスクが{warning_days}日以内に期限です:\n")

        for task, days in upcoming_tasks:
            # 緊急度に応じて絵文字を変更
            if days == 0:
                urgency = "🔴 【本日】"
            elif days == 1:
                urgency = "🟡 【明日】"
            else:
                urgency = f"🟢 【あと{days}日】"

            print(f"{urgency} {task['title']}")
            print(f"     ID: {task['id']} | 期限: {task['due_date']}")
            print(f"     優先度: {task['priority']} | 進捗: {task['progress']}%")
            print(f"     カテゴリ: {task.get('category', 'なし')}")

            if task.get('tags'):
                print(f"     タグ: {', '.join(task['tags'])}")

            # 進捗状況に応じて警告
            if task['progress'] < 50 and days <= 1:
                print(f"     ⚠️ 注意: 進捗が{task['progress']}%で期限が迫っています！")

            print()
    else:
        print(f"✅ 今後{warning_days}日間に期限のタスクはありません\n")

    # 今日期限のタスクがあれば特別な警告
    today_tasks = [t for t, d in upcoming_tasks if d == 0]
    if today_tasks:
        print("=" * 80)
        print(f"🚨 重要: 本日期限のタスクが{len(today_tasks)}件あります！")
        print("=" * 80)

    print()
    print("=" * 80)
    print("✅ 期限チェックが完了しました")
    print("=" * 80)


if __name__ == '__main__':
    import sys
    # コマンドライン引数で警告日数を指定可能
    warning_days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    deadline_check(warning_days)
