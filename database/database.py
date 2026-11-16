
import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, database_name="azrael.db"):
        self.database_name = str(database_name)
        self._connect()

    def _connect(self):
        self.connection = sqlite3.connect(self.database_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _migrate_missions(self):
        self.cursor.execute("PRAGMA table_info(missions)")
        columns = [row[1] for row in self.cursor.fetchall()]

        if "risk" not in columns:
            self.cursor.execute("""
                ALTER TABLE missions
                ADD COLUMN risk INTEGER NOT NULL DEFAULT 50
            """)

        if "deadline" not in columns:
            self.cursor.execute("""
                ALTER TABLE missions
                ADD COLUMN deadline TEXT
            """)

        self.connection.commit()
    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                priority TEXT NOT NULL DEFAULT 'NORMAL',
                status TEXT NOT NULL DEFAULT 'PENDING',
                risk INTEGER NOT NULL DEFAULT 50,
                deadline TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id INTEGER,
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.connection.commit()

        # Migration برای دیتابیس‌های قدیمی
        self._migrate_missions()
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'NORMAL',
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXTre
                )
            """)

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id INTEGER,
                    action TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

        self.connection.commit()

    def log_activity(self, action, description="", mission_id=None):
        self.cursor.execute("""
            INSERT INTO activity_logs (
                mission_id, action, description, created_at
            )
            VALUES (?, ?, ?, ?)
        """, (mission_id, action, description, self.now()))
        self.connection.commit()

    def get_activity_logs(self, limit=200):
        self.cursor.execute("""
            SELECT id, mission_id, action, description, created_at
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def create_mission(
        self,
        name,
        age,
        priority="NORMAL",
        risk=50,
        deadline=None,
        notes=""
    ):
        created_at = self.now()

        self.cursor.execute("""
            INSERT INTO missions (
                name,
                age,
                priority,
                status,
                risk,
                deadline,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            age,
            priority,
            "PENDING",
            risk,
            deadline,
            notes,
            created_at
        ))

        mission_id = self.cursor.lastrowid
        self.connection.commit()

        self.log_activity(
            "MISSION_CREATED",
            f"Mission #{mission_id} created",
            mission_id
        )

        return mission_id

    def get_mission(self, mission_id):
        self.cursor.execute("""
            SELECT
                id, name, age, priority, status,
                created_at, completed_at, notes
            FROM missions
            WHERE id = ?
        """, (mission_id,))
        return self.cursor.fetchone()

    def get_missions(
        self,
        search="",
        status="ALL",
        priority="ALL",
        sort_by="id",
        descending=True
    ):
        query = """
            SELECT
                id,
                name,
                age,
                priority,
                status,
                risk,
                deadline,
                created_at,
                completed_at,
                notes
            FROM missions
            WHERE 1=1
        """

        params = []

        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")

        if status != "ALL":
            query += " AND status = ?"
            params.append(status)

        if priority != "ALL":
            query += " AND priority = ?"
            params.append(priority)

        allowed_sort_columns = {
            "id": "id",
            "name": "name",
            "age": "age",
            "priority": "priority",
            "status": "status",
            "risk": "risk",
            "deadline": "deadline",
            "created_at": "created_at"
        }

        sort_column = allowed_sort_columns.get(sort_by, "id")
        direction = "DESC" if descending else "ASC"

        query += f" ORDER BY {sort_column} {direction}"

        self.cursor.execute(query, params)

        return self.cursor.fetchall()

    def update_mission(self, mission_id, name, age, priority, notes):
        self.cursor.execute("""
            UPDATE missions
            SET name = ?, age = ?, priority = ?, notes = ?
            WHERE id = ?
        """, (name, age, priority, notes, mission_id))

        self.connection.commit()

        self.log_activity(
            "MISSION_UPDATED",
            f"Mission #{mission_id} updated",
            mission_id
        )

    def get_mission(self, mission_id):
        self.cursor.execute("""
            SELECT
                id,
                name,
                age,
                priority,
                status,
                risk,
                deadline,
                created_at,
                completed_at,
                notes
            FROM missions
            WHERE id = ?
        """, (mission_id,))

        return self.cursor.fetchone()

    def complete_mission(self, mission_id):
        completed_at = self.now()

        self.cursor.execute("""
            UPDATE missions
            SET status = 'COMPLETED', completed_at = ?
            WHERE id = ?
        """, (completed_at, mission_id))

        self.connection.commit()

        self.log_activity(
            "MISSION_COMPLETED",
            f"Mission #{mission_id} completed",
            mission_id
        )

    def reopen_mission(self, mission_id):
        self.cursor.execute("""
            UPDATE missions
            SET status = 'PENDING', completed_at = NULL
            WHERE id = ?
        """, (mission_id,))

        self.connection.commit()

        self.log_activity(
            "MISSION_REOPENED",
            f"Mission #{mission_id} reopened",
            mission_id
        )

    def delete_mission(self, mission_id):
        self.cursor.execute("""
            DELETE FROM missions
            WHERE id = ?
        """, (mission_id,))

        self.connection.commit()

        self.log_activity(
            "MISSION_DELETED",
            f"Mission #{mission_id} deleted",
            mission_id
        )

    def get_history(self):
        self.cursor.execute("""
            SELECT
                id, name, age, priority,
                created_at, completed_at, notes
            FROM missions
            WHERE status = 'COMPLETED'
            ORDER BY completed_at DESC
        """)
        return self.cursor.fetchall()

    def get_statistics(self):
        self.cursor.execute("SELECT COUNT(*) FROM missions")
        total = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT COUNT(*) FROM missions
            WHERE status = 'PENDING'
        """)
        pending = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT COUNT(*) FROM missions
            WHERE status = 'COMPLETED'
        """)
        completed = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT priority, COUNT(*)
            FROM missions
            GROUP BY priority
        """)
        priorities = dict(self.cursor.fetchall())

        self.cursor.execute("""
            SELECT COUNT(*)
            FROM missions
            WHERE priority = 'CRITICAL'
            AND status = 'PENDING'
        """)
        critical = self.cursor.fetchone()[0]

        completion_rate = round((completed / total) * 100, 1) if total else 0

        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "critical": critical,
            "completion_rate": completion_rate,
            "priorities": priorities
        }

    def set_setting(self, key, value):
        self.cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
        """, (key, value))
        self.connection.commit()

    def get_setting(self, key, default=None):
        self.cursor.execute("""
            SELECT value
            FROM settings
            WHERE key = ?
        """, (key,))
        result = self.cursor.fetchone()
        return result[0] if result else default

    def clear_missions(self):
        self.cursor.execute("DELETE FROM missions")
        self.connection.commit()

        self.log_activity(
            "DATABASE_CLEARED",
            "All missions deleted"
        )

    def export_missions_csv(self, destination):
        rows = self.get_missions(
            search="",
            status="ALL",
            priority="ALL",
            sort_by="id",
            descending=False
        )

        headers = [
            "id", "name", "age", "priority", "status",
            "created_at", "completed_at", "notes"
        ]

        with open(destination, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

            for row in rows:
                writer.writerow(row)

        self.log_activity(
            "EXPORT_CSV",
            f"Exported {len(rows)} missions to CSV"
        )

        return len(rows)

    def export_missions_json(self, destination):
        rows = self.get_missions(
            search="",
            status="ALL",
            priority="ALL",
            sort_by="id",
            descending=False
        )

        headers = [
            "id", "name", "age", "priority", "status",
            "created_at", "completed_at", "notes"
        ]

        data = [dict(zip(headers, row)) for row in rows]

        with open(destination, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        self.log_activity(
            "EXPORT_JSON",
            f"Exported {len(rows)} missions to JSON"
        )

        return len(rows)

    def backup_database(self, destination):
        self.connection.commit()
        shutil.copy2(self.database_name, destination)

        self.log_activity(
            "DATABASE_BACKUP",
            f"Database backup created: {Path(destination).name}"
        )

    def _validate_database_file(self, source):
        source_path = Path(source)

        if not source_path.exists():
            raise FileNotFoundError("Backup file does not exist.")

        connection = sqlite3.connect(str(source_path))

        try:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name = 'missions'
            """)

            if cursor.fetchone() is None:
                raise ValueError(
                    "This file is not a valid AZRAEL database."
                )

            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if not result or result[0] != "ok":
                raise ValueError("Database integrity check failed.")

        finally:
            connection.close()

    def restore_database(self, source):
        self._validate_database_file(source)

        source = str(source)
        destination = str(self.database_name)

        self.close()

        shutil.copy2(source, destination)

        self._connect()

        self.log_activity(
            "DATABASE_RESTORED",
            f"Database restored from: {Path(source).name}"
        )

    def close(self):
        try:
            self.connection.commit()
            self.connection.close()
        except Exception:
            pass
