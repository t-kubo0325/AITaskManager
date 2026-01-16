"""タスク削除コマンド"""
import click
from ai_task_manager.database import get_connection
from ai_task_manager.utils.errors import (
    handle_error,
    TaskNotFoundError,
    TaskHasChildrenError,
    DatabaseError
)


def delete_task(task_id, force):
    """タスクを削除"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # タスクの存在確認
        cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            raise TaskNotFoundError(f"タスクID {task_id} が見つかりません")

        task_title = row[0]

        # 子タスクの存在確認
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE parent_id = ?", (task_id,))
        child_count = cursor.fetchone()[0]

        if child_count > 0:
            raise TaskHasChildrenError(
                f"タスク '{task_title}' には {child_count} 件の子タスクがあります"
            )

        # 削除確認
        if not force:
            if not click.confirm(f"タスク '{task_title}' を削除しますか？"):
                click.echo("❌ キャンセルしました")
                conn.close()
                return

        # 削除実行
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

        click.echo(f"✅ タスク '{task_title}' を削除しました")

    except (TaskNotFoundError, TaskHasChildrenError, DatabaseError) as e:
        handle_error(e)
