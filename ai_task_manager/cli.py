"""CLIエントリーポイント"""
import click
from ai_task_manager.database import init_db


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """AI Task Manager - Claude Code対応タスク管理ツール"""
    init_db()


@cli.command()
@click.argument('title')
@click.option('--description', '-d', help='タスクの説明')
@click.option('--category', '-c', help='カテゴリ')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), default='medium', help='優先度')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--parent', type=int, help='親タスクID')
@click.option('--tags', help='タグ（カンマ区切り）')
def add(title, description, category, priority, start, due, parent, tags):
    """新しいタスクを追加"""
    from ai_task_manager.commands.add import add_task
    add_task(title, description, category, priority, start, due, parent, tags)


@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
@click.option('--tags', help='タグでフィルタ（カンマ区切り）')
@click.option('--json', 'output_json', is_flag=True, help='JSON形式で出力')
def list(category, status, priority, tags, output_json):
    """タスク一覧を表示"""
    from ai_task_manager.commands.list import list_tasks
    list_tasks(category, status, priority, tags, output_json)


@cli.command()
@click.argument('task_id', type=int)
@click.option('--title', help='タスク名')
@click.option('--description', '-d', help='説明')
@click.option('--category', '-c', help='カテゴリ')
@click.option('--priority', '-p', type=click.Choice(['low', 'medium', 'high']), help='優先度')
@click.option('--status', '-s', type=click.Choice(['pending', 'in_progress', 'completed', 'cancelled']), help='ステータス')
@click.option('--progress', type=int, help='進捗率 (0-100)')
@click.option('--start', help='開始日 (YYYY-MM-DD)')
@click.option('--due', help='期限 (YYYY-MM-DD)')
@click.option('--add-tags', help='追加するタグ（カンマ区切り）')
@click.option('--remove-tags', help='削除するタグ（カンマ区切り）')
def update(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags):
    """タスクを更新"""
    from ai_task_manager.commands.update import update_task
    update_task(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags)


@cli.command()
@click.argument('task_id', type=int)
@click.option('--force', '-f', is_flag=True, help='確認なしで削除')
def delete(task_id, force):
    """タスクを削除"""
    from ai_task_manager.commands.delete import delete_task
    delete_task(task_id, force)


@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--tags', help='タグでフィルタ（カンマ区切り）')
def tree(category, status, tags):
    """タスクをツリー形式で表示"""
    from ai_task_manager.commands.tree import tree_command
    tree_command(category, status, tags)


@cli.command()
@click.option('--range', 'range_str', help='表示範囲 (YYYY-MM)')
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
@click.option('--width', default=80, help='チャート幅')
@click.option('--html', is_flag=True, help='HTML形式で出力')
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--open', 'open_browser', is_flag=True, help='生成後にブラウザで開く')
def gantt(range_str, category, status, priority, width, html, output, open_browser):
    """ASCIIガントチャートを表示"""
    from ai_task_manager.commands.gantt import gantt_command
    gantt_command(range_str, category, status, priority, width, html, output, open_browser)


@cli.command()
def tags():
    """タグ一覧を表示"""
    from ai_task_manager.commands.tags import tags_command
    tags_command()


@cli.command()
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--period', type=click.Choice(['week', 'month', 'year']), default='month', help='期間指定')
@click.option('--json', 'output_json', is_flag=True, help='JSON形式で出力')
def stats(category, period, output_json):
    """統計情報を表示"""
    from ai_task_manager.commands.stats import stats_command
    stats_command(category, period, output_json)


@cli.group()
def export():
    """データをエクスポート"""
    pass


@export.command('csv')
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--category', '-c', help='カテゴリでフィルタ')
@click.option('--status', '-s', help='ステータスでフィルタ')
@click.option('--priority', '-p', help='優先度でフィルタ')
def export_csv(output, category, status, priority):
    """CSVファイルにエクスポート"""
    from ai_task_manager.commands.export import export_csv_command
    export_csv_command(output, category, status, priority)


@cli.command('init-config')
@click.option('--output', '-o', help='出力ファイルパス')
def init_config(output):
    """設定ファイルを生成"""
    from ai_task_manager.config import init_config_file
    try:
        file_path = init_config_file(output)
        click.echo(f"✅ 設定ファイルを生成しました: {file_path}")
        click.echo("\n設定ファイルを編集してカスタマイズできます。")
    except ImportError as e:
        click.echo(f"❌ エラー: {e}")
        click.echo("PyYAMLをインストールしてください: pip install pyyaml")
    except Exception as e:
        click.echo(f"❌ エラー: {e}")


@cli.command()
@click.option('--output', '-o', help='出力ファイルパス')
@click.option('--open', 'open_browser', is_flag=True, help='生成後にブラウザで開く')
def dashboard(output, open_browser):
    """HTMLダッシュボードを生成"""
    from ai_task_manager.commands.dashboard import dashboard_command
    dashboard_command(output, open_browser)


if __name__ == '__main__':
    cli()
