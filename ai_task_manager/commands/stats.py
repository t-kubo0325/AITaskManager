"""統計コマンド"""
import click
import json
from ai_task_manager.visualization.statistics import get_all_statistics
from ai_task_manager.utils.errors import handle_error, DatabaseError


def stats_command(category, period, output_json):
    """統計情報を表示"""
    try:
        # 統計データを取得
        stats = get_all_statistics()

        # JSON出力
        if output_json:
            click.echo(json.dumps(stats, ensure_ascii=False, indent=2))
            return

        # CLI表示
        display_statistics(stats, category, period)

    except DatabaseError as e:
        handle_error(e)


def display_statistics(stats: dict, category_filter: str = None, period: str = 'month'):
    """統計情報をCLI表示"""
    overall = stats['overall']
    week_stats = stats['week']
    month_stats = stats['month']
    categories = stats['categories']
    priorities = stats['priorities']
    tags = stats['tags']

    # ヘッダー
    click.echo("\n" + "━" * 80)
    click.echo("📊 AI Task Manager - 統計ダッシュボード")
    click.echo("━" * 80)

    # 全体サマリー
    click.echo("\n📈 全体サマリー")
    click.echo("─" * 80)

    status_counts = overall['status_counts']
    click.echo(f"  総タスク数       : {overall['total_tasks']} 件")
    click.echo(f"  完了タスク       : {status_counts.get('completed', 0)} 件 ({overall['completion_rate']:.1f}%)")
    click.echo(f"  進行中           : {status_counts.get('in_progress', 0)} 件 ({status_counts.get('in_progress', 0) / overall['total_tasks'] * 100:.1f}%)")
    click.echo(f"  未着手           : {status_counts.get('pending', 0)} 件 ({status_counts.get('pending', 0) / overall['total_tasks'] * 100:.1f}%)")

    cancelled = status_counts.get('cancelled', 0)
    if cancelled > 0:
        click.echo(f"  キャンセル       : {cancelled} 件 ({cancelled / overall['total_tasks'] * 100:.1f}%)")

    if overall['overdue_count'] > 0:
        click.echo(f"\n⚠️  期限超過       : {overall['overdue_count']} 件")

    # 今週の進捗
    click.echo("\n📅 今週の進捗")
    click.echo("─" * 80)
    click.echo(f"  新規作成         : {week_stats['created_count']} 件")
    click.echo(f"  完了             : {week_stats['completed_count']} 件")
    if week_stats['created_count'] > 0:
        click.echo(f"  進捗率           : {week_stats['progress_rate']:.1f}%")

    # 今月の進捗
    click.echo("\n📅 今月の進捗")
    click.echo("─" * 80)
    click.echo(f"  新規作成         : {month_stats['created_count']} 件")
    click.echo(f"  完了             : {month_stats['completed_count']} 件")
    if month_stats['created_count'] > 0:
        click.echo(f"  進捗率           : {month_stats['progress_rate']:.1f}%")

    # カテゴリ別統計
    if categories:
        click.echo("\n🏷️  カテゴリ別統計")
        click.echo("─" * 80)

        # カテゴリフィルタ適用
        display_categories = categories
        if category_filter:
            display_categories = [c for c in categories if c['category'] == category_filter]

        for cat in display_categories[:10]:  # 上位10件
            click.echo(f"  {cat['category']:20} : {cat['total']} 件 "
                      f"(完了: {cat['completed']}, 進行中: {cat['in_progress']}, 未着手: {cat['pending']})")

    # 優先度別統計
    if priorities:
        click.echo("\n⭐ 優先度別統計")
        click.echo("─" * 80)

        priority_labels = {'high': '高', 'medium': '中', 'low': '低'}
        for pri in priorities:
            label = priority_labels.get(pri['priority'], pri['priority'])
            click.echo(f"  {label:20} : {pri['total']} 件 "
                      f"(完了: {pri['completed']}, 残り: {pri['remaining']})")

    # タグ別統計
    if tags:
        click.echo("\n🏷️  タグ別統計")
        click.echo("─" * 80)

        for tag in tags[:10]:  # 上位10件
            click.echo(f"  {tag['tag']:20} : {tag['count']} 件")

    click.echo("\n" + "━" * 80 + "\n")
