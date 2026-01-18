"""ツリー表示ロジック"""
from typing import List, Optional
from ai_task_manager.models import Task


def generate_tree_view(tasks: List[Task], parent_id: Optional[int] = None,
                       indent: str = '', is_last: bool = True) -> str:
    """
    タスクツリーを生成

    Args:
        tasks: 全タスクのリスト
        parent_id: 親タスクID（Noneはルート）
        indent: 現在のインデント文字列
        is_last: 最後の子要素かどうか

    Returns:
        ツリー表示の文字列
    """
    output = []
    child_tasks = [t for t in tasks if t.parent_id == parent_id]

    for i, task in enumerate(child_tasks):
        is_last_child = (i == len(child_tasks) - 1)
        prefix = '└─ ' if is_last_child else '├─ '

        task_line = format_task_line(task)
        output.append(f"{indent}{prefix}{task_line}")

        new_indent = indent + ('   ' if is_last_child else '│  ')
        child_output = generate_tree_view(tasks, task.id, new_indent, is_last_child)
        if child_output:
            output.append(child_output)

    return '\n'.join(output)


def format_task_line(task: Task) -> str:
    """
    タスクを1行で表示

    Args:
        task: タスクオブジェクト

    Returns:
        フォーマットされた文字列
    """
    # タスクID
    task_id = f"[ID: {task.id}]"

    # 優先度
    priority_map = {'high': '[高]', 'medium': '[中]', 'low': '[低]'}
    priority_mark = priority_map.get(task.priority, '[中]')

    # ステータス
    status_map = {
        'pending': '[未着手]',
        'in_progress': '[進行中]',
        'completed': '[完了]',
        'cancelled': '[中止]'
    }
    status_mark = status_map.get(task.status, '')

    # 基本情報
    parts = [task_id, priority_mark, task.title]

    # 日付
    if task.start_date and task.due_date:
        parts.append(f"({task.start_date} - {task.due_date})")
    elif task.due_date:
        parts.append(f"({task.due_date})")

    # ステータス
    parts.append(status_mark)

    # 進捗率
    if task.status in ('in_progress', 'completed') and task.progress > 0:
        parts.append(f"{task.progress}%")

    # タグ
    if task.tags:
        parts.append(f"🏷️  {', '.join(task.tags)}")

    return ' '.join(p for p in parts if p)


def generate_statistics(tasks: List[Task]) -> str:
    """
    統計情報を生成

    Args:
        tasks: タスクのリスト

    Returns:
        統計情報の文字列
    """
    total = len(tasks)
    if total == 0:
        return ""

    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    pending = sum(1 for t in tasks if t.status == 'pending')

    output = [
        "\n統計:",
        f"  総タスク数: {total}",
        f"  完了: {completed} ({completed/total*100:.1f}%)",
        f"  進行中: {in_progress} ({in_progress/total*100:.1f}%)",
        f"  未着手: {pending} ({pending/total*100:.1f}%)"
    ]

    return '\n'.join(output)
