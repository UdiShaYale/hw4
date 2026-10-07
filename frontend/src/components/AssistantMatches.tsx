import { Link } from 'react-router-dom'
import { money } from '../lib/api'
import { useMatches } from '../lib/matches'
import { ProductImage } from './ProductImage'

/**
 * Product cards for whatever the assistant just matched, rendered on the page
 * itself. Appears under the nav on any route as soon as a turn returns
 * products, and each card links to that item's page.
 */
export function AssistantMatches() {
  const { products, query, clear } = useMatches()

  if (products.length === 0) return null

  return (
    <section className="matches" aria-label="Products matched by the assistant">
      <div className="matches-inner">
        <header className="matches-head">
          <div>
            <h2>
              {products.length} {products.length === 1 ? 'match' : 'matches'} from the assistant
            </h2>
            {query && <p className="muted">You asked: “{query}”</p>}
          </div>
          <button type="button" className="chip" onClick={clear}>
            Clear
          </button>
        </header>

        <div className="matches-grid">
          {products.map((product) => (
            <Link key={product.product_id} to={product.url} className="card">
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
          ))}
        </div>
      </div>
    </section>
  )
}
