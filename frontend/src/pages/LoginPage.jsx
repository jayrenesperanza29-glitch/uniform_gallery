import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import PasswordField from '../components/PasswordField.jsx'

export default function LoginPage() {
  const [email, setEmail]     = useState('')
  const [pw, setPw]           = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const { login }   = useAuth()
  const navigate    = useNavigate()
  const location    = useLocation()
  const justRegistered = location.state?.registered

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, pw)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-art">
        <div className="auth-art-inner">
          <span className="auth-art-badge">Student Portal</span>
          <h1>School Uniform Gallery & Price List</h1>
          <p>Your official reference for approved school attire, complete with sizing guides and current prices.</p>
        </div>
      </div>

      <div className="auth-form-side fade-up">
        <h2>Welcome back</h2>
        <p className="subtitle">Sign in to access the uniform gallery</p>

        {justRegistered && (
          <div className="success-msg">Account created! You can now sign in.</div>
        )}
        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="student@school.edu"
              required
              autoFocus
            />
          </div>

          <PasswordField
            label="Password"
            value={pw}
            onChange={e => setPw(e.target.value)}
            placeholder="••••••••"
            required
          />

          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="auth-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
        <p className="auth-link" style={{ marginTop: 8, fontSize: '0.8rem', color: '#888' }}>
          Admin: admin@school.edu / Admin@1234
        </p>
      </div>
    </div>
  )
}
