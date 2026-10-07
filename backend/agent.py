"""The Campus Customs shopping agent.

Built once at import time and reused for every request: the model, the
instructions in `prompts/prompt.md` and the tool schemas never change between
turns, so there is nothing to rebuild. Only `ShopDeps` — the SQLite connection —
is per-request.
"""
from __future__ import annotations

import os
import sqlite3
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
import tools
from models import (
    ChatReply,
    ChatResponse,
    ChatTurn,
    Customer,
    PageContext,
    PriceInfo,
    ProductDescription,
    ProductSummary,
    StockReport,
)
from tools import ShopDeps

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"

# PORTKEY_API_KEY lives in the project root .env, one level above hw 4.
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE.parent.parent / ".env")

MODEL_NAME = "gpt-5.6-luna"

#: Most cards the site will render for one turn. Keeps a "show me hoodies"
#: answer browsable without turning into the whole catalogue.
MAX_CARDS = 6

#: How many prior turns to replay. Enough for "do you have that in navy?" to
#: resolve, short enough that the prompt stays cheap.
HISTORY_TURNS = 6

#: Loop limit: the most model requests one turn may make before the run is cut
#: off. One search plus a few detail lookups plus the final answer fits well
#: inside this; the cap is a guard against a tool-calling loop that never ends.
REQUEST_LIMIT = 6


