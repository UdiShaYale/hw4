"""Campus Customs API.

Run from backend/:  uvicorn main:app --reload --port 8000
API docs:           http://127.0.0.1:8000/docs
Frontend (Vite):    http://127.0.0.1:5173
"""
from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, model_validator

import db
from models import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    Customer,
    ProductCard,
    StoredMessage,
)

logger = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress JSON responses over ~0.5 KB. The catalogue payload is mostly repeated
# text (descriptions, tags), which gzips to a fraction of its size — a smaller
# download for the shopper and less bandwidth for the shop.
app.add_middleware(GZipMiddleware, minimum_size=500)


class CachedStaticFiles(StaticFiles):
    """StaticFiles that tells the browser product photos rarely change.

    By default StaticFiles sends only ETag/Last-Modified, so every repeat view
    still makes a round trip to revalidate. A long max-age lets the browser
    serve the image straight from its own cache — faster cards on repeat
    visits, fewer requests hitting the server.
    """

    def file_response(self, *args: object, **kwargs: object):
        response = super().file_response(*args, **kwargs)
        # One day, revalidate after. Photos are replaced rarely, and the file
        # path changes when a product does, so stale images are not a risk.
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response


# catalogue.image_file_path is relative to data/data, so mounting that directory
# turns "products/foo.jpg" into "/images/products/foo.jpg".
app.mount("/images", CachedStaticFiles(directory=db.DATA_DIR), name="images")


@app.exception_handler(RequestValidationError)
def readable_validation_error(_request: Request, exc: RequestValidationError):
    """Flatten FastAPI's nested 422 body into one sentence the form can display."""
    first = exc.errors()[0] if exc.errors() else {}
    message = str(first.get("msg", "Please check the form and try again."))
    # Pydantic prefixes messages raised from a validator.
    message = message.removeprefix("Value error, ").removeprefix("Assertion failed, ")
    return JSONResponse(status_code=422, content={"detail": message})


def get_conn():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------- models


