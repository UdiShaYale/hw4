"""Typed shapes shared by the agent, its tools and the API.

The agent is constrained to `ChatReply`, so a turn either parses into these
models or pydantic-ai retries — the frontend never has to guess.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProductCard(BaseModel):
    """One product as the site renders it: image, name, price, short description.

    Built from the database in `tools.cards_for()`, never from model output, so
    a card can only ever show real values.
    """

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    #: Catalogue copy. The frontend clamps it to three lines on the card.
    description: str = ""
    # Where the card links to. Matches the React route in App.tsx.
    url: str = ""

    def model_post_init(self, _context: object) -> None:
        if not self.url:
            self.url = f"/products/{self.product_id}"


class SizeAvailability(BaseModel):
    """What a tool reports back about one size of one product."""

    size: str
    quantity: int
    in_stock: bool


class PriceInfo(BaseModel):
    """Answer to "how much is it?" — read straight from `catalogue.price`."""

    product_id: str
    name: str
    price: float
    # Preformatted so the model never has to decide between $68 and $68.00.
    price_display: str


class ProductDescription(BaseModel):
    """Answer to "what is it like?" — the catalogue's own copy, not a paraphrase."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]


class StockReport(BaseModel):
    """Answer to "do you have my size?".

    The in/out split is computed in Python rather than left to the model, so a
    sold-out size cannot be reported as available by arithmetic slip.
    """

    product_id: str
    name: str
    sizes: list[SizeAvailability]
    in_stock_sizes: list[str] = Field(description="Sizes with quantity > 0.")
    out_of_stock_sizes: list[str] = Field(description="Sizes with quantity == 0. Say these are sold out.")
    total_stock: int
    any_in_stock: bool


class ProductSummary(BaseModel):
    """The view of a product the *model* sees — richer than a card, still trim.

    Deliberately excludes `search_tags`: they help Python rank matches but only
    add noise to the prompt.
    """

    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: list[str]
    price: float
    sizes: list[SizeAvailability] = Field(default_factory=list)


class ChatReply(BaseModel):
    """The agent's structured answer for one turn."""

    reply: str = Field(description="Markdown shown to the shopper. Two or three sentences.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_ids to render as cards on the website, most relevant first, "
            "up to six. Fill this whenever you are talking about specific items — "
            "especially when the shopper asks about a type of garment. Must come "
            "from a catalogue tool in this turn. Empty only when no specific "
            "product is involved."
        ),
    )


class Customer(BaseModel):
    """Who is chatting. Only ever built from a row in `users`."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    #: ISO timestamp from `users.created_at` — lets the agent say "welcome back".
    member_since: str = ""


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message.

    Set by the frontend from the current route, so "do you have this in large?"
    on a product page resolves to that product.
    """

    route: str = Field(default="/", description="Current path, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(
        default=None, description="The product being viewed, when the route is an item page."
    )


class ChatTurn(BaseModel):
    """One prior message, replayed so the agent remembers the conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)
    #: Present only when the shopper is signed in. Drives persistence and
    #: tells the agent who it is talking to.
    user_id: int | None = None
    page: PageContext | None = None


class ChatResponse(BaseModel):
    """What `POST /api/chat` returns to the widget."""

    reply: str
    #: Rendered by the site as product cards. Order is the agent's ranking.
    products: list[ProductCard] = Field(default_factory=list)
    # Which catalogue tools ran this turn — handy when debugging a bad answer.
    tools_used: list[str] = Field(default_factory=list)
    #: True when this turn was written to `chat_messages`.
    saved: bool = False


class StoredMessage(BaseModel):
    """One persisted turn, as returned by GET /api/chat/history."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[StoredMessage] = Field(default_factory=list)
