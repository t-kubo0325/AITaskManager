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
def list(category, status, priority, tags):
    """タスク一覧を表示"""
    from ai_task_manager.commands.list import list_tasks
    list_tasks(category, status, priority, tags)


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
def gantt(range_str, category, status, priority, width):
    """ASCIIガントチャートを表示"""
    from ai_task_manager.commands.gantt import gantt_command
    gantt_command(range_str, category, status, priority, width)


@cli.command()
def tags():
    """タグ一覧を表示"""
    from ai_task_manager.commands.tags import tags_command
    tags_command()


if __name__ == '__main__':
    cli()
