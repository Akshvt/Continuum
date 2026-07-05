import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { authLogin } from '../lib/api.js'
import './Entry.css'

function Entry() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const authData = await authLogin(email)
      login(authData)
      navigate('/app')
    } catch (err) {
      setError(err.message ?? 'Sign in failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-panel">
        <div className="login-panel-inner">
          <Link to="/" className="login-logo">
            continuum
          </Link>

          <div className="login-form-wrap">
            <h1>Welcome to Continuum</h1>
            <p className="login-subtitle">
              Enter your name or student ID to start learning.
            </p>

            <form className="login-email-form" onSubmit={handleSubmit} style={{ marginTop: '32px' }}>
              <input
                type="text"
                name="email"
                placeholder="Enter your name"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
              {error && <p className="login-error">{error}</p>}
              <button type="submit" className="btn-email" disabled={loading}>
                {loading ? 'Entering…' : 'Start learning'}
              </button>
            </form>
          </div>

          <div className="login-footer-links">
            <a href="#help">Help</a>
            <a href="#terms">Terms</a>
            <a href="#privacy">Privacy</a>
          </div>
        </div>
      </div>

      <div className="login-media">
        <img src="/images/garadan.png" alt="" className="login-media-img" />
      </div>
    </div>
  )
}

export default Entry
