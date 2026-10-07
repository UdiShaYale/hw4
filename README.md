# Campus Customs

Storefront for the Campus Customs catalogue: a FastAPI backend reading
`data/data/campus_customs.db`, and a React + Vite + TypeScript frontend.

## Catalogue data

The database and product photos are course-provided and are **not** in this
repo. Before running anything, put them at `hw 4/data/data/` so the tree looks
like this:

```
hw 4/
  data/data/campus_customs.db
  data/data/products/*.jpg
```

`backend/db.py` resolves that path relative to the repo root, and `main.py`
mounts `data/data/` as `/images`. Without it the API starts but every
catalogue route comes back empty.

## Running it

Two terminals.

**Backend** — serves the API and the product photos on port 8000:

```bash
cd "hw 4/backend" && ./.venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

**Frontend** — Vite dev server on port 5173, proxying `/api` and `/images` to the backend:

```bash
npm run dev --prefix "hw 4/frontend"
```

Then open http://localhost:5173. API docs are at http://127.0.0.1:8000/docs.

First-time setup, if the virtualenv is missing:

```bash
cd "hw 4/backend" && python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Layout

```
backend/
  main.py        FastAPI app — routes, auth, static product images
  db.py          every SQLite read; parses the JSON-in-TEXT columns
  agent.py       the PydanticAI agent — model, tools, one turn
  tools.py       catalogue lookups the agent can call
  models.py      typed shapes: ChatRequest, ChatReply, ProductCard
  prompts/
    prompt.md    Campus Customs voice and safety rules
frontend/
  src/pages/     Home, Products, ProductDetail, About, Login, CreateAccount
  src/components/ NavBar, ProductCard, ChatWidget, AssistantMatches, YaleLogo
  src/lib/       api client, shared types, auth + agent-match context
output/harness.md  field-by-field notes on the database
```

## API

| Route | Purpose |
|---|---|
| `GET /api/health` | Row count and whether the chat key is configured |
| `GET /api/products?q=&category=` | Catalogue list, searchable and filterable |
| `GET /api/products/{id}` | One product plus per-size stock |
| `GET /api/categories` | Normalized category labels for the filter chips |
| `POST /api/signup` / `POST /api/login` | Account creation and sign-in |
| `POST /api/chat` | Shopping assistant — returns a reply plus product cards |
| `GET /api/chat/history?user_id=` | A signed-in shopper's saved conversation |
| `DELETE /api/chat/history?user_id=` | Wipe that conversation |
| `GET /images/products/*.jpg` | Product photos, mounted from `data/data/` |

## Notes

- **Credentials.** `PORTKEY_API_KEY` is read from the project root `.env`. The
  catalogue pages work without it; only `/api/chat` needs it.
- **Agent matches render on the page.** When the assistant matches products it
  returns ids only; the backend rebuilds each card from the database and the
  `AssistantMatches` band shows them under the nav on any route. Cards link to
  the normal item page.
- **The assistant is a PydanticAI agent.** It reaches the catalogue only
  through four tools in `tools.py`, and its answer is constrained to the
  `ChatReply` model. Product cards are rebuilt from the database out of the ids
  it returns, so a hallucinated id becomes a missing card, never a fake price.
- **Categories are normalized.** `garment_type` holds 22 spellings of about
  eight categories, so `db.category_for()` collapses them before they reach the
  filter chips.
- **Passwords.** Stored only as a salted PBKDF2-HMAC-SHA256 digest (16-byte
  per-user salt, 260,000 iterations), compared in constant time. See the
  Authentication section of `output/harness.md` for the full write-up.
- **Existing accounts can't log in.** The three users already in the database
  were hashed elsewhere with unknown PBKDF2 parameters. New accounts created
  through **Create Account** work normally.
- **Chat history is saved for signed-in shoppers only**, in the existing
  `chat_messages` table, and restored on their next visit — product cards
  included. Signed-out turns are answered but never written.
- **Login is cosmetic, and that now matters more.** It verifies the password
  but issues no session token, so `user_id` is taken from the request body and
  nothing verifies it — a forged id can read another shopper's saved chat. See
  the end of `output/harness.md` for what closing this needs.
