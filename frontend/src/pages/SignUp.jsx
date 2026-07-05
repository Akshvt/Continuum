import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GoogleIcon } from '../components/AuthIcons'
import { useAuth } from '../context/AuthContext.jsx'
import { authSignup } from '../lib/api.js'
import './Login.css'

function SignUp() {
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
      const authData = await authSignup(email)
      login(authData)
      navigate('/app')
    } catch (err) {
      setError(err.message ?? 'Sign up failed. Please try again.')
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
            <h1>Create your account</h1>
            <p className="login-subtitle">
              Start remembering every session, for every student.
            </p>

            <div className="login-oauth">
              <button type="button" className="btn-oauth" disabled>
                <GoogleIcon />
                Sign up with Google
              </button>
            </div>

            <div className="login-divider">
              <span>Or</span>
            </div>

            <form className="login-email-form" onSubmit={handleSubmit}>
              <input
                type="email"
                name="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
              {error && <p className="login-error">{error}</p>}
              <button type="submit" className="btn-email" disabled={loading}>
                {loading ? 'Creating account…' : 'Sign up with email'}
              </button>
            </form>

            <p className="login-signup">
              Already have an account? <Link to="/login">Sign In</Link>
            </p>
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

export default SignUp
