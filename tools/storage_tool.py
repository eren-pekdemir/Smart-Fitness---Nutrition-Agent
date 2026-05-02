"""StorageTool — persists user profiles and meal logs in a SQLite database."""

import sqlite3
from datetime import date, datetime
from config.settings import DATABASE_PATH


class StorageTool:
    """Reads and writes user data to a local SQLite database."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # User profile
    # ------------------------------------------------------------------

    def save_user_profile(self, profile: dict) -> None:
        """Insert or replace the user profile record."""
        required = {"name", "age", "gender", "weight_kg", "height_cm", "activity_level", "goal"}
        missing = required - profile.keys()
        if missing:
            raise ValueError(f"Missing profile fields: {missing}")
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO user_profile
                    (name, age, gender, weight_kg, height_cm, activity_level, goal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    age=excluded.age, gender=excluded.gender,
                    weight_kg=excluded.weight_kg, height_cm=excluded.height_cm,
                    activity_level=excluded.activity_level, goal=excluded.goal
                """,
                (
                    profile["name"], profile["age"], profile["gender"],
                    profile["weight_kg"], profile["height_cm"],
                    profile["activity_level"], profile["goal"],
                ),
            )

    def get_user_profile(self, name: str) -> dict | None:
        """Return the profile dict for `name`, or None if not found."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT name, age, gender, weight_kg, height_cm, activity_level, goal "
                "FROM user_profile WHERE name = ?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        keys = ("name", "age", "gender", "weight_kg", "height_cm", "activity_level", "goal")
        return dict(zip(keys, row))

    # ------------------------------------------------------------------
    # Meal log
    # ------------------------------------------------------------------

    def log_meal(self, entry: dict) -> int:
        """Insert a meal log entry and return the new row id.

        Required keys: food_name, calories, protein_g, carbs_g, fat_g.
        Optional keys: quantity_g, notes, logged_at (ISO string).
        """
        required = {"food_name", "calories", "protein_g", "carbs_g", "fat_g"}
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"Missing meal entry fields: {missing}")
        logged_at = entry.get("logged_at") or datetime.now().isoformat(timespec="seconds")
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO meal_log
                    (food_name, quantity_g, calories, protein_g, carbs_g, fat_g, notes, logged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["food_name"], entry.get("quantity_g", 100),
                    entry["calories"], entry["protein_g"],
                    entry["carbs_g"], entry["fat_g"],
                    entry.get("notes", ""), logged_at,
                ),
            )
            return cursor.lastrowid

    def get_daily_summary(self, for_date: str | None = None) -> dict:
        """Return totals for a specific date (YYYY-MM-DD). Defaults to today."""
        target = for_date or date.today().isoformat()
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS meals,
                    COALESCE(SUM(calories), 0),
                    COALESCE(SUM(protein_g), 0),
                    COALESCE(SUM(carbs_g), 0),
                    COALESCE(SUM(fat_g), 0)
                FROM meal_log
                WHERE DATE(logged_at) = ?
                """,
                (target,),
            ).fetchone()
        return {
            "date": target,
            "meals_logged": row[0],
            "total_calories": round(row[1], 1),
            "total_protein_g": round(row[2], 1),
            "total_carbs_g": round(row[3], 1),
            "total_fat_g": round(row[4], 1),
        }

    def get_meal_history(self, limit: int = 10) -> list[dict]:
        """Return the most recent `limit` meal log entries."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT food_name, quantity_g, calories, protein_g, carbs_g, fat_g, notes, logged_at
                FROM meal_log ORDER BY logged_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        keys = ("food_name", "quantity_g", "calories", "protein_g", "carbs_g", "fat_g", "notes", "logged_at")
        return [dict(zip(keys, row)) for row in rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    name          TEXT PRIMARY KEY,
                    age           INTEGER,
                    gender        TEXT,
                    weight_kg     REAL,
                    height_cm     REAL,
                    activity_level TEXT,
                    goal          TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meal_log (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_name  TEXT NOT NULL,
                    quantity_g REAL DEFAULT 100,
                    calories   REAL NOT NULL,
                    protein_g  REAL NOT NULL,
                    carbs_g    REAL NOT NULL,
                    fat_g      REAL NOT NULL,
                    notes      TEXT DEFAULT '',
                    logged_at  TEXT NOT NULL
                )
                """
            )
