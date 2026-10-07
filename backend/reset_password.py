"""Reset a user's password to the format this backend can verify.

The three seeded accounts were hashed elsewhere with unknown PBKDF2 settings, so
login can never verify them. This rewrites one account's `password_hash` using
the backend's own `hash_password`, after which that email/password logs in
normally.

Run it from the backend/ folder with the project's virtualenv:

    ./.venv/Scripts/python.exe reset_password.py test@campuscustoms.yale.edu campuscustoms

Arguments: <email> <new_password>  (password must be at least 8 characters).
"""
from __future__ import annotations

import sys

import db
from main import hash_password, verify_password


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python reset_password.py <email> <new_password>")
        return 2

    email, new_password = sys.argv[1].strip().lower(), sys.argv[2]
    if len(new_password) < 8:
        print("Password must be at least 8 characters.")
        return 2

    conn = db.connect()
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        print(f"No account found for {email}.")
        existing = [r["email"] for r in conn.execute("SELECT email FROM users ORDER BY id")]
        print("Accounts in the database:", ", ".join(existing))
        return 1

    new_hash = hash_password(new_password)
    conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email))
    conn.commit()

    # Confirm it verifies exactly the way the /api/login route will.
    stored = conn.execute(
        "SELECT password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()["password_hash"]
    ok = verify_password(new_password, stored)
    print(f"Password for {email} reset. Verifies: {ok}")
    print("You can now log in with that email and the new password." if ok
          else "Something went wrong — the new hash did not verify.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
