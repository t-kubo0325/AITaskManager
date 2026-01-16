"""日付操作ユーティリティ"""
from datetime import date, datetime
from typing import Optional
from ai_task_manager.utils.errors import InvalidDateFormatError


def parse_date(date_str: str) -> date:
    """
    文字列を日付オブジェクトに変換

    Args:
        date_str: 日付文字列（YYYY-MM-DD）

    Returns:
        date オブジェクト

    Raises:
        InvalidDateFormatError: フォーマットが不正な場合
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise InvalidDateFormatError(
            f"日付フォーマットが不正です: {date_str}"
        )


def format_date(d: date) -> str:
    """日付を文字列に変換"""
    return d.strftime('%Y-%m-%d')


def parse_date_optional(date_str: Optional[str]) -> Optional[date]:
    """オプショナルな日付文字列をパース"""
    if date_str is None:
        return None
    return parse_date(date_str)
