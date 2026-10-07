"""SQLite access for the Campus Customs catalogue.

Every row the API returns is shaped here, so the JSON-in-TEXT columns
(`colors`, `search_tags`, `products_json`) are parsed exactly once.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_DIR = ROOT / "data" / "data"
DB_PATH = DATA_DIR / "campus_customs.db"

#: Catalogue order for the size selector. `inventory.size` has no natural sort.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

#: `garment_type` holds 22 spellings of roughly eight categories. Map the raw
#: value onto a clean label so the Products filter does not show duplicates.
_CATEGORY_RULES: list[tuple[tuple[str, ...], str]] = [
    (("hood",), "Hoodies"),
    (("quarter-zip", "quarter zip", "mockneck"), "Quarter-Zips"),
    (("fleece", "jacket", "bomber"), "Jackets"),
    (("crewneck", "crew-neck sweatshirt"), "Crewnecks"),
    (("performance",), "Performance"),
    (("t-shirt", "tshirt", "tee"), "T-Shirts"),
]


def category_for(garment_type: str) -> str:
    """Collapse a raw `garment_type` into one of a handful of shopper-facing labels."""
    needle = garment_type.lower()
    for keywords, label in _CATEGORY_RULES:
        if any(k in needle for k in keywords):
            return label
    return "Other"


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _loads(raw: Any) -> list[str]:
    """`colors` and `search_tags` are JSON arrays stored as TEXT."""
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return [str(raw)]
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_for(row["garment_type"]),
        "description": row["description"],
        "colors": _loads(row["colors"]),
        "search_tags": _loads(row["search_tags"]),
        # Served by the StaticFiles mount in main.py, not read from disk by the client.
        "image_url": f"/images/{row['image_file_path']}",
        "price": float(row["price"]),
    }


def list_products(conn: sqlite3.Connection, q: str | None = None,
                  category: str | None = None) -> list[dict]:
    rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    products = [product_from_row(r) for r in rows]

    if category and category.lower() != "all":
        products = [p for p in products if p["category"].lower() == category.lower()]

    if q:
        needle = q.lower().strip()
        products = [p for p in products if _matches(p, needle)]

    return products


def _matches(product: dict, needle: str) -> bool:
    """Search name, description, colors and the hand-written search_tags."""
    haystack = " ".join(
        [product["name"], product["description"], product["garment_type"],
         product["category"], *product["colors"], *product["search_tags"]]
    ).lower()
    return all(word in haystack for word in needle.split())


def sizes_for(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    sizes = [{"size": r["size"], "quantity": r["quantity"]} for r in rows]
    sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"])
               if s["size"] in SIZE_ORDER else len(SIZE_ORDER))
    return sizes


def get_product(conn: sqlite3.Connection, product_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
    ).fetchone()
    if row is None:
        return None
    product = product_from_row(row)
    product["sizes"] = sizes_for(conn, product_id)
    product["total_stock"] = sum(s["quantity"] for s in product["sizes"])
    product["in_stock"] = product["total_stock"] > 0
    return product


def categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT garment_type FROM catalogue").fetchall()
    labels = sorted({category_for(r["garment_type"]) for r in rows})
    return ["All", *labels]


# ---------------------------------------------------------------- chat history
# Persisted only for signed-in shoppers, in the `chat_messages` table that was
# already in the schema: (user_id, role, content, products_json, created_at).

#: Turns to replay when someone comes back. One conversation, not a transcript.
HISTORY_LIMIT = 40


def load_chat_history(conn: sqlite3.Connection, user_id: int,
                      limit: int = HISTORY_LIMIT) -> list[dict]:
    """The most recent turns for one user, oldest first."""
    rows = conn.execute(
        "SELECT role, content, products_json, created_at FROM chat_messages"
        " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()

    messages = []
    for row in reversed(rows):  # newest-first query, oldest-first result
        products: list[dict] = []
        if row["products_json"]:
            try:
                parsed = json.loads(row["products_json"])
                products = parsed if isinstance(parsed, list) else []
            except ValueError:
                # A malformed blob should cost the cards, not the conversation.
                products = []
        messages.append({
            "role": row["role"],
            "content": row["content"],
            "products": products,
            "created_at": row["created_at"],
        })
    return messages


def save_chat_message(conn: sqlite3.Connection, user_id: int, role: str,
                      content: str, products: list[dict] | None = None) -> None:
    """Append one turn. `products_json` stays NULL for user turns."""
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json)"
        " VALUES (?, ?, ?, ?)",
        (
            user_id,
            role,
            content,
            json.dumps(products, ensure_ascii=False) if products else None,
        ),
    )
    conn.commit()


def clear_chat_history(conn: sqlite3.Connection, user_id: int) -> int:
    """Delete one user's conversation. Returns how many rows went."""
    cursor = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
    conn.commit()
    return cursor.rowcount


def get_customer(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """The handful of `users` fields the agent is allowed to see.

    Deliberately excludes `password_hash` — the agent has no reason to know a
    credential exists, and what the agent cannot see it cannot leak.
    """
    row = conn.execute(
        "SELECT id, name, email, first_name, last_name, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None

    first = row["first_name"]
    last = row["last_name"]
    if not (first and last):
        parts = (row["name"] or "").split()
        first = parts[0] if parts else "there"
        last = " ".join(parts[1:]) if len(parts) > 1 else ""

    return {
        "user_id": row["id"],
        "first_name": first,
        "last_name": last,
        "email": row["email"],
        "member_since": row["created_at"] or "",
    }
