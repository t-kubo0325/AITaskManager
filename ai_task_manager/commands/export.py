"""エクスポートコマンド"""
import click
from ai_task_manager.exporters.csv_exporter import export_to_csv
from ai_task_manager.utils.errors import handle_error, DatabaseError


def export_csv_command(output, category, status, priority):
    """CSVエクスポート"""
    try:
        output_path = output or 'tasks.csv'
        file_path = export_to_csv(output_path, category, status, priority)
        click.echo(f"✅ CSVファイルを生成しました: {file_path}")

    except (DatabaseError, IOError) as e:
        handle_error(e)
