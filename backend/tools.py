"""Catalogue tools the agent can call.

Each one reads `data/data/campus_customs.db` through `db.py` and returns a typed
model. The agent has no other way to learn what the shop sells, which is what
keeps it from inventing products.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

import db
from models import (
    Customer,
    PageContext,
    PriceInfo,
    ProductCard,
    ProductDescription,
    ProductSummary,
    SizeAvailability,
    StockReport,
)

#: Cap on rows handed back to the model in one call. Enough to compare, small
#: enough that the prompt stays cheap.
MAX_RESULTS = 12

#: Words that carry no signal when ranking a catalogue search.
_STOPWORDS = {
    "a", "an", "and", "any", "are", "can", "do", "does", "for", "got", "has",
    "have", "how", "i", "in", "is", "it", "like", "looking", "me", "my", "of",
    "on", "or", "show", "some", "something", "that", "the", "there", "this",
    "to", "want", "what", "which", "with", "you", "your", "need", "get",
}


@dataclass
class ShopDeps:
    """Per-request dependencies: the database, who is asking, and where they are.

    `customer` is None for a signed-out shopper, and `page` is None when the
    frontend did not say which route the message came from.
    """

    conn: sqlite3.Connection
    customer: Customer | None = None
    page: PageContext | None = None


def _summarize(conn: sqlite3.Connection, product: dict, with_sizes: bool = True) -> ProductSummary:
    sizes: list[SizeAvailability] = []
    if with_sizes:
        sizes = [
            SizeAvailability(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0)
            for s in db.sizes_for(conn, product["product_id"])
        ]
    return ProductSummary(
        product_id=product["product_id"],
        name=product["name"],
        garment_type=product["garment_type"],
        category=product["category"],
        description=product["description"],
        colors=product["colors"],
        price=product["price"],
        sizes=sizes,
    )


def search_catalogue(
    conn: sqlite3.Connection,
    query: str = "",
    category: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> list[ProductSummary]:
    """Rank the catalogue against the shopper's words, then apply hard filters."""
    products = db.list_products(conn, category=category)

    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]

    if size:
        wanted = size.strip().upper()
        products = [
            p for p in products
            if any(s["size"] == wanted and s["quantity"] > 0
                   for s in db.sizes_for(conn, p["product_id"]))
        ]

    words = [
        w for w in re.findall(r"[a-z0-9-]+", query.lower())
        if w not in _STOPWORDS and len(w) > 2
    ]
    if not words:
        return [_summarize(conn, p) for p in products[:MAX_RESULTS]]

    scored: list[tuple[int, dict]] = []
    for product in products:
        name = product["name"].lower()
        tags = " ".join(product["search_tags"]).lower()
        colors = " ".join(product["colors"]).lower()
        body = f"{product['description']} {product['garment_type']} {product['category']}".lower()

        # search_tags were hand-written to match how shoppers phrase things, so
        # they are weighted alongside the name rather than with the prose.
        score = sum(
            3 * (w in name) + 3 * (w in tags) + 2 * (w in colors) + (w in body)
            for w in words
        )
        if score:
            scored.append((score, product))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [_summarize(conn, p) for _, p in scored[:MAX_RESULTS]]


def product_details(conn: sqlite3.Connection, product_id: str) -> ProductSummary | None:
    product = db.get_product(conn, product_id)
    return _summarize(conn, product) if product else None


def price_of(conn: sqlite3.Connection, product_id: str) -> PriceInfo | None:
    product = db.get_product(conn, product_id)
    if product is None:
        return None
    price = product["price"]
    return PriceInfo(
        product_id=product["product_id"],
        name=product["name"],
        price=price,
        # Whole dollars when the price is whole, matching the house style.
        price_display=f"${price:.0f}" if price % 1 == 0 else f"${price:.2f}",
    )


def description_of(conn: sqlite3.Connection, product_id: str) -> ProductDescription | None:
    product = db.get_product(conn, product_id)
    if product is None:
        return None
    return ProductDescription(
        product_id=product["product_id"],
        name=product["name"],
        garment_type=product["garment_type"],
        description=product["description"],
        colors=product["colors"],
    )


def stock_report(conn: sqlite3.Connection, product_id: str) -> StockReport | None:
    """Per-size stock, with the in/out split precomputed."""
    product = db.get_product(conn, product_id)
    if product is None:
        return None

    sizes = [
        SizeAvailability(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0)
        for s in db.sizes_for(conn, product_id)
    ]
    return StockReport(
        product_id=product["product_id"],
        name=product["name"],
        sizes=sizes,
        in_stock_sizes=[s.size for s in sizes if s.in_stock],
        out_of_stock_sizes=[s.size for s in sizes if not s.in_stock],
        total_stock=sum(s.quantity for s in sizes),
        any_in_stock=any(s.in_stock for s in sizes),
    )


def category_list(conn: sqlite3.Connection) -> list[str]:
    return db.categories(conn)


def cards_for(conn: sqlite3.Connection, product_ids: list[str]) -> list[ProductCard]:
    """Turn the agent's chosen ids into cards.

    Unknown ids are dropped rather than faked, so a hallucinated id shows up as
    a missing card instead of a broken link.
    """
    cards: list[ProductCard] = []
    for product_id in product_ids:
        product = db.get_product(conn, product_id)
        if product is None:
            continue
        cards.append(
            ProductCard(
                product_id=product["product_id"],
                name=product["name"],
                garment_type=product["garment_type"],
                price=product["price"],
                image_url=product["image_url"],
                description=product["description"],
            )
        )
    return cards
