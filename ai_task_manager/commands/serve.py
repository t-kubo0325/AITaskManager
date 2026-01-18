"""Webサーバーコマンド"""
import click
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from jinja2 import Template
from ai_task_manager.database import get_connection, get_task_tags
from ai_task_manager.models import Task
from ai_task_manager.visualization.statistics import get_all_statistics
from ai_task_manager.visualization.html_generator import generate_mermaid_syntax
from ai_task_manager.utils.errors import handle_error, DatabaseError


def serve_command(port, host, debug):
    """Webサーバーを起動してタスクをブラウザで表示"""
    try:
        app = Flask(__name__)
        template_dir = Path(__file__).parent.parent / 'visualization' / 'templates'

        @app.route('/')
        def dashboard():
            """ダッシュボード"""
            try:
                # 統計データを取得
                stats = get_all_statistics()

                # カテゴリデータを準備
                category_labels = [c['category'] for c in stats['categories'][:10]]
                category_completed = [c['completed'] for c in stats['categories'][:10]]
                category_in_progress = [c['in_progress'] for c in stats['categories'][:10]]
                category_pending = [c['pending'] for c in stats['categories'][:10]]

                # タグデータを準備
                tag_labels = [t['tag'] for t in stats['tags'][:10]]
                tag_counts = [t['count'] for t in stats['tags'][:10]]

                # テンプレートを読み込み
                template_path = template_dir / 'dashboard.html'
                template = Template(template_path.read_text(encoding='utf-8'))

                # HTMLを生成
                html_content = template.render(
                    stats=stats,
                    category_labels=category_labels,
                    category_completed=category_completed,
                    category_in_progress=category_in_progress,
                    category_pending=category_pending,
                    tag_labels=tag_labels,
                    tag_counts=tag_counts
                )

                return html_content

            except Exception as e:
                return f"<h1>エラー</h1><pre>{str(e)}</pre>", 500

        @app.route('/gantt')
        def gantt():
            """ガントチャート"""
            try:
                conn = get_connection()
                cursor = conn.cursor()

                query = """
                    SELECT * FROM tasks
                    WHERE start_date IS NOT NULL
                    AND due_date IS NOT NULL
                    ORDER BY start_date, id
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                conn.close()

                if not rows:
                    return "<h1>表示するタスクがありません</h1>", 404

                # タスクオブジェクトに変換（タグ付き）
                tasks = []
                for row in rows:
                    task_tags = get_task_tags(row[0])
                    tasks.append(Task.from_db_row(row, task_tags))

                # Mermaid チャート構文を生成
                mermaid_chart = generate_mermaid_syntax(tasks)

                # タスクの日付範囲を計算
                start_dates = [t.start_date for t in tasks if t.start_date]
                end_dates = [t.due_date for t in tasks if t.due_date]

                # テンプレートを読み込み
                template_path = template_dir / 'gantt.html'
                template = Template(template_path.read_text(encoding='utf-8'))

                from datetime import datetime

                # HTMLを生成
                html_content = template.render(
                    generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    start_date=min(start_dates).strftime('%Y-%m-%d') if start_dates else 'N/A',
                    end_date=max(end_dates).strftime('%Y-%m-%d') if end_dates else 'N/A',
                    total_tasks=len(tasks),
                    mermaid_chart=mermaid_chart
                )

                return html_content

            except Exception as e:
                return f"<h1>エラー</h1><pre>{str(e)}</pre>", 500

        @app.route('/api/tasks')
        def api_tasks():
            """タスク一覧API"""
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks ORDER BY created_at")
                rows = cursor.fetchall()
                conn.close()

                tasks = []
                for row in rows:
                    task_tags = get_task_tags(row[0])
                    task = Task.from_db_row(row, task_tags)
                    tasks.append({
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'category': task.category,
                        'priority': task.priority,
                        'status': task.status,
                        'tags': task.tags,
                        'start_date': task.start_date.isoformat() if task.start_date else None,
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                    })

                return jsonify(tasks)

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # サーバー起動
        click.echo(f"🚀 Webサーバーを起動しています...")
        click.echo(f"📊 ダッシュボード: http://{host}:{port}/")
        click.echo(f"📈 ガントチャート: http://{host}:{port}/gantt")
        click.echo(f"🔌 API (タスク一覧): http://{host}:{port}/api/tasks")
        click.echo(f"\n終了するには Ctrl+C を押してください\n")

        app.run(host=host, port=port, debug=debug)

    except DatabaseError as e:
        handle_error(e)
    except Exception as e:
        click.echo(f"❌ サーバーの起動に失敗しました: {e}")
