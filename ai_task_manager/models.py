"""データモデル"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from ai_task_manager.utils.date_utils import parse_date_optional


@dataclass
class Task:
    """タスクモデル"""
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = 'medium'
    status: str = 'pending'
    parent_id: Optional[int] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    progress: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: list = field(default_factory=list)
    depth: int = 0

    @property
    def is_overdue(self) -> bool:
        """期限切れかどうかを判定"""
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return self.due_date < date.today()
        return False

    @classmethod
    def from_db_row(cls, row: tuple, tags: list = None) -> 'Task':
        """
        データベース行からTaskオブジェクトを生成

        Args:
            row: データベース行（タプル）
            tags: タグのリスト（オプション）

        Returns:
            Task オブジェクト
        """
        return cls(
            id=row[0],
            title=row[1],
            description=row[2],
            category=row[3],
            priority=row[4] or 'medium',
            status=row[5] or 'pending',
            parent_id=row[6],
            start_date=parse_date_optional(row[7]),
            due_date=parse_date_optional(row[8]),
            completed_date=parse_date_optional(row[9]),
            progress=row[10] or 0,
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
            tags=tags or []
        )


@dataclass
class Tag:
    """タグモデル"""
    id: int
    name: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Tag':
        """データベース行からTagオブジェクトを生成"""
        return cls(
            id=row[0],
            name=row[1],
            created_at=datetime.fromisoformat(row[2]) if row[2] else None
        )
