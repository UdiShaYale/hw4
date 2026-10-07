import { Route, Routes } from 'react-router-dom'
import { AssistantMatches } from './components/AssistantMatches'
import { ChatWidget } from './components/ChatWidget'
import { NavBar } from './components/NavBar'
import { About } from './pages/About'
import { CreateAccount } from './pages/CreateAccount'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { ProductDetail } from './pages/ProductDetail'
import { Products } from './pages/Products'

export default function App() {
  return (
    <>
      <NavBar />
      {/* Agent matches render here, on the page, not just in the chat bubble. */}
      <AssistantMatches />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route
            path="*"
            element={
              <div className="page">
                <h1>Page not found</h1>
                <p className="muted">That link does not go anywhere.</p>
              </div>
            }
          />
        </Routes>
      </main>
      {/* Fixed to the bottom-right on every page. */}
      <ChatWidget />
    </>
  )
}
