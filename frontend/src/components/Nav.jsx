import { Link } from 'react-router-dom'
import './Nav.css'

const LINKS = [
  { label: 'Adaptive Learning', to: '/adaptive-learning' },
  { label: 'For Students', to: '/for-students' },
]

function Nav() {
  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-logo">
          continuum
        </Link>

        <nav className="nav-links" aria-label="Primary">
          {LINKS.map(({ label, to }) => (
            <Link key={label} to={to}>
              {label}
            </Link>
          ))}
          <Link to="/login">Login</Link>
        </nav>
      </div>
    </header>
  )
}

export default Nav
