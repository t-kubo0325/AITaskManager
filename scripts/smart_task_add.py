#!/usr/bin/env python3
"""タスクを分析して自動的に親子構造で登録"""
import subprocess
import json
import sys
import os
import argparse
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# スクリプトのディレクトリからプロジェクトルートを取得
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# PYTHONPATHにプロジェクトルートを追加
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_cli_command(args):
    """CLIコマンドを実行"""
    cmd = ['python3', '-m', 'ai_task_manager.cli'] + args

    # 環境変数にPYTHONPATHを追加
    env = os.environ.copy()
    pythonpath = env.get('PYTHONPATH', '')
    if pythonpath:
        env['PYTHONPATH'] = f"{PROJECT_ROOT}:{pythonpath}"
    else:
        env['PYTHONPATH'] = str(PROJECT_ROOT)

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result


def analyze_task_complexity(title: str, description: str = "", due_date: Optional[str] = None) -> Dict:
    """タスクの複雑度を分析

    Returns:
        Dict: {
            'complexity_score': int (0-100),
            'should_split': bool,
            'reasons': List[str],
            'suggested_subtasks': List[str]
        }
    """
    score = 0
    reasons = []
    suggested_subtasks = []

    # 1. タイトルの長さチェック
    if len(title) > 30:
        score += 15
        reasons.append("タイトルが長い（30文字以上）")

    # 2. 複雑さを示すキーワードチェック
    complex_keywords = [
        'プロジェクト', '開発', '実装', '構築', 'システム',
        'アプリ', 'サービス', 'プラットフォーム', '機能追加',
        'リファクタリング', '移行', 'アップグレード', '統合',
        'フェーズ', 'Phase', 'ステージ', 'Stage'
    ]

    for keyword in complex_keywords:
        if keyword in title or keyword in description:
            score += 20
            reasons.append(f"複雑なキーワード「{keyword}」を含む")
            break

    # 3. 複数ステップを示すキーワード
    multi_step_keywords = ['から', 'まで', 'および', 'と', '、', '・', '及び']
    multi_step_count = sum(1 for keyword in multi_step_keywords if keyword in title)
    if multi_step_count >= 2:
        score += 15
        reasons.append(f"複数のステップを示す表現を含む（{multi_step_count}箇所）")

    # 4. 期限の長さチェック
    if due_date:
        try:
            due = date.fromisoformat(due_date)
            days_until_due = (due - date.today()).days

            if days_until_due > 14:  # 2週間以上
                score += 20
                reasons.append(f"期限まで{days_until_due}日（2週間以上）")
            elif days_until_due > 7:  # 1週間以上
                score += 10
                reasons.append(f"期限まで{days_until_due}日（1週間以上）")
        except ValueError:
            pass

    # 5. 説明文の長さチェック
    if len(description) > 100:
        score += 10
        reasons.append("詳細な説明がある（100文字以上）")

    # 分割推奨の判定（スコア40以上）
    should_split = score >= 40

    # サブタスク提案の生成
    if should_split:
        suggested_subtasks = generate_suggested_subtasks(title, description, due_date)

    return {
        'complexity_score': min(score, 100),
        'should_split': should_split,
        'reasons': reasons,
        'suggested_subtasks': suggested_subtasks
    }


def generate_suggested_subtasks(title: str, description: str, due_date: Optional[str]) -> List[str]:
    """推奨されるサブタスクを生成

    一般的なプロジェクトフェーズに基づいて提案
    """
    subtasks = []

    # タイトルから推測されるタスクタイプ
    if any(kw in title for kw in ['開発', '実装', 'システム', 'アプリ', '機能']):
        # 開発系タスク
        subtasks = [
            f"{title} - 要件定義",
            f"{title} - 設計",
            f"{title} - 実装",
            f"{title} - テスト",
            f"{title} - レビュー・修正"
        ]
    elif any(kw in title for kw in ['プロジェクト', '企画']):
        # プロジェクト系タスク
        subtasks = [
            f"{title} - 計画立案",
            f"{title} - リソース確保",
            f"{title} - 実行",
            f"{title} - 進捗確認",
            f"{title} - 完了報告"
        ]
    elif any(kw in title for kw in ['調査', '研究', 'リサーチ']):
        # 調査系タスク
        subtasks = [
            f"{title} - 情報収集",
            f"{title} - 分析",
            f"{title} - レポート作成"
        ]
    elif any(kw in title for kw in ['移行', 'アップグレード', 'リファクタリング']):
        # 移行系タスク
        subtasks = [
            f"{title} - 現状調査",
            f"{title} - 移行計画",
            f"{title} - テスト環境での検証",
            f"{title} - 本番環境への適用",
            f"{title} - 動作確認"
        ]
    else:
        # 一般的なタスク
        subtasks = [
            f"{title} - 準備",
            f"{title} - 実行",
            f"{title} - 確認・完了"
        ]

    return subtasks


