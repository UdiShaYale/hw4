import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ProductImage } from '../components/ProductImage'
import { api, money } from '../lib/api'
import type { ProductDetail as Detail } from '../lib/types'

export function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Detail | null>(null)
  const [selectedSize, setSelectedSize] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    setProduct(null)
    setSelectedSize('')
    setError('')
    api
      .getProduct(productId)
      .then((data) => {
        setProduct(data)
        // Preselect the first size that is actually available.
        setSelectedSize(data.sizes.find((s) => s.quantity > 0)?.size ?? '')
      })
      .catch((err: Error) => setError(err.message))
  }, [productId])

  if (error) {
    return (
      <div className="page">
        <Link to="/products" className="back-link">
          ← Back to products
        </Link>
        <div className="alert error">{error}</div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="page">
        <p className="muted">Loading…</p>
      </div>
    )
  }

  const chosen = product.sizes.find((s) => s.size === selectedSize)

  return (
    <div className="page">
      <Link to="/products" className="back-link">
        ← Back to products
      </Link>

      <div className="detail">
        <div className="detail-img">
          <ProductImage src={product.image_url} alt={product.name} />
        </div>

        <div>
          <span className="detail-type">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{money(product.price)}</p>

          <span className={product.in_stock ? 'stock-pill in' : 'stock-pill out'}>
            {product.in_stock ? `In stock — ${product.total_stock} available` : 'Sold out'}
          </span>

          <h2>Description</h2>
          <p>{product.description}</p>

          <h2>Sizes</h2>
          <div className="sizes">
            {product.sizes.map((size) => {
              const soldOut = size.quantity === 0
              return (
                <button
                  key={size.size}
                  type="button"
                  disabled={soldOut}
                  onClick={() => setSelectedSize(size.size)}
                  className={[
                    'size',
                    soldOut ? 'out' : '',
                    size.size === selectedSize ? 'selected' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                >
                  {size.size}
                  <small>{soldOut ? 'sold out' : `${size.quantity} left`}</small>
                </button>
              )
            })}
          </div>

          <h2>Colours</h2>
          <div className="tags">
            {product.colors.map((color) => (
              <span key={color} className="tag">
                {color}
              </span>
            ))}
          </div>

          <h2>Tags</h2>
          <div className="tags">
            {product.search_tags.map((tag) => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>

          <p style={{ marginTop: '2rem' }}>
            <button type="button" className="btn btn-wide" disabled={!chosen || chosen.quantity === 0}>
              {chosen ? `Add ${chosen.size} to bag` : 'Select a size'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
