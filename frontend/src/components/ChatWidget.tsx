import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useMatch } from 'react-router-dom'
import { api, money } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useMatches } from '../lib/matches'
import type { ChatTurn, PageContext, ProductCard } from '../lib/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ProductCard[]
  failed?: boolean
}

const GREETING: Message = {
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shopping assistant. Ask me about hoodies, crewnecks, colors, prices or what's left in your size.",
}

/**
 * The assistant replies in Markdown but only ever uses **bold**, so render that
 * one case rather than pulling in a Markdown library. Text is never injected as
 * HTML.
 */
function renderText(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={index}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={index}>{part}</span>
    ),
  )
}

export function ChatWidget() {
  const { setMatches } = useMatches()
  const { user } = useAuth()
  const location = useLocation()
  // Matches the item route, so the agent learns which product is on screen.
  const productRoute = useMatch('/products/:productId')

  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [restoring, setRestoring] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)

  const page: PageContext = {
    route: location.pathname,
    product_id: productRoute?.params.productId ?? null,
  }

  // Reload the saved conversation on sign-in; reset to the greeting on sign-out
  // so one shopper's history never shows to the next.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      return
    }

    let cancelled = false
    setRestoring(true)
    api
      .chatHistory(user.id)
      .then((data) => {
        if (cancelled) return
        if (data.messages.length === 0) {
          setMessages([GREETING])
          return
        }
        setMessages([
          GREETING,
          ...data.messages.map((m) => ({
            role: m.role,
            content: m.content,
            products: m.products,
          })),
        ])
      })
      .catch(() => {
        // A failed restore should not stop them chatting now.
        if (!cancelled) setMessages([GREETING])
      })
      .finally(() => {
        if (!cancelled) setRestoring(false)
      })

    return () => {
      cancelled = true
    }
  }, [user])

  // Keep the newest turn in view as the conversation grows.
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking, open])

  async function clearHistory() {
    if (!user) return
    try {
      await api.clearChatHistory(user.id)
    } catch {
      // Clearing is best-effort; the local reset below is what they asked for.
    }
    setMessages([GREETING])
  }

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const question = draft.trim()
    if (!question || thinking) return

    // Only real exchanges go back as history — not the canned greeting or errors.
    const history: ChatTurn[] = messages
      .filter((m) => m !== GREETING && !m.failed)
      .map((m) => ({ role: m.role, content: m.content }))

    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setDraft('')
    setThinking(true)

    try {
      const reply = await api.chat(question, history, user?.id ?? null, page)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: reply.reply, products: reply.products },
      ])
      // Hand the matches to the page so they render as full cards there too.
      if (reply.products.length > 0) setMatches(reply.products, question)
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          failed: true,
          content: error instanceof Error ? error.message : 'Something went wrong.',
        },
      ])
    } finally {
      setThinking(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setOpen(true)}
        aria-label="Open the shopping assistant"
      >
        💬
      </button>
    )
  }

  return (
    <section className="chat-panel" aria-label="Shopping assistant">
      <header className="chat-head">
        <div>
          <strong>Campus Customs Assistant</strong>
          <small>
            {user ? `Saved for ${user.first_name}` : 'Log in to save this chat'}
          </small>
        </div>
        {user && (
          <button
            type="button"
            className="chat-clear"
            onClick={clearHistory}
            title="Delete your saved conversation"
          >
            Clear
          </button>
        )}
        <button type="button" className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
          ×
        </button>
      </header>

      <div className="chat-log" ref={logRef}>
        {restoring && <p className="chat-note">Loading your saved conversation…</p>}
        {messages.map((message, index) => (
          <div key={index} style={{ display: 'contents' }}>
            <div className={`bubble ${message.failed ? 'error' : message.role}`}>
              {renderText(message.content)}
            </div>

            {message.products && message.products.length > 0 && (
              <div className="chat-cards">
                {message.products.map((product) => (
                  <Link
                    key={product.product_id}
                    to={product.url}
                    className="chat-card"
                    onClick={() => setOpen(false)}
                  >
                    <img src={product.image_url} alt={product.name} />
                    <div>
                      <b>{product.name}</b>
                      <span>{money(product.price)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}

        {thinking && (
          <div className="bubble assistant">
            <span className="dots">
              <i />
              <i />
              <i />
            </span>
          </div>
        )}
      </div>

      <form className="chat-form" onSubmit={send}>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="What hoodies do you have?"
          aria-label="Message the assistant"
          autoFocus
        />
        <button type="submit" disabled={thinking || !draft.trim()} aria-label="Send">
          ➤
        </button>
      </form>
    </section>
  )
}
