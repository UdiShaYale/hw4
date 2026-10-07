/** Mirrors the shapes returned by backend/db.py. */

export interface Product {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
}

export interface SizeStock {
  size: string
  quantity: number
}

/** `GET /api/products/:id` adds live inventory on top of the catalogue row. */
export interface ProductDetail extends Product {
  sizes: SizeStock[]
  total_stock: number
  in_stock: boolean
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

/** The product shape the site renders as a card. Mirrors models.ProductCard. */
export interface ProductCard {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  /** Catalogue copy, clamped on the card. */
  description: string
  /** Route to the item page, built by the backend. */
  url: string
}

/** Where the shopper is, so the agent can resolve "this". */
export interface PageContext {
  route: string
  product_id: string | null
}

/** One turn restored from the database. */
export interface StoredMessage {
  role: 'user' | 'assistant'
  content: string
  products: ProductCard[]
  created_at: string
}

export interface ChatReply {
  reply: string
  products: ProductCard[]
  /** Which catalogue tools the agent called this turn - useful when debugging. */
  tools_used: string[]
  /** True when the turn was written to chat_messages (signed-in shoppers only). */
  saved: boolean
}
