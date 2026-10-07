import { useEffect, useMemo, useState } from 'react'
import { ProductCard } from '../components/ProductCard'
import { api } from '../lib/api'
import type { Product } from '../lib/types'

type SortKey = 'relevance' | 'price-asc' | 'price-desc' | 'name'

const SORTS: { key: SortKey; label: string }[] = [
  { key: 'relevance', label: 'Featured' },
  { key: 'price-asc', label: 'Price: low to high' },
  { key: 'price-desc', label: 'Price: high to low' },
  { key: 'name', label: 'Name: A–Z' },
]

export function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<string[]>(['All'])
  const [category, setCategory] = useState('All')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState<SortKey>('relevance')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getCategories().then((data) => setCategories(data.categories)).catch(() => {})
  }, [])

  // Debounced so typing in the search box doesn't fire a request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true)
      api
        .listProducts(query, category)
        .then((data) => {
          setProducts(data.products)
          setError('')
        })
        .catch((err: Error) => setError(err.message))
        .finally(() => setLoading(false))
    }, 200)
    return () => clearTimeout(timer)
  }, [query, category])

  // Sort on the client: all matches are already in hand, so reordering is
  // instant and needs no extra request. 'relevance' keeps the server's order.
  const sorted = useMemo(() => {
    if (sort === 'relevance') return products
    const copy = [...products]
    copy.sort((a, b) => {
      if (sort === 'price-asc') return a.price - b.price
      if (sort === 'price-desc') return b.price - a.price
      return a.name.localeCompare(b.name)
    })
    return copy
  }, [products, sort])

  return (
    <div className="page">
      <h1>Products</h1>
      <p className="muted">
        {loading ? 'Loading the catalogue…' : `${products.length} items in the catalogue`}
      </p>

      <div className="toolbar">
        <input
          className="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by name, color, team or tag — try “navy hoodie”"
          aria-label="Search products"
        />
        {categories.map((name) => (
          <button
            key={name}
            type="button"
            className={name === category ? 'chip active' : 'chip'}
            onClick={() => setCategory(name)}
          >
            {name}
          </button>
        ))}

        <label className="sort-label" htmlFor="sort">
          Sort
        </label>
        <select
          id="sort"
          className="sort-select"
          value={sort}
          onChange={(event) => setSort(event.target.value as SortKey)}
          aria-label="Sort products"
        >
          {SORTS.map((option) => (
            <option key={option.key} value={option.key}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="alert error">{error}</div>}

      {!loading && products.length === 0 && !error && (
        <p className="muted">Nothing matched that. Try a broader search or clear the filter.</p>
      )}

      <div className="grid">
        {sorted.map((product) => (
          <ProductCard key={product.product_id} product={product} />
        ))}
      </div>
    </div>
  )
}
