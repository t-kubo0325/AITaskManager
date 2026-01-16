"""ガントチャートコマンド"""
import click
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.visualization.ascii_gantt import generate_ascii_gantt
from ai_task_manager.utils.errors import handle_error, DatabaseError, InvalidDateFormatError


def gantt_command(range_str, category, status, priority, width, html, output, open_browser):
    """ASCIIガントチャート表示"""
    try:
        # 日付範囲の解析
        start_date, end_date = parse_date_range(range_str)

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM tasks
            WHERE start_date IS NOT NULL
            AND due_date IS NOT NULL
            AND due_date >= ?
            AND start_date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY start_date, id"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            click.echo("⚠️  表示するタスクがありません")
            return

        # タスクオブジェクトに変換（タグ付き）
        tasks = []
        for row in rows:
            task_tags = get_task_tags(row[0])
            tasks.append(Task.from_db_row(row, task_tags))

        if html:
            # HTML生成
            from ai_task_manager.visualization.html_generator import generate_html_gantt

            file_path = generate_html_gantt(tasks, output or 'gantt.html')
            click.echo(f"✅ HTMLファイルを生成しました: {file_path}")

            if open_browser:
                open_in_browser(file_path)
                click.echo("ブラウザで開きました")
        else:
            # ASCII表示（既存）
            gantt_chart = generate_ascii_gantt(tasks, start_date, end_date, width)
            click.echo(gantt_chart)

    except (DatabaseError, InvalidDateFormatError) as e:
        handle_error(e)


def open_in_browser(file_path: str):
    """ブラウザでHTMLファイルを開く（WSL対応）"""
    import os
    import subprocess
    import platform

    abs_path = os.path.abspath(file_path)

    try:
        if platform.system() == "Windows":
            os.startfile(abs_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", abs_path])
        else:  # Linux / WSL
            # WSL環境の検出
            if "microsoft" in platform.uname().release.lower():
                # WSL: wslview を使用
                try:
                    subprocess.run(["wslview", abs_path], check=True, timeout=5)
                except FileNotFoundError:
                    # wslview がない場合のフォールバック
                    click.echo("⚠️ wslview が見つかりません。wslu パッケージをインストールしてください")
                    click.echo(f"手動で開く場合: {abs_path}")
            else:
                # 通常のLinux: xdg-open
                subprocess.run(["xdg-open", abs_path])
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        click.echo("⚠️ ブラウザの自動起動に失敗しました")
        click.echo(f"手動で開く場合: {abs_path}")


def parse_date_range(range_str):
    """
    日付範囲文字列を解析

    Args:
        range_str: 範囲文字列（YYYY-MM または YYYY-MM-DD:YYYY-MM-DD）

    Returns:
        (start_date, end_date) のタプル
    """
    try:
        if not range_str:
            # デフォルト: 今月
            today = date.today()
            start = date(today.year, today.month, 1)
            end = start + relativedelta(months=1, days=-1)
            return start, end

        if ':' in range_str:
            # 範囲指定: YYYY-MM-DD:YYYY-MM-DD
            start_str, end_str = range_str.split(':')
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()
            return start, end

        # 月指定: YYYY-MM
        year_month = datetime.strptime(range_str, '%Y-%m')
        start = date(year_month.year, year_month.month, 1)
        end = start + relativedelta(months=1, days=-1)
        return start, end

    except ValueError as e:
        raise InvalidDateFormatError(f"日付範囲のフォーマットが不正です: {range_str}")
