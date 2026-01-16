"""タスク追加コマンド"""
import click
from ai_task_manager.database import get_connection, add_tags_to_task
from ai_task_manager.utils.errors import (
    handle_error,
    InvalidDateFormatError,
    ParentTaskNotFoundError,
    DatabaseError
)
from ai_task_manager.utils.date_utils import parse_date_optional


def add_task(title, description, category, priority, start, due, parent, tags):
    """タスクを追加"""
    try:
        # 日付のパース
        start_date = parse_date_optional(start)
        due_date = parse_date_optional(due)

        conn = get_connection()
        cursor = conn.cursor()

        # 親タスクの存在確認
        if parent:
            cursor.execute("SELECT id FROM tasks WHERE id = ?", (parent,))
            if not cursor.fetchone():
                raise ParentTaskNotFoundError(f"親タスクID {parent} が見つかりません")

        # タスク追加
        cursor.execute("""
            INSERT INTO tasks (title, description, category, priority, start_date, due_date, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            category,
            priority,
            start_date.isoformat() if start_date else None,
            due_date.isoformat() if due_date else None,
            parent
        ))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # タグの追加
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            add_tags_to_task(task_id, tag_list)

        click.echo(f"✅ タスクを追加しました (ID: {task_id})")

    except (InvalidDateFormatError, ParentTaskNotFoundError, DatabaseError) as e:
        handle_error(e)