def calculate_subtask_deadlines(parent_due_date: str, num_subtasks: int) -> List[str]:
    """サブタスクの期限を計算

    親タスクの期限を均等に分割
    """
    if not parent_due_date:
        return [None] * num_subtasks

    try:
        due = date.fromisoformat(parent_due_date)
        today = date.today()
        total_days = (due - today).days

        if total_days <= 0:
            return [parent_due_date] * num_subtasks

        # サブタスクごとの日数を計算
        days_per_subtask = total_days / num_subtasks

        deadlines = []
        for i in range(num_subtasks):
            # 最後のサブタスクは親タスクと同じ期限
            if i == num_subtasks - 1:
                deadlines.append(parent_due_date)
            else:
                subtask_due = today + timedelta(days=int(days_per_subtask * (i + 1)))
                deadlines.append(subtask_due.isoformat())

        return deadlines
    except ValueError:
        return [None] * num_subtasks


def create_task_with_subtasks(
    title: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    description: str = "",
    subtasks: Optional[List[str]] = None,
    auto_confirm: bool = False
) -> Dict:
    """親タスクとサブタスクを作成

    Returns:
        Dict: {
            'parent_task_id': int,
            'subtask_ids': List[int],
            'success': bool
        }
    """
    print("=" * 80)
    print("🎯 スマートタスク登録")
    print("=" * 80)
    print()

    # 1. タスク複雑度の分析
    print("📊 タスクを分析中...")
    analysis = analyze_task_complexity(title, description, due_date)

    print(f"\n複雑度スコア: {analysis['complexity_score']}/100")
    if analysis['reasons']:
        print("\n分析結果:")
        for reason in analysis['reasons']:
            print(f"  • {reason}")

    # 2. 分割の必要性を判定
    if not analysis['should_split'] and not subtasks:
        print("\n✅ このタスクは単一タスクとして登録するのが適切です")
        print("\n親タスクを登録中...")

        # 単一タスクとして登録
        args = ['add', title]
        if category:
            args.extend(['--category', category])
        if priority:
            args.extend(['--priority', priority])
        if due_date:
            args.extend(['--due', due_date])
        if description:
            args.extend(['--description', description])

        result = run_cli_command(args)

        if result.returncode == 0:
            print("✅ タスクを登録しました")
            # タスクIDを抽出（出力から）
            import re
            match = re.search(r'ID:\s*(\d+)', result.stdout)
            task_id = int(match.group(1)) if match else None

            return {
                'parent_task_id': task_id,
                'subtask_ids': [],
                'success': True
            }
        else:
            print(f"❌ エラー: {result.stderr}")
            return {'success': False}

    # 3. サブタスクへの分割を提案
    print("\n💡 このタスクはサブタスクに分割することをお勧めします")

    if not subtasks:
        subtasks = analysis['suggested_subtasks']

    print(f"\n推奨されるサブタスク ({len(subtasks)}件):")
    for i, subtask in enumerate(subtasks, 1):
        print(f"  {i}. {subtask}")

    # 期限の配分を表示
    if due_date:
        subtask_deadlines = calculate_subtask_deadlines(due_date, len(subtasks))
        print(f"\n期限の配分:")
        for i, (subtask, deadline) in enumerate(zip(subtasks, subtask_deadlines), 1):
            if deadline:
                print(f"  {i}. {deadline} - {subtask}")
    else:
        subtask_deadlines = [None] * len(subtasks)

    # 確認
    if not auto_confirm:
        print("\nこの内容で登録しますか？ [y/N/edit]: ", end='')
        response = input().strip().lower()

        if response == 'edit':
            print("\nサブタスクを編集してください（空行で終了）:")
            subtasks = []
            i = 1
            while True:
                subtask = input(f"  {i}. ").strip()
                if not subtask:
                    break
                subtasks.append(subtask)
                i += 1

            if not subtasks:
                print("❌ サブタスクが指定されませんでした")
                return {'success': False}

            # 期限を再計算
            subtask_deadlines = calculate_subtask_deadlines(due_date, len(subtasks))
        elif response != 'y':
            print("❌ キャンセルしました")
            return {'success': False}

    # 4. 親タスクを作成
    print("\n親タスクを作成中...")
    args = ['add', title]
    if category:
        args.extend(['--category', category])
    if priority:
        args.extend(['--priority', priority])
    if due_date:
        args.extend(['--due', due_date])
    if description:
        args.extend(['--description', description])

    result = run_cli_command(args)

    if result.returncode != 0:
        print(f"❌ エラー: 親タスクの作成に失敗しました")
        print(result.stderr)
        return {'success': False}

    # 親タスクIDを取得
    import re
    match = re.search(r'ID:\s*(\d+)', result.stdout)
    if not match:
        print("❌ エラー: 親タスクIDの取得に失敗しました")
        return {'success': False}

    parent_id = int(match.group(1))
    print(f"✅ 親タスクを作成しました (ID: {parent_id})")

    # 5. サブタスクを作成
    print(f"\nサブタスクを作成中...")
    subtask_ids = []

    for i, (subtask_title, subtask_due) in enumerate(zip(subtasks, subtask_deadlines), 1):
        args = ['add', subtask_title, '--parent', str(parent_id)]
        if category:
            args.extend(['--category', category])
        if priority:
            # サブタスクの優先度は親タスクより1段階下げる（任意）
            args.extend(['--priority', priority])
        if subtask_due:
            args.extend(['--due', subtask_due])

        result = run_cli_command(args)

        if result.returncode == 0:
            match = re.search(r'ID:\s*(\d+)', result.stdout)
            if match:
                subtask_id = int(match.group(1))
                subtask_ids.append(subtask_id)
                print(f"  ✅ {i}/{len(subtasks)}: {subtask_title} (ID: {subtask_id})")
        else:
            print(f"  ❌ {i}/{len(subtasks)}: {subtask_title} - 失敗")

    print()
    print("=" * 80)
    print("✅ タスクの登録が完了しました")
    print("=" * 80)
    print(f"\n親タスク ID: {parent_id}")
    print(f"サブタスク: {len(subtask_ids)}件")
    print("\nツリー表示で確認できます:")
    print(f"  ai-task-manager tree --task-id {parent_id}")
    print()

    return {
        'parent_task_id': parent_id,
        'subtask_ids': subtask_ids,
        'success': True
    }


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='タスクを分析して自動的に親子構造で登録',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # インタラクティブモード
  python3 scripts/smart_task_add.py

  # コマンドライン引数で指定
  python3 scripts/smart_task_add.py \\
    --title "Webアプリ開発" \\
    --category Work \\
    --priority high \\
    --due 2026-02-28 \\
    --description "新しいWebアプリケーションを開発する"

  # サブタスクを手動指定
  python3 scripts/smart_task_add.py \\
    --title "プロジェクトA" \\
    --subtasks "要件定義" "設計" "実装" "テスト"
        """
    )

    parser.add_argument('--title', help='タスクのタイトル')
    parser.add_argument('--category', help='カテゴリ')
    parser.add_argument('--priority', choices=['low', 'medium', 'high'], help='優先度')
    parser.add_argument('--due', '--due-date', dest='due_date', help='期限 (YYYY-MM-DD)')
    parser.add_argument('--description', help='説明')
    parser.add_argument('--subtasks', nargs='+', help='サブタスクのリスト')
    parser.add_argument('--yes', '-y', action='store_true', help='確認なしで実行')

    args = parser.parse_args()

    # インタラクティブモード
    if not args.title:
        print("=" * 80)
        print("🎯 スマートタスク登録（インタラクティブモード）")
        print("=" * 80)
        print()

        title = input("タスクのタイトル: ").strip()
        if not title:
            print("❌ タイトルは必須です")
            sys.exit(1)

        category = input("カテゴリ (省略可): ").strip() or None

        priority_input = input("優先度 [low/medium/high] (省略可): ").strip().lower()
        priority = priority_input if priority_input in ['low', 'medium', 'high'] else None

        due_date = input("期限 (YYYY-MM-DD, 省略可): ").strip() or None
        description = input("説明 (省略可): ").strip() or ""

        # サブタスクの手動指定
        print("\nサブタスクを手動で指定しますか？ [y/N]: ", end='')
        if input().strip().lower() == 'y':
            print("サブタスクを入力してください（空行で終了）:")
            subtasks = []
            i = 1
            while True:
                subtask = input(f"  {i}. ").strip()
                if not subtask:
                    break
                subtasks.append(subtask)
                i += 1
        else:
            subtasks = None
    else:
        title = args.title
        category = args.category
        priority = args.priority
        due_date = args.due_date
        description = args.description or ""
        subtasks = args.subtasks

    # タスク作成
    result = create_task_with_subtasks(
        title=title,
        category=category,
        priority=priority,
        due_date=due_date,
        description=description,
        subtasks=subtasks,
        auto_confirm=args.yes if hasattr(args, 'yes') else False
    )

    if result['success']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
