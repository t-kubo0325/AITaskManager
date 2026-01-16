"""タスク更新コマンド"""
import click
from ai_task_manager.database import (
    get_connection,
    add_tags_to_task,
    remove_tags_from_task
)
from ai_task_manager.utils.errors import (
    handle_error,
    TaskNotFoundError,
    InvalidDateFormatError,
    DatabaseError
)
from ai_task_manager.utils.date_utils import parse_date_optional


def update_task(task_id, title, description, category, priority, status, progress, start, due, add_tags, remove_tags):
    """タスクを更新"""
    try:
        # 日付のパース
        start_date = parse_date_optional(start)
        due_date = parse_date_optional(due)

        conn = get_connection()
        cursor = conn.cursor()

        # タスクの存在確認
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise TaskNotFoundError(f"タスクID {task_id} が見つかりません")

        # 更新クエリを構築
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if category is not None:
            updates.append("category = ?")
            params.append(category)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if progress is not None:
            if not (0 <= progress <= 100):
                raise ValueError("進捗率は 0〜100 の範囲で指定してください")
            updates.append("progress = ?")
            params.append(progress)

        if start_date is not None:
            updates.append("start_date = ?")
            params.append(start_date.isoformat())

        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date.isoformat())

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)

            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

        conn.close()

        # タグの追加
        if add_tags:
            tag_list = [t.strip() for t in add_tags.split(',')]
            add_tags_to_task(task_id, tag_list)

        # タグの削除
        if remove_tags:
            tag_list = [t.strip() for t in remove_tags.split(',')]
            remove_tags_from_task(task_id, tag_list)

        click.echo(f"✅ タスク {task_id} を更新しました")

    except (TaskNotFoundError, InvalidDateFormatError, DatabaseError, ValueError) as e:
        handle_error(e)