class Credentials(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    # Capped as well as floored: PBKDF2 happily hashes megabytes, and a huge
    # password is a cheap way to tie up the server.
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def check_password(self) -> "SignupRequest":
        # The browser checks this too, but the browser is not the gatekeeper.
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if self.password.lower() == self.email.lower():
            raise ValueError("Password cannot be your email address.")
        if self.password.strip() == "":
            raise ValueError("Password cannot be blank.")
        return self


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


# ChatRequest / ChatResponse live in models.py, alongside the agent's own types.


# ---------------------------------------------------------------- auth

# Passwords are never stored, logged or returned — only this one-way digest is.
# Format `pbkdf2_sha256$<salt>$<hash>`, matching what the users table already holds.
_PBKDF2_ITERATIONS = 260_000

#: Per-user random salt, so two people with the same password get different
#: digests and one precomputed rainbow table cannot crack both.
_SALT_BYTES = 16


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the attempt with the stored salt and compare in constant time."""
    try:
        algorithm, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), _PBKDF2_ITERATIONS
    ).hex()
    # compare_digest, not ==, so the comparison cannot be timed character by character.
    return secrets.compare_digest(candidate, digest)


def burn_one_hash(password: str) -> None:
    """Spend the same work on an unknown email as on a known one.

    Without this, a failed login returns noticeably faster when the address is
    not registered, which hands an attacker a list of who has an account.
    """
    hash_password(password, salt="timing-equalizer")


def _display_name(row: sqlite3.Row) -> tuple[str, str]:
    """first_name/last_name were added after the fact, so fall back to `name`."""
    first = row["first_name"]
    last = row["last_name"]
    if first and last:
        return first, last
    parts = (row["name"] or "").split()
    return (parts[0] if parts else "Friend"), (" ".join(parts[1:]) if len(parts) > 1 else "")


# ---------------------------------------------------------------- routes


@app.get("/api/health")
def health(conn: sqlite3.Connection = Depends(get_conn)):
    count = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    return {
        "ok": True,
        "database": db.DB_PATH.name,
        "products": count,
        "chat_configured": bool(os.getenv("PORTKEY_API_KEY")),
    }


@app.get("/api/categories")
def categories(conn: sqlite3.Connection = Depends(get_conn)):
    return {"categories": db.categories(conn)}


@app.get("/api/products")
def products(
    q: str | None = Query(default=None, description="free-text search"),
    category: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_conn),
):
    found = db.list_products(conn, q=q, category=category)
    return {"count": len(found), "products": found}


@app.get("/api/products/{product_id}")
def product_detail(product_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    product = db.get_product(conn, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/signup", response_model=UserOut)
def signup(body: SignupRequest, conn: sqlite3.Connection = Depends(get_conn)):
    email = body.email.lower().strip()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="That email already has an account.")

    first = body.first_name.strip()
    last = body.last_name.strip()
    full_name = f"{first} {last}".strip()

    try:
        cursor = conn.execute(
            # Parameterised, so a name or email can never be read as SQL.
            "INSERT INTO users (name, email, password_hash, first_name, last_name)"
            " VALUES (?, ?, ?, ?, ?)",
            (full_name, email, hash_password(body.password), first, last),
        )
    except sqlite3.IntegrityError:
        # The UNIQUE index is the real guard; the SELECT above only makes the
        # common case a friendly message instead of a 500.
        raise HTTPException(status_code=409, detail="That email already has an account.") from None
    conn.commit()

    # UserOut has no password field, so no hash can leak through the response.
    return UserOut(id=cursor.lastrowid, first_name=first, last_name=last, email=email)


@app.post("/api/login", response_model=UserOut)
def login(body: Credentials, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (body.email.lower().strip(),)
    ).fetchone()

    if row is None:
        burn_one_hash(body.password)
        # Same message either way: never reveal whether the email is registered.
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    if not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    first, last = _display_name(row)
    return UserOut(id=row["id"], first_name=first, last_name=last, email=row["email"])


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(user_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    """The signed-in shopper's saved conversation, oldest turn first.

    Returns empty rather than 404 for an unknown user, so a stale client never
    blocks the widget from opening.
    """
    stored = db.load_chat_history(conn, user_id)
    return ChatHistoryResponse(
        messages=[
            StoredMessage(
                role=row["role"],
                content=row["content"],
                products=[ProductCard(**p) for p in row["products"]],
                created_at=row["created_at"],
            )
            for row in stored
        ]
    )


@app.delete("/api/chat/history")
def delete_chat_history(user_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    """Let a shopper wipe their own saved conversation."""
    return {"deleted": db.clear_chat_history(conn, user_id)}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, conn: sqlite3.Connection = Depends(get_conn)):
    """One turn of the shopping agent, called by the chat widget in the corner."""
    # Imported here, not at module scope, so the catalogue endpoints still work
    # when PORTKEY_API_KEY is missing — building the agent needs the key.
    try:
        from agent import run_agent
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Who is chatting. Looked up from the database, never taken from the request
    # body, so the client can only pick an id — it cannot assert a name.
    customer = None
    if body.user_id is not None:
        row = db.get_customer(conn, body.user_id)
        if row is not None:
            customer = Customer(**row)

    try:
        result = await run_agent(conn, body.message, body.history, customer, body.page)

        # History is kept for signed-in shoppers only.
        if customer is not None:
            db.save_chat_message(conn, customer.user_id, "user", body.message)
            db.save_chat_message(
                conn,
                customer.user_id,
                "assistant",
                result.reply,
                [p.model_dump() for p in result.products],
            )
            result.saved = True
        return result
    except Exception as exc:  # noqa: BLE001 - one bad turn must not 500 the widget
        text = str(exc).lower()
        if "content_filter" in text or "content management policy" in text:
            # The gateway refused the prompt before the model saw it. Answer in
            # the shop's voice instead of showing the shopper a provider dump.
            return ChatResponse(
                reply=(
                    "I can't help with that one, but I'm happy to help you find "
                    "something in the shop — just ask about a style, colour or size."
                )
            )
        # Log the real cause for us; keep provider internals out of the browser.
        logger.exception("Chat turn failed")
        raise HTTPException(
            status_code=502,
            detail="The assistant is unavailable right now. Please try again in a moment.",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
