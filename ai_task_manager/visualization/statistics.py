"""統計情報の計算"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
from ai_task_manager.database import get_connection


def get_overall_statistics() -> Dict[str, Any]:
    """全体統計を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    # 総タスク数
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]

    # ステータス別タスク数
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM tasks
        GROUP BY status
    """)
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # 優先度別タスク数
    cursor.execute("""
        SELECT priority, COUNT(*) as count
        FROM tasks
        GROUP BY priority
    """)
    priority_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # 期限超過タスク数
    today = date.today().isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE due_date < ?
        AND status NOT IN ('completed', 'cancelled')
    """, (today,))
    overdue_count = cursor.fetchone()[0]

    conn.close()

    # 完了率計算
    completed = status_counts.get('completed', 0)
    completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'total_tasks': total_tasks,
        'status_counts': status_counts,
        'priority_counts': priority_counts,
        'overdue_count': overdue_count,
        'completion_rate': completion_rate
    }


def get_period_statistics(period: str = 'week') -> Dict[str, Any]:
    """期間別統計を取得

    Args:
        period: 'week', 'month', 'year'
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 期間の開始日を計算
    today = date.today()
    if period == 'week':
        start_date = (today - timedelta(days=today.weekday())).isoformat()
    elif period == 'month':
        start_date = today.replace(day=1).isoformat()
    elif period == 'year':
        start_date = today.replace(month=1, day=1).isoformat()
    else:
        raise ValueError(f"Invalid period: {period}")

    # 期間内に作成されたタスク数
    cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE created_at >= ?
    """, (start_date,))
    created_count = cursor.fetchone()[0]

    # 期間内に完了したタスク数
    cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE completed_date >= ?
        AND status = 'completed'
    """, (start_date,))
    completed_count = cursor.fetchone()[0]

    conn.close()

    # 進捗率計算
    progress_rate = (completed_count / created_count * 100) if created_count > 0 else 0

    return {
        'period': period,
        'start_date': start_date,
        'created_count': created_count,
        'completed_count': completed_count,
        'progress_rate': progress_rate
    }


def get_category_statistics() -> List[Dict[str, Any]]:
    """カテゴリ別統計を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(category, 'その他') as category,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM tasks
        GROUP BY category
        ORDER BY total DESC
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            'category': row[0],
            'total': row[1],
            'completed': row[2],
            'in_progress': row[3],
            'pending': row[4]
        })

    conn.close()
    return results


def get_priority_statistics() -> List[Dict[str, Any]]:
    """優先度別統計を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            priority,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status IN ('pending', 'in_progress') THEN 1 ELSE 0 END) as remaining
        FROM tasks
        GROUP BY priority
        ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            'priority': row[0],
            'total': row[1],
            'completed': row[2],
            'remaining': row[3]
        })

    conn.close()
    return results


def get_tag_statistics() -> List[Dict[str, int]]:
    """タグ別統計を取得"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            t.name,
            COUNT(tt.task_id) as task_count
        FROM tags t
        LEFT JOIN task_tags tt ON t.id = tt.tag_id
        GROUP BY t.name
        ORDER BY task_count DESC
        LIMIT 20
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            'tag': row[0],
            'count': row[1]
        })

    conn.close()
    return results


def get_all_statistics() -> Dict[str, Any]:
    """すべての統計情報を取得"""
    return {
        'overall': get_overall_statistics(),
        'week': get_period_statistics('week'),
        'month': get_period_statistics('month'),
        'categories': get_category_statistics(),
        'priorities': get_priority_statistics(),
        'tags': get_tag_statistics()
    }
