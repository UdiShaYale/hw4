import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { ProductCard } from './types'

/**
 * The last set of products the agent matched.
 *
 * The chat widget writes here; the results band on the page reads it. Keeping
 * it in context rather than inside the widget is what lets the matches render
 * on the website itself instead of only inside the 390px chat bubble.
 */
interface MatchesValue {
  products: ProductCard[]
  /** What the shopper asked, shown as the band's subtitle. */
  query: string
  setMatches: (products: ProductCard[], query: string) => void
  clear: () => void
}

const MatchesContext = createContext<MatchesValue | null>(null)

export function MatchesProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<ProductCard[]>([])
  const [query, setQuery] = useState('')

  const setMatches = useCallback((next: ProductCard[], asked: string) => {
    setProducts(next)
    setQuery(asked)
  }, [])

  const clear = useCallback(() => {
    setProducts([])
    setQuery('')
  }, [])

  const value = useMemo<MatchesValue>(
    () => ({ products, query, setMatches, clear }),
    [products, query, setMatches, clear],
  )

  return <MatchesContext.Provider value={value}>{children}</MatchesContext.Provider>
}

export function useMatches(): MatchesValue {
  const context = useContext(MatchesContext)
  if (!context) throw new Error('useMatches must be used inside <MatchesProvider>')
  return context
}
