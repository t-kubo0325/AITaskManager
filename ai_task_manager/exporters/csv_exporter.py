"""CSV エクスポート機能"""
import csv
from pathlib import Path
from typing import List
from ai_task_manager.models import Task
from ai_task_manager.database import get_connection, get_task_tags


def export_to_csv(output_path: str, category: str = None, status: str = None, priority: str = None) -> str:
    """タスクをCSV形式でエクスポート

    Args:
        output_path: 出力ファイルパス
        category: カテゴリフィルタ
        status: ステータスフィルタ
        priority: 優先度フィルタ

    Returns:
        生成されたファイルの絶対パス
    """
    # タスクを取得
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

    query += " ORDER BY id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # タスクオブジェクトに変換（タグ付き）
    tasks = []
    for row in rows:
        task_tags = get_task_tags(row[0])
        tasks.append(Task.from_db_row(row, task_tags))

    # ファイルに書き込み
    output_file = Path(output_path).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)

        # ヘッダー
        writer.writerow([
            'ID', 'タイトル', '説明', 'カテゴリ', '優先度', 'ステータス',
            '進捗率', '開始日', '期限', '完了日', '親タスクID', 'タグ',
            '作成日', '更新日'
        ])

        # データ
        for task in tasks:
            writer.writerow([
                task.id,
                task.title,
                task.description or '',
                task.category or '',
                task.priority,
                task.status,
                task.progress,
                task.start_date or '',
                task.due_date or '',
                task.completed_date or '',
                task.parent_id or '',
                ', '.join(task.tags) if task.tags else '',
                task.created_at.isoformat() if task.created_at else '',
                task.updated_at.isoformat() if task.updated_at else ''
            ])

    return str(output_file)
