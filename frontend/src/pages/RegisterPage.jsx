import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import PasswordField from '../components/PasswordField.jsx'

export default function RegisterPage() {
  const [form, setForm]       = useState({ student_name: '', email: '', password: '', confirm: '' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate     = useNavigate()

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      await register(form.student_name, form.email, form.password)
      navigate('/login', { state: { registered: true } })
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
          <span className="auth-art-badge">New Student</span>
          <h1>Join the Uniform Gallery</h1>
          <p>Create your student account to browse official school uniforms and current pricing information.</p>
        </div>
      </div>

      <div className="auth-form-side fade-up">
        <h2>Create account</h2>
        <p className="subtitle">Register to access the gallery</p>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Full name</label>
            <input value={form.student_name} onChange={set('student_name')} placeholder="Juan dela Cruz" required autoFocus />
          </div>
          <div className="field">
            <label>Email address</label>
            <input type="email" value={form.email} onChange={set('email')} placeholder="student@school.edu" required />
          </div>

          <PasswordField
            label="Password"
            value={form.password}
            onChange={set('password')}
            placeholder="Min. 6 characters"
            required
          />
          <PasswordField
            label="Confirm password"
            value={form.confirm}
            onChange={set('confirm')}
            placeholder="••••••••"
            required
          />

          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
