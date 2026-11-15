"""SQLite recipe book: safe persistent history and favorites."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "recipes.sqlite3"


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS recipe_book (
      id TEXT PRIMARY KEY,
      created_at TEXT NOT NULL,
      name TEXT NOT NULL,
      cuisine TEXT NOT NULL,
      ingredients TEXT NOT NULL,
      payload TEXT NOT NULL,
      favorite INTEGER NOT NULL DEFAULT 0
    )""")
    conn.commit()
    return conn


def save_recipe(state: dict, db_path: Path | str = DB_PATH) -> str:
    recipe = state["recipe"]
    recipe_id = str(uuid.uuid4())
    with connect(db_path) as conn:
        conn.execute("""INSERT INTO recipe_book (id, created_at, name, cuisine, ingredients, payload)
                        VALUES (?, ?, ?, ?, ?, ?)""", (
            recipe_id,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            str(recipe.get("recipe_name", "Untitled recipe")),
            str(recipe.get("cuisine", state.get("cuisine", "Other"))),
            ", ".join(state.get("ingredients", [])),
            json.dumps(state, ensure_ascii=False),
        ))
        conn.commit()
    return recipe_id


def list_recipes(db_path: Path | str = DB_PATH, limit: int = 100) -> list[dict]:
    with connect(db_path) as conn:
        rows = conn.execute("""SELECT id, created_at, name, cuisine, ingredients, favorite
                               FROM recipe_book ORDER BY created_at DESC, rowid DESC LIMIT ?""", (max(1, min(limit, 500)),)).fetchall()
    return [dict(row) for row in rows]


def get_recipe(recipe_id: str, db_path: Path | str = DB_PATH) -> dict | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT payload FROM recipe_book WHERE id = ?", (recipe_id,)).fetchone()
    return json.loads(row["payload"]) if row else None


def set_favorite(recipe_id: str, favorite: bool, db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute("UPDATE recipe_book SET favorite = ? WHERE id = ?", (int(favorite), recipe_id))
        conn.commit()


def delete_recipe(recipe_id: str, db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM recipe_book WHERE id = ?", (recipe_id,))
        conn.commit()
