"""ダッシュボードコマンド"""
import click
from pathlib import Path
from jinja2 import Template
from ai_task_manager.visualization.statistics import get_all_statistics
from ai_task_manager.utils.errors import handle_error, DatabaseError


def dashboard_command(output, open_browser):
    """HTMLダッシュボードを生成"""
    try:
        # 統計データを取得
        stats = get_all_statistics()

        # カテゴリデータを準備
        category_labels = [c['category'] for c in stats['categories'][:10]]
        category_completed = [c['completed'] for c in stats['categories'][:10]]
        category_in_progress = [c['in_progress'] for c in stats['categories'][:10]]
        category_pending = [c['pending'] for c in stats['categories'][:10]]

        # タグデータを準備
        tag_labels = [t['tag'] for t in stats['tags'][:10]]
        tag_counts = [t['count'] for t in stats['tags'][:10]]

        # テンプレートを読み込み
        template_path = Path(__file__).parent.parent / 'visualization' / 'templates' / 'dashboard.html'
        template = Template(template_path.read_text(encoding='utf-8'))

        # HTMLを生成
        html_content = template.render(
            stats=stats,
            category_labels=category_labels,
            category_completed=category_completed,
            category_in_progress=category_in_progress,
            category_pending=category_pending,
            tag_labels=tag_labels,
            tag_counts=tag_counts
        )

        # ファイルに書き込み
        output_path = Path(output or 'dashboard.html').expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')

        click.echo(f"✅ ダッシュボードを生成しました: {output_path}")

        # ブラウザで開く
        if open_browser:
            from ai_task_manager.commands.gantt import open_in_browser
            open_in_browser(str(output_path))
            click.echo("ブラウザで開きました")

    except (DatabaseError, IOError) as e:
        handle_error(e)
