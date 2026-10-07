import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ProductCard } from '../components/ProductCard'
import { YaleLogo } from '../components/YaleLogo'
import { api } from '../lib/api'
import type { Product } from '../lib/types'

export function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    api
      .listProducts()
      .then((data) => setFeatured(data.products.slice(0, 4)))
      .catch(() => setFeatured([]))
  }, [])

  return (
    <div className="page">
      <section className="hero">
        <div>
          <h1>Yale, worn well.</h1>
          <p>
            Campus Customs is the student-run apparel shop on Broadway — hoodies,
            crewnecks, quarter-zips and tees built for New Haven winters and
            Harvard-Yale Saturdays.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">
              Shop the catalogue
            </Link>
            <Link to="/about" className="btn btn-ghost">
              Our story
            </Link>
          </div>
        </div>
        <div className="hero-logo">
          <YaleLogo size={190} />
        </div>
      </section>

      <div className="tiles">
        <div className="tile">
          <h3>Printed in New Haven</h3>
          <p>Every garment is pressed two blocks from Old Campus, usually within 48 hours.</p>
        </div>
        <div className="tile">
          <h3>Sized for everyone</h3>
          <p>XS through XXL on every style, with live stock counts on each product page.</p>
        </div>
        <div className="tile">
          <h3>Ask the assistant</h3>
          <p>Use the chat in the corner — it reads the real catalogue, not a script.</p>
        </div>
      </div>

      <div className="section-head">
        <h2>Fresh off the press</h2>
        <Link to="/products">See all products →</Link>
      </div>
      <div className="grid">
        {featured.map((product) => (
          <ProductCard key={product.product_id} product={product} />
        ))}
      </div>
    </div>
  )
}
