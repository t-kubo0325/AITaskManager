"""ツリー表示コマンド"""
import click
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.visualization.tree_view import generate_tree_view, generate_statistics
from ai_task_manager.utils.errors import handle_error, DatabaseError


def tree_command(category, status, tags):
    """ツリー表示"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        # タグフィルタ
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            placeholders = ','.join('?' * len(tag_list))
            query += f"""
                AND id IN (
                    SELECT tt.task_id FROM task_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                )
            """
            params.extend(tag_list)

        query += " ORDER BY created_at"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("📭 タスクが見つかりません")
            return

        # タスクオブジェクトに変換（タグ付き）
        tasks = []
        for row in rows:
            task_tags = get_task_tags(row[0])
            tasks.append(Task.from_db_row(row, task_tags))

        # ツリー表示
        click.echo("\n📁 すべてのタスク\n")
        tree = generate_tree_view(tasks)
        if tree:
            click.echo(tree)

        # 統計情報
        stats = generate_statistics(tasks)
        if stats:
            click.echo(stats)

    except DatabaseError as e:
        handle_error(e)