@lru_cache(maxsize=1)
def read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_agent() -> Agent[ShopDeps, ChatReply]:
    """OpenAI model routed through the Portkey gateway, constrained to ChatReply."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the root .env file.")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        default_headers={"x-portkey-provider": "openai"},
    )
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))

    return Agent(
        model,
        deps_type=ShopDeps,
        output_type=ChatReply,
        instructions=read_prompt(),
    )


agent = build_agent()


@agent.instructions
def who_is_chatting(ctx: RunContext[ShopDeps]) -> str:
    """Tell the agent who it is talking to, every turn.

    Injected as instructions rather than left to a tool call, because the agent
    should greet someone by name without having to think to look it up.
    """
    customer = ctx.deps.customer
    if customer is None:
        return (
            "The shopper is not signed in. You do not know who they are. Do not "
            "guess, and do not ask for personal details — if they want their chat "
            "remembered they can log in."
        )
    return (
        f"The shopper is signed in: {customer.first_name} {customer.last_name}. "
        f"Greet them by first name when it is natural; do not overuse it. "
        f"Call get_customer only if you need their details beyond the name. "
        f"Never read their email address back to them."
    )


@agent.instructions
def current_page(ctx: RunContext[ShopDeps]) -> str:
    """Resolve the product the shopper is looking at, so "this" has a referent.

    The route alone would leave the agent to infer a product from a slug; this
    looks the item up and states it plainly, with live stock.
    """
    page = ctx.deps.page
    if page is None or not page.product_id:
        where = page.route if page else "/"
        return (
            f"The shopper is on {where}, which is not a product page. If they say "
            f'"this" or "it" without naming an item, ask which product they mean.'
        )

    product = tools.product_details(ctx.deps.conn, page.product_id)
    if product is None:
        return f"The shopper is on {page.route}, but that product_id is not in the catalogue."

    in_stock = [s.size for s in product.sizes if s.in_stock]
    sold_out = [s.size for s in product.sizes if not s.in_stock]
    lines = [
        "The shopper is currently viewing this product page, so "
        '"this", "it" and "this one" mean this product unless they name another:',
        f"  product_id: {product.product_id}",
        f"  name: {product.name} ({product.garment_type})",
        f"  price: ${product.price:.0f}",
        f"  colors: {', '.join(product.colors)}",
        f"  in stock: {', '.join(in_stock) or 'none'}",
        f"  sold out: {', '.join(sold_out) or 'none'}",
        "These figures were read from the database for this turn. You may use "
        "them directly; call check_stock again only if the shopper asks about a "
        "different product.",
    ]
    return "\n".join(lines)


def _unknown_id(ctx: RunContext[ShopDeps], product_id: str) -> str:
    """Steer the model back to a real id instead of letting it guess.

    Raised as ModelRetry, so pydantic-ai feeds this straight back to the model
    and it can correct itself within the same turn.
    """
    nearby = tools.search_catalogue(ctx.deps.conn, product_id.replace("-", " "))[:5]
    suggestions = ", ".join(p.product_id for p in nearby) or "none"
    return (
        f"No product has the id '{product_id}'. Do not guess or invent one. "
        f"Call search_products first and use an id it returns. "
        f"Closest matches: {suggestions}."
    )


# ---------------------------------------------------------------- tools
# Everything the agent knows about the shop comes through these four functions.


@agent.tool
def search_products(
    ctx: RunContext[ShopDeps],
    query: str = "",
    category: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> list[ProductSummary]:
    """Search the catalogue.

    Args:
        query: What the shopper is after — "navy hoodie", "law school", "The Game".
        category: Optional exact filter: Hoodies, Crewnecks, T-Shirts, Jackets,
            Quarter-Zips, Performance.
        max_price: Only products at or below this price, in dollars.
        size: Only products with this size still in stock (XS, S, M, L, XL, XXL).
    """
    return tools.search_catalogue(ctx.deps.conn, query, category, max_price, size)


@agent.tool
def get_product(ctx: RunContext[ShopDeps], product_id: str) -> ProductSummary:
    """Everything about one product: description, colours, price and per-size stock.

    Use this when a shopper asks about a specific item and you need more than
    one fact about it.
    """
    found = tools.product_details(ctx.deps.conn, product_id)
    if found is None:
        raise ModelRetry(_unknown_id(ctx, product_id))
    return found


@agent.tool
def get_price(ctx: RunContext[ShopDeps], product_id: str) -> PriceInfo:
    """The current price of one product, read from the catalogue.

    Call this before stating any price. Never quote a price from memory or from
    earlier in the conversation.
    """
    found = tools.price_of(ctx.deps.conn, product_id)
    if found is None:
        raise ModelRetry(_unknown_id(ctx, product_id))
    return found


@agent.tool
def get_description(ctx: RunContext[ShopDeps], product_id: str) -> ProductDescription:
    """The catalogue's own description, garment type and colours for one product.

    Call this before describing what an item looks like or what colours it
    comes in.
    """
    found = tools.description_of(ctx.deps.conn, product_id)
    if found is None:
        raise ModelRetry(_unknown_id(ctx, product_id))
    return found


@agent.tool
def check_stock(ctx: RunContext[ShopDeps], product_id: str) -> StockReport:
    """How many of each size are left, with the sold-out sizes listed separately.

    Call this before saying anything about availability. Report
    `out_of_stock_sizes` as sold out — do not quietly omit them.
    """
    found = tools.stock_report(ctx.deps.conn, product_id)
    if found is None:
        raise ModelRetry(_unknown_id(ctx, product_id))
    return found


@agent.tool
def get_customer(ctx: RunContext[ShopDeps]) -> Customer | None:
    """Who you are talking to: first name, last name, email, member-since date.

    Returns None when the shopper is not signed in. There is nothing else about
    them you can see — no orders, no payment details, no password.
    """
    return ctx.deps.customer


@agent.tool
def list_categories(ctx: RunContext[ShopDeps]) -> list[str]:
    """The categories the shop stocks. Use when a shopper asks what is available."""
    return tools.category_list(ctx.deps.conn)


# ---------------------------------------------------------------- running a turn


def _to_messages(history: list[ChatTurn]) -> list[ModelMessage]:
    """Replay prior turns as pydantic-ai message history."""
    messages: list[ModelMessage] = []
    for turn in history[-HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


async def run_agent(
    conn: sqlite3.Connection,
    message: str,
    history: list[ChatTurn] | None = None,
    customer: Customer | None = None,
    page: PageContext | None = None,
) -> ChatResponse:
    """Run one chat turn, resolve product_ids into cards, and audit the loop."""
    user_id = customer.user_id if customer else None

    try:
        result = await agent.run(
            message,
            deps=ShopDeps(conn=conn, customer=customer, page=page),
            message_history=_to_messages(history or []),
            # Loop guard: stop the agentic loop after REQUEST_LIMIT model calls.
            usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
        )
    except UsageLimitExceeded:
        audit.record(user_id=user_id, message=message, tool_calls=[],
                     stop_reason="usage_limit")
        raise
    except Exception as exc:  # noqa: BLE001 - record why the loop died, then re-raise
        text = str(exc).lower()
        reason = (
            "content_filter"
            if "content_filter" in text or "content management policy" in text
            else f"error:{type(exc).__name__}"
        )
        audit.record(user_id=user_id, message=message, tool_calls=[], stop_reason=reason)
        raise

    reply: ChatReply = result.output
    calls = _tool_calls(result)

    audit.record(
        user_id=user_id,
        message=message,
        tool_calls=calls,
        stop_reason="completed",
        reply=reply.reply,
    )

    return ChatResponse(
        reply=reply.reply,
        # Resolved from the database, never from the model, so prices and images
        # on the cards are always real.
        products=tools.cards_for(conn, reply.product_ids[:MAX_CARDS]),
        tools_used=[c["tool"] for c in calls],
    )


def _tool_calls(result: object) -> list[dict]:
    """Pair each tool call this turn with its result, for the audit trail.

    `get_customer` results are redacted — the trail should prove the tool ran
    without copying a shopper's email and join date into a file.
    """
    calls: list[dict] = []
    by_id: dict[str, dict] = {}
    for message in getattr(result, "all_messages", list)():
        for part in getattr(message, "parts", []):
            kind = type(part).__name__
            call_id = getattr(part, "tool_call_id", None)
            if kind == "ToolCallPart":
                call = {
                    "tool": getattr(part, "tool_name", "?"),
                    "args": audit.short(getattr(part, "args", "")),
                    "result": None,
                }
                calls.append(call)
                if call_id:
                    by_id[call_id] = call
            elif kind == "ToolReturnPart":
                call = by_id.get(call_id)
                if call is not None:
                    call["result"] = (
                        "<redacted: customer PII>"
                        if call["tool"] == "get_customer"
                        else audit.short(getattr(part, "content", ""))
                    )
    return calls
