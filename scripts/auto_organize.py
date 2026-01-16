#!/usr/bin/env python3
"""タスクの自動整理"""
import subprocess
import json
import sys
from datetime import date, timedelta


def run_cli_command(args):
    """CLIコマンドを実行"""
    cmd = ['python3', '-m', 'ai_task_manager.cli'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def auto_organize():
    """タスクを自動整理"""
    print("=" * 80)
    print("🔧 タスクの自動整理を開始します")
    print("=" * 80)
    print()

    # タスクデータを取得
    result = run_cli_command(['list', '--json'])

    if result.returncode != 0:
        print("❌ エラー: タスクの取得に失敗しました")
        sys.exit(1)

    tasks = json.loads(result.stdout)
    today = date.today()

    # 統計カウンター
    stats = {
        'overdue_tagged': 0,
        'urgent_tagged': 0,
        'archived_tagged': 0
    }

    # 1. 期限超過タスクに「overdue」タグを追加
    print("📌 期限超過タスクの処理...")
    for task in tasks:
        if task.get('due_date') and task['status'] not in ['completed', 'cancelled']:
            due = date.fromisoformat(task['due_date'])
            if due < today:
                current_tags = task.get('tags', [])
                if 'overdue' not in current_tags:
                    result = run_cli_command([
                        'update', str(task['id']),
                        '--add-tags', 'overdue'
                    ])
                    if result.returncode == 0:
                        stats['overdue_tagged'] += 1
                        print(f"  ✅ タスク {task['id']}: {task['title']} に「overdue」タグを追加")

    # 2. 期限が3日以内のタスクに「urgent」タグを追加
    print("\n⚡ 緊急タスクの処理...")
    urgent_deadline = today + timedelta(days=3)

    for task in tasks:
        if task.get('due_date') and task['status'] not in ['completed', 'cancelled']:
            due = date.fromisoformat(task['due_date'])
            if today <= due <= urgent_deadline:
                current_tags = task.get('tags', [])
                if 'urgent' not in current_tags:
                    result = run_cli_command([
                        'update', str(task['id']),
                        '--add-tags', 'urgent'
                    ])
                    if result.returncode == 0:
                        stats['urgent_tagged'] += 1
                        print(f"  ✅ タスク {task['id']}: {task['title']} に「urgent」タグを追加")

    # 3. 完了済みで30日以上経過したタスクに「archived」タグを追加
    print("\n📦 アーカイブ処理...")
    archive_date = today - timedelta(days=30)

    for task in tasks:
        if task['status'] == 'completed' and task.get('completed_date'):
            completed = date.fromisoformat(task['completed_date'])
            if completed < archive_date:
                current_tags = task.get('tags', [])
                if 'archived' not in current_tags:
                    result = run_cli_command([
                        'update', str(task['id']),
                        '--add-tags', 'archived'
                    ])
                    if result.returncode == 0:
                        stats['archived_tagged'] += 1
                        print(f"  ✅ タスク {task['id']}: {task['title']} に「archived」タグを追加")

    # 4. 「overdue」タグがあるが期限を過ぎていないタスクからタグを削除
    print("\n🗑️  不要なタグのクリーンアップ...")
    cleaned_count = 0

    for task in tasks:
        current_tags = task.get('tags', [])

        # 期限超過タグのクリーンアップ
        if 'overdue' in current_tags:
            should_remove = False

            if task['status'] in ['completed', 'cancelled']:
                should_remove = True
            elif task.get('due_date'):
                due = date.fromisoformat(task['due_date'])
                if due >= today:
                    should_remove = True

            if should_remove:
                result = run_cli_command([
                    'update', str(task['id']),
                    '--remove-tags', 'overdue'
                ])
                if result.returncode == 0:
                    cleaned_count += 1
                    print(f"  ✅ タスク {task['id']}: {task['title']} から「overdue」タグを削除")

        # 緊急タグのクリーンアップ
        if 'urgent' in current_tags:
            should_remove = False

            if task['status'] in ['completed', 'cancelled']:
                should_remove = True
            elif task.get('due_date'):
                due = date.fromisoformat(task['due_date'])
                if due > urgent_deadline or due < today:
                    should_remove = True

            if should_remove:
                result = run_cli_command([
                    'update', str(task['id']),
                    '--remove-tags', 'urgent'
                ])
                if result.returncode == 0:
                    cleaned_count += 1
                    print(f"  ✅ タスク {task['id']}: {task['title']} から「urgent」タグを削除")

    # サマリー表示
    print("\n" + "=" * 80)
    print("📊 整理結果サマリー")
    print("=" * 80)
    print(f"  期限超過タグ追加   : {stats['overdue_tagged']} 件")
    print(f"  緊急タグ追加       : {stats['urgent_tagged']} 件")
    print(f"  アーカイブタグ追加 : {stats['archived_tagged']} 件")
    print(f"  不要なタグ削除     : {cleaned_count} 件")
    print()
    print("=" * 80)
    print("✅ タスクの自動整理が完了しました")
    print("=" * 80)


if __name__ == '__main__':
    auto_organize()
