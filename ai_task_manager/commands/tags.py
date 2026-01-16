"""タグ管理コマンド"""
import click
from ai_task_manager.database import get_connection
from ai_task_manager.utils.errors import handle_error, DatabaseError


def tags_command():
    """タグ一覧を表示"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # タグ一覧を取得（使用回数付き）
        cursor.execute("""
            SELECT t.name, COUNT(tt.task_id) as count
            FROM tags t
            LEFT JOIN task_tags tt ON t.id = tt.tag_id
            GROUP BY t.id, t.name
            ORDER BY count DESC, t.name
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("🏷️  タグがありません")
            return

        click.echo(f"\n🏷️  タグ一覧 ({len(rows)} 件)\n")
        click.echo("=" * 50)

        for name, count in rows:
            click.echo(f"{name:30} ({count} 件のタスク)")

        click.echo("=" * 50)

    except DatabaseError as e:
        handle_error(e)
