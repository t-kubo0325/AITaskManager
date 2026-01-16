"""JSON出力ユーティリティ"""
import json
from typing import List
from ai_task_manager.models import Task


def tasks_to_json(tasks: List[Task]) -> str:
    """タスクリストをJSON形式に変換"""
    task_dicts = []
    for task in tasks:
        task_dict = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'category': task.category,
            'priority': task.priority,
            'status': task.status,
            'parent_id': task.parent_id,
            'start_date': str(task.start_date) if task.start_date else None,
            'due_date': str(task.due_date) if task.due_date else None,
            'completed_date': str(task.completed_date) if task.completed_date else None,
            'progress': task.progress,
            'tags': task.tags,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'is_overdue': task.is_overdue
        }
        task_dicts.append(task_dict)

    return json.dumps(task_dicts, ensure_ascii=False, indent=2)
