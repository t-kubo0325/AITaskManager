"""タスク一覧コマンド"""
import click
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.utils.errors import handle_error, DatabaseError


def list_tasks(category, status, priority, tags):
    """タスク一覧を表示"""
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

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        # タグフィルタ
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            placeholders = ','.join('?' * len(tag_list))
            query += f"""
                AND id IN (
                    SELECT tt.task_id FROM task_tags tt
                    JOIN tags t ON tt.tag_id = t.id
                    WHERE t.name IN ({placeholders})
                    GROUP BY tt.task_id
                    HAVING COUNT(DISTINCT t.name) = ?
                )
            """
            params.extend(tag_list)
            params.append(len(tag_list))

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("📭 タスクが見つかりません")
            return

        # タスクの表示
        click.echo(f"\n📋 タスク一覧 ({len(rows)} 件)\n")
        click.echo("=" * 80)

        for row in rows:
            task_tags = get_task_tags(row[0])
            task = Task.from_db_row(row, task_tags)

            # 優先度マーク
            priority_mark = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}
            status_mark = {
                'pending': '[未着手]',
                'in_progress': '[進行中]',
                'completed': '[完了]',
                'cancelled': '[中止]'
            }

            # タグ表示
            tags_str = f" 🏷️  {', '.join(task.tags)}" if task.tags else ""

            click.echo(f"ID: {task.id} | {priority_mark.get(task.priority)} {task.title}")
            click.echo(f"  ステータス: {status_mark.get(task.status)} | 進捗: {task.progress}%")
            if task.category:
                click.echo(f"  カテゴリ: {task.category}")
            if task.start_date and task.due_date:
                click.echo(f"  期間: {task.start_date} 〜 {task.due_date}")
            elif task.due_date:
                click.echo(f"  期限: {task.due_date}")
            if tags_str:
                click.echo(f"  {tags_str}")
            click.echo("-" * 80)

    except DatabaseError as e:
        handle_error(e)
