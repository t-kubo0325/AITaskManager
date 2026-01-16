#!/usr/bin/env python3
"""プロジェクトの進捗レポートを生成"""
import subprocess
import json
import sys
from datetime import datetime, date


def run_cli_command(args):
    """CLIコマンドを実行"""
    cmd = ['python3', '-m', 'ai_task_manager.cli'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def progress_report():
    """進捗レポートを生成"""
    print("=" * 80)
    print("📊 プロジェクト進捗レポート")
    print("=" * 80)
    print(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # タスクデータを取得
    result = run_cli_command(['list', '--json'])

    if result.returncode != 0:
        print("❌ エラー: タスクの取得に失敗しました")
        sys.exit(1)

    tasks = json.loads(result.stdout)
    today = date.today()

    if not tasks:
        print("📭 タスクがありません\n")
        return

    # カテゴリ別集計
    categories = {}
    for task in tasks:
        cat = task.get('category') or 'その他'
        if cat not in categories:
            categories[cat] = {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'cancelled': 0,
                'overdue': 0
            }

        categories[cat]['total'] += 1
        categories[cat][task['status']] += 1

        # 期限超過チェック
        if task.get('due_date') and task['status'] not in ['completed', 'cancelled']:
            due = date.fromisoformat(task['due_date'])
            if due < today:
                categories[cat]['overdue'] += 1

    # カテゴリ別レポート
    print("=" * 80)
    print("📂 カテゴリ別進捗状況")
    print("=" * 80)

    for cat in sorted(categories.keys()):
        stats = categories[cat]
        completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0

        print(f"\n【{cat}】")
        print(f"  総タスク数   : {stats['total']} 件")
        print(f"  完了         : {stats['completed']} 件 ({completion_rate:.1f}%)")
        print(f"  進行中       : {stats['in_progress']} 件")
        print(f"  未着手       : {stats['pending']} 件")

        if stats['cancelled'] > 0:
            print(f"  キャンセル   : {stats['cancelled']} 件")

        if stats['overdue'] > 0:
            print(f"  ⚠️ 期限超過  : {stats['overdue']} 件")

    # 優先度別集計
    print("\n" + "=" * 80)
    print("⭐ 優先度別統計")
    print("=" * 80)

    priority_stats = {'high': 0, 'medium': 0, 'low': 0}
    priority_completed = {'high': 0, 'medium': 0, 'low': 0}

    for task in tasks:
        priority = task.get('priority', 'medium')
        priority_stats[priority] += 1
        if task['status'] == 'completed':
            priority_completed[priority] += 1

    for priority in ['high', 'medium', 'low']:
        label = {'high': '高', 'medium': '中', 'low': '低'}[priority]
        total = priority_stats[priority]
        completed = priority_completed[priority]
        rate = (completed / total * 100) if total > 0 else 0
        print(f"\n{label}優先度: {total} 件 (完了: {completed} 件, {rate:.1f}%)")

    # 全体統計
    print("\n" + "=" * 80)
    print("📈 全体統計")
    print("=" * 80)

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'completed'])
    in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
    pending = len([t for t in tasks if t['status'] == 'pending'])
    overdue = len([
        t for t in tasks
        if t.get('due_date') and date.fromisoformat(t['due_date']) < today
        and t['status'] not in ['completed', 'cancelled']
    ])

    print(f"\n総タスク数: {total} 件")
    print(f"  完了       : {completed} 件 ({completed/total*100:.1f}%)" if total > 0 else "  完了: 0件")
    print(f"  進行中     : {in_progress} 件")
    print(f"  未着手     : {pending} 件")
    if overdue > 0:
        print(f"  ⚠️ 期限超過: {overdue} 件")

    # タスク階層表示
    print("\n" + "=" * 80)
    print("🌳 タスク階層")
    print("=" * 80)
    print()
    subprocess.run(['python3', '-m', 'ai_task_manager.cli', 'tree'])

    print("\n" + "=" * 80)
    print("✅ 進捗レポートの生成が完了しました")
    print("=" * 80)


if __name__ == '__main__':
    progress_report()
