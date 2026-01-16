"""データベース操作モジュール"""
import sqlite3
from pathlib import Path
from ai_task_manager.utils.errors import DatabaseError

# データベースパス
DB_PATH = Path(__file__).parent.parent / "data" / "tasks.db"


def get_connection() -> sqlite3.Connection:
    """データベース接続を取得"""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約を有効化
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"データベース接続に失敗しました: {e}")


def init_db():
    """データベースを初期化"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # tasks テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
                parent_id INTEGER,
                start_date TEXT,
                due_date TEXT,
                completed_date TEXT,
                progress INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE RESTRICT
            )
        """)

        # tags テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # task_tags テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # インデックス
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_tags_task_id ON task_tags(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_tags_tag_id ON task_tags(tag_id)")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"データベース初期化に失敗しました: {e}")
    finally:
        conn.close()


def get_or_create_tag(tag_name: str) -> int:
    """
    タグを取得または作成

    Args:
        tag_name: タグ名

    Returns:
        タグID
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 既存タグを検索
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        row = cursor.fetchone()

        if row:
            return row[0]

        # 新規作成
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの取得/作成に失敗しました: {e}")
    finally:
        conn.close()


def add_tags_to_task(task_id: int, tag_names: list):
    """
    タスクにタグを追加

    Args:
        task_id: タスクID
        tag_names: タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for tag_name in tag_names:
            # 既存タグを検索
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            row = cursor.fetchone()

            if row:
                tag_id = row[0]
            else:
                # 新規作成
                cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid

            cursor.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id)
            )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの追加に失敗しました: {e}")
    finally:
        conn.close()


def remove_tags_from_task(task_id: int, tag_names: list):
    """
    タスクからタグを削除

    Args:
        task_id: タスクID
        tag_names: タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for tag_name in tag_names:
            cursor.execute("""
                DELETE FROM task_tags
                WHERE task_id = ? AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """, (task_id, tag_name))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"タグの削除に失敗しました: {e}")
    finally:
        conn.close()


def get_task_tags(task_id: int) -> list:
    """
    タスクのタグ一覧を取得

    Args:
        task_id: タスクID

    Returns:
        タグ名のリスト
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
            ORDER BY t.name
        """, (task_id,))
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise DatabaseError(f"タグの取得に失敗しました: {e}")
    finally:
        conn.close()
