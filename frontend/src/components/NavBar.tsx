import { NavLink } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { YaleMark } from './YaleLogo'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
]

export function NavBar() {
  const { user, signOut } = useAuth()

  return (
    <nav className="nav">
      <div className="nav-inner">
        <NavLink to="/" className="nav-brand">
          <YaleMark />
          Campus Customs
        </NavLink>

        <div className="nav-links">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {link.label}
            </NavLink>
          ))}

          {user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button type="button" className="nav-signout" onClick={signOut}>
                Sign out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                Log In
              </NavLink>
              <NavLink
                to="/create-account"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link cta')}
              >
                Create Account
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
