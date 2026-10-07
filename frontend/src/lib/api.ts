import type {
  ChatReply,
  ChatTurn,
  PageContext,
  Product,
  ProductDetail,
  StoredMessage,
  User,
} from './types'

/** Vite proxies /api and /images to the FastAPI app on port 8000. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })

  if (!response.ok) {
    // FastAPI puts the human-readable message in `detail`.
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  listProducts(q = '', category = 'All') {
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (category && category !== 'All') params.set('category', category)
    const query = params.toString()
    return request<{ count: number; products: Product[] }>(
      `/api/products${query ? `?${query}` : ''}`,
    )
  },

  getProduct(id: string) {
    return request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)
  },

  getCategories() {
    return request<{ categories: string[] }>('/api/categories')
  },

  login(email: string, password: string) {
    return request<User>('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },

  signup(input: {
    first_name: string
    last_name: string
    email: string
    password: string
    confirm_password: string
  }) {
    return request<User>('/api/signup', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },

  chat(message: string, history: ChatTurn[], userId: number | null, page: PageContext) {
    return request<ChatReply>('/api/chat', {
      method: 'POST',
      // user_id is sent only when signed in; it drives both persistence and
      // whether the agent knows who it is talking to.
      body: JSON.stringify({ message, history, user_id: userId, page }),
    })
  },

  chatHistory(userId: number) {
    return request<{ messages: StoredMessage[] }>(
      `/api/chat/history?user_id=${encodeURIComponent(userId)}`,
    )
  },

  clearChatHistory(userId: number) {
    return request<{ deleted: number }>(
      `/api/chat/history?user_id=${encodeURIComponent(userId)}`,
      { method: 'DELETE' },
    )
  },
}

export const money = (value: number) =>
  `$${value % 1 === 0 ? value.toFixed(0) : value.toFixed(2)}`
