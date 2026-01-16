"""ASCIIガントチャート生成"""
from datetime import date, timedelta
from typing import List
from ai_task_manager.models import Task


def generate_ascii_gantt(tasks: List[Task], start_date: date, end_date: date, width: int = 80) -> str:
    """
    ASCII ガントチャートを生成

    Args:
        tasks: 表示するタスクのリスト
        start_date: 表示開始日
        end_date: 表示終了日
        width: チャート全体の幅

    Returns:
        ガントチャートの文字列
    """
    # ガントチャート表示可能なタスクのみフィルタ
    valid_tasks = [t for t in tasks if t.start_date and t.due_date]

    if not valid_tasks:
        return "⚠️  開始日と期限の両方が設定されているタスクがありません"

    name_col_width = 30
    chart_width = width - name_col_width - 10

    output = []
    output.append(f"タスクガントチャート: {start_date.strftime('%Y年%m月')}")
    output.append('━' * width)

    # タイムラインヘッダー
    timeline_header = generate_timeline_header(start_date, end_date, name_col_width, chart_width)
    output.append(timeline_header)
    output.append('━' * width)

    # 各タスクのバー
    for task in valid_tasks:
        task_line = generate_task_bar(task, start_date, end_date, name_col_width, chart_width)
        output.append(task_line)

    output.append('━' * width)
    output.append(generate_legend())
    output.append(generate_statistics_gantt(valid_tasks, start_date, end_date))

    return '\n'.join(output)


def generate_timeline_header(start_date: date, end_date: date, name_width: int, chart_width: int) -> str:
    """タイムライン目盛りヘッダーを生成"""
    total_days = (end_date - start_date).days + 1
    timeline = [' '] * chart_width

    # 5日単位で目盛りを配置
    for i in range(0, total_days, 5):
        current_date = start_date + timedelta(days=i)
        position = int((i / total_days) * chart_width)
        if position < chart_width - 2:
            day_str = str(current_date.day).rjust(2)
            if position + 1 < chart_width:
                timeline[position] = day_str[0]
                timeline[position + 1] = day_str[1]

    timeline_str = ''.join(timeline)
    return f"{'ID':<3} | {'タスク名':<{name_width}} | {timeline_str}"


def generate_task_bar(task: Task, start_date: date, end_date: date, name_width: int, chart_width: int) -> str:
    """個別タスクのバーを生成"""
    bar = [' '] * chart_width

    if task.start_date and task.due_date:
        total_days = (end_date - start_date).days + 1
        task_start_offset = max(0, (task.start_date - start_date).days)
        task_end_offset = min(total_days, (task.due_date - start_date).days + 1)

        start_pos = int((task_start_offset / total_days) * chart_width)
        end_pos = int((task_end_offset / total_days) * chart_width)

        # バーの記号を決定
        bar_char = get_bar_character(task)

        for i in range(start_pos, min(end_pos, chart_width)):
            bar[i] = bar_char

        # 現在位置を表示
        today_offset = (date.today() - start_date).days
        if 0 <= today_offset < total_days:
            today_pos = int((today_offset / total_days) * chart_width)
            if start_pos <= today_pos < end_pos:
                bar[today_pos] = '>'

    bar_str = ''.join(bar)
    task_name = task.title[:name_width]
    return f"{task.id:<3} | {task_name:<{name_width}} | [{bar_str}]"


def get_bar_character(task: Task) -> str:
    """タスクのステータスに応じたバー文字を返す"""
    if task.status == 'completed':
        return '✓'
    elif task.is_overdue:
        return '!'
    elif task.status == 'in_progress':
        return '='
    else:  # pending
        return '-'


def generate_legend() -> str:
    """凡例を生成"""
    return """
凡例:
  [=] タスク期間（進行中）  [✓] 完了  [!] 期限超過  [-] 未着手  [>] 本日
"""


def generate_statistics_gantt(tasks: List[Task], start_date: date, end_date: date) -> str:
    """統計情報を生成"""
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')

    return f"""
統計:
  期間: {start_date} - {end_date}
  総タスク数: {total}
  完了: {completed} ({completed/total*100:.1f}%)
"""
