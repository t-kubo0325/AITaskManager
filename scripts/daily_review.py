#!/usr/bin/env python3
"""毎日のタスク確認と整理"""
import subprocess
import json
import sys
from datetime import date, timedelta
from pathlib import Path


def run_cli_command(args):
    """CLIコマンドを実行"""
    cmd = ['python3', '-m', 'ai_task_manager.cli'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def daily_review():
    """毎日のタスクレビュー"""
    print("=" * 80)
    print("🔍 今日のタスク確認を開始します")
    print("=" * 80)
    print()

    # タスクデータを取得
    result = run_cli_command(['list', '--json'])

    if result.returncode != 0:
        print("❌ エラー: タスクの取得に失敗しました")
        sys.exit(1)

    tasks = json.loads(result.stdout)
    today = date.today()

    # 1. 今日期限のタスク
    print("📅 今日期限のタスク")
    print("-" * 80)
    today_tasks = [t for t in tasks if t.get('due_date') == str(today)]

    if today_tasks:
        print(f"⚠️  {len(today_tasks)}件のタスクが今日期限です:\n")
        for task in today_tasks:
            status_emoji = {'completed': '✅', 'in_progress': '🔄', 'pending': '⏸️', 'cancelled': '🚫'}
            emoji = status_emoji.get(task['status'], '❓')
            print(f"  {emoji} {task['title']}")
            print(f"     ID: {task['id']} | 優先度: {task['priority']} | 進捗: {task['progress']}%")
            if task.get('tags'):
                print(f"     タグ: {', '.join(task['tags'])}")
            print()
    else:
        print("✅ 今日期限のタスクはありません\n")

    # 2. 期限超過タスク
    print("🚨 期限超過タスク")
    print("-" * 80)
    overdue_tasks = [
        t for t in tasks
        if t.get('due_date') and date.fromisoformat(t['due_date']) < today
        and t['status'] not in ['completed', 'cancelled']
    ]

    if overdue_tasks:
        print(f"⚠️  {len(overdue_tasks)}件のタスクが期限超過しています:\n")
        for task in overdue_tasks:
            due = date.fromisoformat(task['due_date'])
            days_overdue = (today - due).days
            print(f"  🔴 {task['title']}")
            print(f"     ID: {task['id']} | 期限: {task['due_date']} ({days_overdue}日超過)")
            print(f"     優先度: {task['priority']} | 進捗: {task['progress']}%")
            print()
    else:
        print("✅ 期限超過のタスクはありません\n")

    # 3. 進行中のタスク
    print("📋 進行中のタスク")
    print("-" * 80)
    in_progress_tasks = [t for t in tasks if t['status'] == 'in_progress']

    if in_progress_tasks:
        print(f"現在 {len(in_progress_tasks)}件のタスクが進行中です:\n")
        for task in in_progress_tasks:
            print(f"  🔄 {task['title']}")
            print(f"     ID: {task['id']} | 進捗: {task['progress']}%")
            if task.get('due_date'):
                due = date.fromisoformat(task['due_date'])
                days_left = (due - today).days
                if days_left >= 0:
                    print(f"     期限: {task['due_date']} (あと{days_left}日)")
                else:
                    print(f"     期限: {task['due_date']} ({abs(days_left)}日超過)")
            print()
    else:
        print("進行中のタスクはありません\n")

    # 4. 統計情報
    print("📊 統計サマリー")
    print("-" * 80)
    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'completed'])
    pending = len([t for t in tasks if t['status'] == 'pending'])
    in_progress = len(in_progress_tasks)

    print(f"総タスク数: {total}件")
    print(f"  完了: {completed}件 ({completed/total*100:.1f}%)" if total > 0 else "  完了: 0件")
    print(f"  進行中: {in_progress}件")
    print(f"  未着手: {pending}件")
    print(f"  期限超過: {len(overdue_tasks)}件")

    print()
    print("=" * 80)
    print("✅ 毎日のタスク確認が完了しました")
    print("=" * 80)


if __name__ == '__main__':
    daily_review()
