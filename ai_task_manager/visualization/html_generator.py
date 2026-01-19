"""HTML生成モジュール"""
from datetime import datetime
from pathlib import Path
from typing import List
from jinja2 import Template
from ai_task_manager.models import Task

TEMPLATE_DIR = Path(__file__).parent / 'templates'


def generate_html_gantt(tasks: List[Task], output_path: str) -> str:
    """
    Mermaid.js を使用したHTML ガントチャートを生成

    Args:
        tasks: タスクリスト
        output_path: 出力ファイルパス

    Returns:
        生成されたファイルの絶対パス
    """
    template_path = TEMPLATE_DIR / 'gantt.html'
    template = Template(template_path.read_text(encoding='utf-8'))

    # Mermaid チャート構文を生成
    mermaid_chart = generate_mermaid_syntax(tasks)

    # タスクの日付範囲を計算
    start_dates = [t.start_date for t in tasks if t.start_date]
    end_dates = [t.due_date for t in tasks if t.due_date]

    # テンプレートに値を注入
    html_content = template.render(
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        start_date=min(start_dates).strftime('%Y-%m-%d') if start_dates else 'N/A',
        end_date=max(end_dates).strftime('%Y-%m-%d') if end_dates else 'N/A',
        total_tasks=len(tasks),
        mermaid_chart=mermaid_chart
    )

    # ファイルに書き込み
    output_file = Path(output_path).expanduser().resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding='utf-8')

    return str(output_file)


def generate_mermaid_syntax(tasks: List[Task]) -> str:
    """Mermaid ガントチャート構文を生成"""
    lines = [
        "gantt",
        "    title タスク管理ガントチャート",
        "    dateFormat YYYY-MM-DD",
    ]

    # カテゴリごとにグループ化
    tasks_by_category = {}
    for task in tasks:
        category = task.category or 'その他'
        if category not in tasks_by_category:
            tasks_by_category[category] = []
        tasks_by_category[category].append(task)

    # 各カテゴリのタスクを出力
    for category, category_tasks in tasks_by_category.items():
        lines.append(f"    section {category}")

        for task in category_tasks:
            if not task.start_date or not task.due_date:
                continue

            # ステータスをMermaidの状態に変換
            status = {
                'completed': 'done',
                'in_progress': 'active',
                'cancelled': 'crit',
                'pending': ''
            }.get(task.status, '')

            # 期間を計算（日数）
            duration_days = (task.due_date - task.start_date).days + 1

            # ステータスが空の場合はカンマなし
            if status:
                task_line = f"    {task.title}    :{status}, task{task.id}, "
            else:
                task_line = f"    {task.title}    :task{task.id}, "
            task_line += f"{task.start_date}, {duration_days}d"
            lines.append(task_line)

    return '\n'.join(lines)
