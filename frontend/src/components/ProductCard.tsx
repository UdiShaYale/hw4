import { Link } from 'react-router-dom'
import { money } from '../lib/api'
import type { Product } from '../lib/types'
import { ProductImage } from './ProductImage'

/** The whole card is the link, so clicking anywhere opens the item page. */
export function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-img">
        <ProductImage src={product.image_url} alt={product.name} />
      </div>
      <div className="card-body">
        <span className="card-type">{product.garment_type}</span>
        <span className="card-name">{product.name}</span>
        <p className="card-desc">{product.description}</p>
        <span className="card-price">{money(product.price)}</span>
      </div>
    </Link>
  )
}
