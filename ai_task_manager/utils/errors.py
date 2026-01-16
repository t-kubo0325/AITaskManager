"""エラーハンドリング共通モジュール"""
import sys
import click


class TaskManagerError(Exception):
    """AI Task Manager 基底例外クラス"""
    pass


class TaskNotFoundError(TaskManagerError):
    """タスクが見つからない"""
    pass


class InvalidDateFormatError(TaskManagerError):
    """日付フォーマットが不正"""
    pass


class ParentTaskNotFoundError(TaskManagerError):
    """親タスクが存在しない"""
    pass


class TaskHasChildrenError(TaskManagerError):
    """タスクに子タスクが存在する"""
    pass


class DatabaseError(TaskManagerError):
    """データベースエラー"""
    pass


def handle_error(error: Exception, exit_code: int = 1):
    """
    エラーを処理してユーザーに表示

    Args:
        error: 例外オブジェクト
        exit_code: 終了コード
    """
    if isinstance(error, TaskNotFoundError):
        click.echo(f"❌ エラー: {error}", err=True)
    elif isinstance(error, InvalidDateFormatError):
        click.echo(f"❌ エラー: {error}", err=True)
        click.echo("💡 日付は YYYY-MM-DD 形式で指定してください（例: 2025-01-31）", err=True)
    elif isinstance(error, ParentTaskNotFoundError):
        click.echo(f"❌ エラー: {error}", err=True)
    elif isinstance(error, TaskHasChildrenError):
        click.echo(f"❌ エラー: {error}", err=True)
        click.echo("💡 先に子タスクを削除してください", err=True)
    elif isinstance(error, DatabaseError):
        click.echo(f"❌ データベースエラー: {error}", err=True)
    else:
        click.echo(f"❌ 予期しないエラー: {error}", err=True)

    sys.exit(exit_code)
